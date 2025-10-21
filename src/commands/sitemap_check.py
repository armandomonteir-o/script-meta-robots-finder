from commands.base_command import Command
import argparse
import pandas as pd
import logging
import requests as rq
from core.crawler import Crawler
from reporting.excel_writer import ExcelWriter
from typing import Optional

logger = logging.getLogger(__name__)


class SitemapCheck(Command):

    @staticmethod
    def setup_args(parser: argparse.ArgumentParser):
        parser.description = "Scan a sitemap and audits against a excel spreadsheet"

        parser.add_argument(
            "file_path",
            help="Path to the .xlsx file with Sitemap URL and Expected URLS columns.",
        )

        parser.add_argument(
            "--sitemap-col",
            default="Sitemap",
            help="Name of the column containing the Sitemap URL",
        )

        parser.add_argument(
            "--urls-col",
            default="Expected URLS",
            help="Name of the column with the expected URLS (default: 'Expected URLS').",
        )

    def _process_row(
        self, row: pd.Series, urls_col: str, sitemap_urls_set: set
    ) -> dict:
        """
        Processes a single row from the DataFrame to check if its URL is
        present in the set of URLs from the sitemap.

        This function is designed to be run concurrently and performs no
        network operations.

        Args:
            row (pd.Series): A single row from the input DataFrame.
            urls_col (str): The name of the column containing the URL to check.
            sitemap_urls_set (set): A set of all URLs found in the sitemap for
                                    fast, case-sensitive lookups.

        Returns:
            dict: A dictionary containing the URL and the result of the check.
        """
        url_to_check = str(row[urls_col]).strip()
        is_in_sitemap = url_to_check in sitemap_urls_set

        return {
            urls_col: url_to_check,
            "Found in Sitemap?": is_in_sitemap,
        }

    def _fetch_and_prepare_sitemap_set(
        self, sheet_data: pd.DataFrame, sitemap_col: str
    ) -> Optional[set]:
        """
        Orchestrates the fetching, parsing, and preparation of the sitemap URLs.

        This helper function handles the entire "heavy lifting" part of the
        command: it extracts the sitemap URL from the DataFrame, instantiates
        the Crawler to fetch and parse the XML content, and converts the
        resulting list of URLs into a set for high-performance lookups.

        Args:
            sheet_data (pd.DataFrame): The DataFrame loaded from the user's
                                    Excel file.
            sitemap_col (str): The validated name of the column that contains
                            the sitemap URL.

        Returns:
            Optional[set]: A set of URL strings found in the sitemap if the
                        operation is successful. Returns None if the sitemap
                        cannot be fetched or parsed.
        """
        sitemap_url = str(sheet_data[sitemap_col].iloc[0])
        print(f"URL do Sitemap a ser analisada: {sitemap_url}")

        with rq.Session() as session:
            crawler = Crawler(sitemap_url, session, [])
            print("Buscando e analisando o sitemap... Isso pode levar um momento.")
            sitemap_urls = crawler.fetch_sitemap_urls()

        if sitemap_urls is None:
            print("Não foi possível ler o sitemap...")
            return None

        sitemap_urls_set = set(sitemap_urls)
        print(
            f"Sitemap analisado com sucesso. {len(sitemap_urls_set)} URLs encontradas."
        )

        return sitemap_urls_set

    def execute(self, args: argparse.Namespace):

        print(">>> Comando 'sitemap-check' ativado! <<<")

        filepath = self._normalize_filepath(args.file_path)

        sheet_data = self._get_valid_sheet_data(filepath)
        if sheet_data is None:
            return

        required_columns = [
            {"name": args.sitemap_col, "description": "Que contém a URL do Sitemap"},
            {"name": args.urls_col, "description": "Que contém as URLs esperadas"},
        ]

        validated_columns = self._ensure_multiple_columns_exist(
            required_columns, sheet_data
        )
        if validated_columns is None:
            return

        sitemap_col, urls_col = validated_columns

        sheet_data = self._clean_dataframe(sheet_data, urls_col)

        sitemap_urls_set = self._fetch_and_prepare_sitemap_set(sheet_data, sitemap_col)

        if sitemap_urls_set is None:
            return

        tasks_to_process = [row for _, row in sheet_data.iterrows()]

        task_function = lambda task, session: self._process_row(
            task, urls_col, sitemap_urls_set
        )

        desc_provider = lambda task: str(task[urls_col])

        report_data = self._run_concurrent_tasks(
            tasks=tasks_to_process,
            task_function=task_function,
            desc_provider=desc_provider,
            pbar_color="blue",
        )

        if not report_data:
            print("Nenhum dado foi processado. Nenhum relatório será gerado.")
            return

        report_df = pd.DataFrame(report_data)
        ExcelWriter.create_spreadsheet_with_results(
            report_df, "results/sitemap_check_results.xlsx"
        )
