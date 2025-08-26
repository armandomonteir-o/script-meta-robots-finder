from pathlib import Path
from spreadsheet_manager import SpreadSheetManager
from crawler import Crawler
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import argparse

log_directory = Path("./logs")

log_directory.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_directory / "app.log")],
)


def main():
    """Main function to run the meta robots finder script."""

    parser = argparse.ArgumentParser(
        description="A script to find meta robots tags in URLs from a spreadsheet."
    )

    parser.add_argument("file_path")

    parser.add_argument("column_name")

    args = parser.parse_args()

    url = args.file_path
    if not url.endswith(".xlsx"):
        url = url + ".xlsx"

    column = args.column_name

    print(f"Reading from file: {url}")
    spreadsheet_manager = SpreadSheetManager(url)
    sheet_data = spreadsheet_manager.read_spreadsheet()
    urls_to_check = SpreadSheetManager.read_column(sheet_data, column)

    final_results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(Crawler(link).link_checker): link for link in urls_to_check
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
                    logging.error((f"'{original_link}' generated an exception: {e}"))
                    final_results[original_link] = "Error"

                pbar.update(1)

    ordered_results = [final_results[link] for link in urls_to_check]
    SpreadSheetManager.create_spreadsheet_with_results(urls_to_check, ordered_results)


if __name__ == "__main__":
    main()
