import pandas as pd
import logging

logger = logging.getLogger(__name__)


def read_urls_from_sheet(url_name: str) -> pd.DataFrame:
    """Reads URLs from an Excel sheet.

    Args:
        url_name (str): The path to the Excel file.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the Excel file.
    """

    try:
        df = pd.read_excel(url_name)
        return df
    except FileNotFoundError:
        logger.error(f"The file {url_name} was not found")
        raise


def read_column(df: pd.DataFrame, column: str) -> list[str]:
    """Reads a specific column from a DataFrame and returns it as a list.

    Args:
        df (pd.DataFrame): The DataFrame to read from.
        column (str): The name of the column to read.

    Returns:
        list[str]: A list of values from the specified column.
    """

    column_data = df[column].dropna()

    convert_to_list = column_data.tolist()

    return convert_to_list
