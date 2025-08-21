from requests import RequestException
from url_reader import read_urls_from_sheet, read_column
from searcher import html_search, find_metarobots
from output import create_spreadsheet_with_results
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log")],
)


def main():
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

    data = read_urls_from_sheet(url)

    logger = logging.getLogger(__name__)

    reading_column = read_column(data, column)

    def verificar_link(link: str):
        try:
            html_res = html_search(link)
            finder = find_metarobots(html_res)

            if finder == True:
                logger.info(f"SUCESSO: Meta tag 'robots' encontrada na URL: {link}")
                return True
            else:
                logger.info(f"PARCIAL: Meta tag 'robots' NÃO encontrada na URL: {link}")
                return False
        except RequestException as e:
            logger.error((f"ERRO: A verificação da URL {link} falhou. Motivo: {e}"))
            return "Error"
        except Exception as e:
            logger.critical(f"ERRO INESPERADO ao processar a URL {link}: {e}")
            return "Error"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(verificar_link, link): link for link in reading_column
        }

        final_results = {}

        with tqdm(
            total=len(reading_column),
            bar_format="{l_bar}{bar:40}| {n_fmt}/{total_fmt} [{elapsed}]",
            colour="green",
        ) as pbar:

            for future in as_completed(futures):
                original_link = futures[future]

                pbar.set_description(f"Verificando { original_link[:50]}")

                results = future.result()

                final_results[original_link] = results

                pbar.update(1)

    ordened_resulted_list = [final_results[link] for link in reading_column]

    create_spreadsheet_with_results(reading_column, ordened_resulted_list)


if __name__ == "__main__":
    main()
