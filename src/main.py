from requests import RequestException
from url_reader import ler_urls_da_planilha, read_column
from searcher import html_search, find_metarobots
from output import create_planilha_with_results
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log")],
)


logger = logging.getLogger(__name__)


def insert_url_name() -> str:

    url_name = input("Digite o nome da planilha aqui: ")

    return url_name


def insert_column_name() -> str:

    column_name = input("Digite o nome da coluna que contenha as URLS: ")

    return column_name


url = insert_url_name()

data = ler_urls_da_planilha(url)

column = insert_column_name()

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
    futures = {executor.submit(verificar_link, link): link for link in reading_column}

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


create_planilha_with_results(reading_column, ordened_resulted_list)
