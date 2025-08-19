import pandas as pd


def ler_urls_da_planilha(url_name):
    df = pd.read_excel(url_name)

    return df


def read_column(df, column):

    coluna = df[column]

    convert_to_list = coluna.tolist()

    return convert_to_list
