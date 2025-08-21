from url_reader import ler_urls_da_planilha, read_column
from searcher import html_search, find_metarobots
from output import create_planilha_with_results
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
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

results = []


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
    except Exception as e:
        logger.critical(f"ERRO INESPERADO ao processar a URL {link}: {e}")
        return "Error"


with ThreadPoolExecutor(max_workers=10) as executor:
    resultados = list(executor.map(verificar_link, reading_column))


create_planilha_with_results(reading_column, resultados)
