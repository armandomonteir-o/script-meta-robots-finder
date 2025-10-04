import sys
import argparse
from reporting.excel_reader import ExcelReader
from reporting.excel_writer import ExcelWriter
import requests as rq
from core.crawler import Crawler
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
from pathlib import Path

log_directory = Path("./logs")

log_directory.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_directory / "app.log")],
)


def run_interactive_mode():
    try:
        with open("src/splash.txt", "r", encoding="utf-8") as f:
            splash_screen = f.read()
        print(splash_screen)
    except FileNotFoundError:
        print("========== SEO Helper ==========")

    print("\nWelcome to SEO Helper!")


def run_direct_mode():

    parser = argparse.ArgumentParser(
        description="SEO Helper - a CLI Tool to improve technical SEO stuff"
    )

    parser.add_argument("file_path")

    parser.add_argument("column_name")

    args = parser.parse_args()
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
                executor.submit(Crawler(link, session).link_checker): link
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
                        logging.error(
                            (f"'{original_link}' generated an exception: {e}")
                        )
                        final_results[original_link] = "Error"

                    pbar.update(1)

        ordered_results = [final_results[link] for link in urls_to_check]
        ExcelWriter.create_spreadsheet_with_results(urls_to_check, ordered_results)


def main():

    if len(sys.argv) <= 1:
        run_interactive_mode()
    else:
        run_direct_mode()


if __name__ == "__main__":
    main()
