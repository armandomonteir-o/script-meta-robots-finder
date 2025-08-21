import pandas as pd
import logging

logger = logging.getLogger(__name__)


def read_urls_from_sheet(url_name: str) -> pd.DataFrame:

    try:
        df = pd.read_excel(url_name)
        return df
    except FileNotFoundError:
        logger.error(f"The file {url_name} was not found")
        raise


def read_column(df: pd.DataFrame, column: str) -> list[str]:

    column_data = df[column].dropna()

    convert_to_list = column_data.tolist()

    return convert_to_list
