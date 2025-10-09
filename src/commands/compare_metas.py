import argparse
import logging
import requests as rq
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd

from src.core.crawler import Crawler
from reporting.excel_reader import ExcelReader
from reporting.excel_writer import ExcelWriter
from .base_command import Command

logger = logging.getLogger(__name__)


class CompareMetasCommand(Command):

    @staticmethod
    def setup_args(parser: argparse.ArgumentParser):
        parser.description = "Audits meta tag contents against an Excel spreadsheet."

        parser.add_argument(
            "file_path",
            help="Path to the .xlsx file with URL, Meta Name, and Expected Content columns.",
        )

        parser.add_argument(
            "--url-col",
            default="URL",
            help="Name of the column containing the URLs.",
        )

        parser.add_argument(
            "--name-col",
            default="Meta Name",
            help="Name of the column containing the meta tag names (default: 'Meta Name').",
        )

        parser.add_argument(
            "--content-col",
            default="Expected Content",
            help="Name of the column with the expected content (default: 'Expected Content').",
        )

    def _process_row(
        self, row: pd.Series, args: argparse.Namespace, session: rq.Session
    ):
        """Processes a single row from the DataFrame to audit a meta tag.

        Designed to be run in a separate thread.

        Args:
            row (pd.Series): A single row from the input DataFrame.
            args (argparse.Namespace): The command-line arguments.
            session (rq.Session): The requests.Session object for making HTTP requests.

        Returns:
            dict: A dictionary containing the complete audit result for the row.
        """

        url = row[args.url_col]
        meta_name = row[args.name_col]
        expected_content = row[args.content_col]

        try:
            crawler = Crawler(str(url), session, [])
            found_content = crawler.get_meta_content_by_name(str(meta_name))
            is_match = str(found_content).strip() == str(expected_content).strip()

            return {
                args.url_col: url,
                args.name_col: meta_name,
                args.content_col: expected_content,
                "Found Content": found_content or "Not Found",
                "Match?": is_match,
            }
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return {
                args.url_col: url,
                args.name_col: meta_name,
                args.content_col: expected_content,
                "Found Content": f"Error: {e}",
                "Match?": False,
            }

    def _clean_dataframe(self, df: pd.DataFrame, url_column: str) -> pd.DataFrame:
        """Removes rows from the DataFrame that do not have a valid URL.

        Args:
            df (pd.DataFrame): The input DataFrame to be cleaned.
            url_column (str): The name of the column that should contain the URLs.

        Returns:
            pd.DataFrame: A cleaned copy of the input DataFrame.
        """

        cleaned_df = df.dropna(subset=[url_column]).copy()

        cleaned_df = cleaned_df[cleaned_df[url_column].str.strip() != ""]

        return cleaned_df

    def execute(self, args: argparse.Namespace):
        """Executes the meta tag content comparison concurrently.

        Reads a spreadsheet with URLs, meta tag names, and expected content.
        It then crawls each URL, compares the found content with the expected
        content, and generates a detailed audit report in Excel.

        Args:
            args (argparse.Namespace): The command-line arguments, including
                file_path and the names of the relevant columns.
        """
        print(">>> Comando 'compare-metas' ativado! <<<")
        print(f"Recebi os argumentos: {args}")

        filepath = self._normalize_filepath(args.file_path)

        excel_reader = ExcelReader(filepath)
        sheet_data = excel_reader.read_spreadsheet()

        sheet_data = self._clean_dataframe(sheet_data, args.url_col)

        tasks_to_process = [row for index, row in sheet_data.iterrows()]

        task_function = lambda task, session: self._process_row(task, args, session)

        desc_provider = lambda task: task[args.url_col]

        report_data = self._run_concurrent_tasks(
            tasks=tasks_to_process,
            task_function=task_function,
            desc_provider=desc_provider,
            pbar_color="green",
        )

        if not report_data:
            print("Nenhum dado foi processado. Nenhum relatório será gerado.")
            return

        df = pd.DataFrame(report_data)
        ExcelWriter.create_spreadsheet_with_results(df, "compare_results.xlsx")
