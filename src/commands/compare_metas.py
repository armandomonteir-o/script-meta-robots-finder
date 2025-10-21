import argparse
import logging
import requests as rq
from tqdm import tqdm
import pandas as pd
from core.crawler import Crawler
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
        self,
        row: pd.Series,
        url_col: str,
        name_col: str,
        content_col: str,
        session: rq.Session,
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

        url = row[url_col]
        meta_name = row[name_col]
        expected_content = row[content_col]

        try:
            crawler = Crawler(str(url), session, [])
            found_content = crawler.get_meta_content_by_name(str(meta_name))
            is_match = str(found_content).strip() == str(expected_content).strip()

            return {
                url_col: url,
                name_col: meta_name,
                content_col: expected_content,
                "Found Content": found_content or "Not Found",
                "Match?": is_match,
            }
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return {
                url_col: url,
                name_col: meta_name,
                content_col: expected_content,
                "Found Content": f"Error: {e}",
                "Match?": False,
            }

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

        sheet_data = self._get_valid_sheet_data(filepath)
        if sheet_data is None:
            raise ValueError("No valid sheet data found in the file")

        required_columns = [
            {"name": args.url_col, "description": "que contém as URLs"},
            {"name": args.name_col, "description": "que contém os nomes das meta tags"},
            {"name": args.content_col, "description": "que contém o conteúdo esperado"},
        ]

        validated_columns = self._ensure_multiple_columns_exist(
            required_columns, sheet_data
        )

        if validated_columns is None:
            return

        url_col, name_col, content_col = validated_columns

        sheet_data = self._clean_dataframe(sheet_data, url_col)

        tasks_to_process = [row for index, row in sheet_data.iterrows()]

        task_function = lambda task, session: self._process_row(
            task, url_col, name_col, content_col, session
        )

        desc_provider = lambda task: task[url_col]

        report_data = self._run_concurrent_tasks(
            tasks=tasks_to_process,
            task_function=task_function,
            desc_provider=desc_provider,
            pbar_color="red",
        )

        if not report_data:
            print("Nenhum dado foi processado. Nenhum relatório será gerado.")
            return

        df = pd.DataFrame(report_data)
        ExcelWriter.create_spreadsheet_with_results(df, "results/compare_results.xlsx")
