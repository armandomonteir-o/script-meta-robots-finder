import argparse
from ast import arg
from reporting.excel_reader import ExcelReader
from reporting.excel_writer import ExcelWriter
import requests as rq
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from core.crawler import Crawler
import logging

logger = logging.getLogger(__name__)


def run(args: argparse.Namespace):
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

    final_results = {}

    with rq.Session() as session:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(
                    Crawler(link, session, tags_to_check=args.checks).execute_scan
                ): link
                for link in urls_to_check
            }

            with tqdm(
                total=len(urls_to_check),
                bar_format="{l_bar}{bar:40}| {n_fmt}/{total_fmt} [{elapsed}]",
                colour="green",
            ) as pbar:

                for future in as_completed(future_to_url):
                    original_link = future_to_url[future]

                    pbar.set_description(f"Checking { original_link[:50]}")

                    try:
                        results = future.result()
                        final_results[original_link] = results
                    except Exception as e:
                        logger.error((f"'{original_link}' generated an exception: {e}"))
                        final_results[original_link] = "Error"

                    pbar.update(1)

        ordered_results = [final_results[link] for link in urls_to_check]
        ExcelWriter.create_spreadsheet_with_results(urls_to_check, ordered_results)
