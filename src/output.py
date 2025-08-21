import pandas as pd


def create_planilha_with_results(urls: list[str], results: list[bool | str]):

    data = {"urls:": urls, "results": results}

    sheet = pd.DataFrame(data)

    sheet.to_excel("resultados.xlsx", index=False)
