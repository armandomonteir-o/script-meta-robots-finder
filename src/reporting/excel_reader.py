import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ExcelReader:
    def __init__(self, file_path: str):

        self.file_path = file_path

    def read_spreadsheet(self) -> pd.DataFrame:
        """Reads all the content from an Excel sheet.

        Args:
            file_path (str): The path to the Excel file.

        Returns:
            pd.DataFrame: A DataFrame containing the data from the Excel file.
        """

        try:
            df = pd.read_excel(self.file_path)
            return df
        except FileNotFoundError:
            logger.error(f"The file {self.file_path} was not found")
            raise

    @staticmethod
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
