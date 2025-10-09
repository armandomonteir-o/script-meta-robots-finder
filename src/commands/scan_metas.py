import argparse
from reporting.excel_reader import ExcelReader
from reporting.excel_writer import ExcelWriter
import requests as rq
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from core.crawler import Crawler
import logging
import pandas as pd
from .base_command import Command

logger = logging.getLogger(__name__)


class ScanMetasCommand(Command):

    @staticmethod
    def setup_args(parser: argparse.ArgumentParser):
        parser.description = "Scans a list of URLs for specific meta tags."

        parser.add_argument("file_path", help="Path to the .xlsx file with URLs.")
        parser.add_argument(
            "column_name", help="Name of the column containing the URLs."
        )
        parser.add_argument(
            "--checks",
            nargs="+",
            default=["robots"],
            help="A list of meta tags to check (e.g., robots description viewport).",
        )

    def _process_url(self, url: str, checks: list[str], session: rq.Session) -> dict:
        """Processes a single URL to scan for specified meta tags.

        Designed to be run in a separate thread.

        Args:
            url (str): The URL to be processed.
            checks (list[str]): A list of meta tag names to scan for.
            session (rq.Session): The requests.Session object for making HTTP requests.

        Returns:
            dict: A dictionary containing the URL and the scan results.
        """
        try:
            crawler = Crawler(url, session, checks)
            results = crawler.execute_scan()

            return {"URL": url, **results}

        except Exception as e:
            logger.error(f"'{url}' generated an exception: {e}")

            error_results = {check: "Error" for check in checks}
            return {"URL": url, **error_results}

    def execute(self, args: argparse.Namespace):
        """Executes the meta tag scan concurrently based on user arguments.

        Reads a list of URLs from a spreadsheet, processes them in parallel to
        check for the existence of specified meta tags, and generates an Excel
        report with the results.

        Args:
            args (argparse.Namespace): The command-line arguments, including
                file_path, column_name, and checks.
        """
        print(">>> Comando 'scan-metas' ativado! <<<")
        print(f"Recebi o arquivo: {args.file_path}")
        print(f"Recebi a coluna: {args.column_name}")

        filepath = self._normalize_filepath(args.file_path)

        column = args.column_name

        print(f"Reading from file: {filepath}")
        excel_reader = ExcelReader(filepath)
        sheet_data = excel_reader.read_spreadsheet()
        urls_to_check = excel_reader.read_column(sheet_data, column)

        task_function = lambda url, session: self._process_url(
            url, args.checks, session
        )

        report_data = self._run_concurrent_tasks(
            tasks=urls_to_check, task_function=task_function, pbar_color="green"
        )

        if not report_data:
            print("Nenhum dado foi processado. Nenhum relatório será gerado.")
            return

        logger.info("Scan concluído. Gerando relatório.")
        report_df = pd.DataFrame(report_data)
        ExcelWriter.create_spreadsheet_with_results(report_df)
