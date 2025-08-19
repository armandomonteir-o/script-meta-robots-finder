from url_reader import ler_urls_da_planilha, read_column
from searcher import html_search, find_metarobots
from output import create_planilha_with_results
from concurrent.futures import ThreadPoolExecutor


def insert_url_name():

    url_name = input("Digite o nome da planilha aqui: ")

    return url_name


def insert_column_name():

    column_name = input("Digite o nome da coluna que contenha as URLS: ")

    return column_name


url = insert_url_name()

data = ler_urls_da_planilha(url)

column = insert_column_name()

reading_column = read_column(data, column)

results = []


def verificar_link(link):
    try:
        html_res = html_search(link)
        finder = find_metarobots(html_res)
        if finder == True:
            return True
        else:
            return False
    except:
        return "Error"


with ThreadPoolExecutor(max_workers=10) as executor:
    resultados = list(executor.map(verificar_link, reading_column))


create_planilha_with_results(reading_column, resultados)
