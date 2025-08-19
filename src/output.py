import pandas as pd


def create_planilha_with_results(urls, results):

    data = {"urls:": urls, "results": results}

    sheet = pd.DataFrame(data)

    sheet.to_excel("resultados.xlsx", index=False)
