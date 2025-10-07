import argparse
from reporting.excel_reader import ExcelReader
from reporting.excel_writer import ExcelWriter
import requests as rq
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from core.crawler import Crawler
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def _process_url(url: str, checks: list[str], session: rq.Session) -> dict:
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


def run(args: argparse.Namespace):
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

    url = args.file_path
    if not url.endswith(".xlsx"):
        url = url + ".xlsx"

    column = args.column_name

    print(f"Reading from file: {url}")
    excel_reader = ExcelReader(url)
    sheet_data = excel_reader.read_spreadsheet()
    urls_to_check = excel_reader.read_column(sheet_data, column)

    report_data = []

    with rq.Session() as session:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(_process_url, url, args.checks, session): url
                for url in urls_to_check
            }

            with tqdm(
                total=len(urls_to_check),
                bar_format="{l_bar}{bar:40}| {n_fmt}/{total_fmt} [{elapsed}]",
                colour="green",
            ) as pbar:

                for future in as_completed(future_to_url):
                    original_link = future_to_url[future]

                    pbar.set_description(f"Checking { original_link[:50]}")

                    results = future.result()
                    report_data.append(results)
                    pbar.update(1)

        logger.info("Scan concluído. Gerando relatório.")
        df = pd.DataFrame(report_data)
        ExcelWriter.create_spreadsheet_with_results(df)
