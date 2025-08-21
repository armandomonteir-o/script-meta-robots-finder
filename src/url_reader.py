import pandas as pd


def ler_urls_da_planilha(url_name: str) -> pd.DataFrame:
    df = pd.read_excel(url_name)

    return df


def read_column(df: pd.DataFrame, column: str) -> list[str]:

    coluna = df[column].dropna()

    convert_to_list = coluna.tolist()

    return convert_to_list
