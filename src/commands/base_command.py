import argparse
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Optional, Dict
import requests as rq
from tqdm import tqdm
import pandas as pd
from reporting.excel_reader import ExcelReader
import questionary


class Command(ABC):
    """
    A base class that all command classes must inherit from.

    It defines the contract for what a command must provide to integrate
    with the CLI application.
    """

    @staticmethod
    @abstractmethod
    def setup_args(subparser: argparse.ArgumentParser):
        """
        Adds the specific arguments for this command to the subparser.

        This is where 'add_argument()' calls should be made.
        """
        pass

    def _normalize_filepath(self, filepath: str) -> str:
        """
        Ensures the given filepath ends with .xlsx.

        Args:
            filepath (str): The initial file path.

        Returns:
            str: The normalized file path.
        """
        if not filepath.endswith(".xlsx"):
            return f"{filepath}.xlsx"
        return filepath

    def _run_concurrent_tasks(
        self,
        tasks: Iterable,
        task_function: Callable,
        desc_provider: Callable,
        pbar_color: str = "green",
    ) -> List[dict]:
        """
        A generic engine to run tasks concurrently with a progress bar.

        Args:
            tasks (Iterable): A list or iterable of items to process (e.g., URLs or DataFrame rows).
            task_function (Callable): A lambda or function that takes one item from the tasks list
                                     and returns a dictionary.
            pbar_color (str): The color for the tqdm progress bar.

        Returns:
            List[dict]: A list containing the dictionary results from each task.
        """

        results = []

        tasks_list = list(tasks)
        if not tasks_list:
            return []

        with rq.Session() as session:
            with ThreadPoolExecutor(max_workers=10) as executor:

                future_to_task = {
                    executor.submit(task_function, task, session): task
                    for task in tasks_list
                }

                with tqdm(
                    total=len(tasks_list),
                    bar_format="{l_bar}{bar:40}| {n_fmt}/{total_fmt} [{elapsed}]",
                    colour=pbar_color,
                ) as pbar:
                    for future in as_completed(future_to_task):
                        original_task = future_to_task[future]

                        description = desc_provider(original_task)
                        pbar.set_description(f"Processing {description[:50]}")

                        result = future.result()
                        results.append(result)
                        pbar.update(1)
        return results

    def _get_valid_sheet_data(self, filepath: str) -> pd.DataFrame | None:
        """
        Interactively validates the file path and reads the spreadsheet.
        It will keep asking the user for a correct path until one is provided or the operation is cancelled.

        Args:
            filepath (str): The initial file path provided by the user.

        Returns:
            pd.DataFrame | None: The loaded DataFrame if successful, or None if the user cancels.
        """

        while True:
            try:
                print(f"Reading from file: {filepath}")
                excel_reader = ExcelReader(filepath)
                sheet_data = excel_reader.read_spreadsheet()
                return sheet_data
            except FileNotFoundError:
                new_filepath = questionary.text(
                    f"Arquivo '{filepath}' não encontrado. Por favor, digite o nome correto do caminho do arquivo:"
                ).ask()

                if new_filepath is None:
                    print("Operação cancelada.")
                    return

                filepath = self._normalize_filepath(new_filepath)

    def _get_validated_urls_from_column(
        self, column: str, sheet_data: pd.DataFrame
    ) -> list[str] | None:
        """
        Interactively validates the column name and extracts the URL list.
        It will keep asking the user for a correct column name until one is provided or the operation is cancelled.

        Args:
            sheet_data (pd.DataFrame): The DataFrame to read from.
            column (str): The initial column name provided by the user.

        Returns:
            list[str] | None: The list of URLs if successful, or None if the user cancels.
        """
        while True:
            try:
                urls_to_check = ExcelReader.read_column(sheet_data, column)
                return urls_to_check
            except KeyError:
                new_column = questionary.text(
                    f"Coluna '{column}' não encontrada na planilha. Por favor, digite o nome correto da coluna:"
                ).ask()

                if new_column is None:
                    print("Operação cancelada.")
                    return None
                column = new_column

    def _ensure_multiple_columns_exist(
        self, required_columns: List[Dict], sheet_data: pd.DataFrame
    ) -> Optional[List[str]]:
        """
        Interactively validates that a list of required columns exists in the DataFrame,
        performing a case-insensitive search. If a column is not found,
        it prompts the user for the correct name.

        Args:
            required_columns (List[str]): A list of column names to validate.
            sheet_data (pd.DataFrame): The DataFrame to check against.

        Returns:
            Optional[List[str]]: A list with the corrected, valid column names
                                    (preserving original casing from the file),
                                    or None if the user cancels the operation.
        """
        validated_columns = []
        actual_sheet_columns = sheet_data.columns.tolist()

        for col_to_find in required_columns:
            current_col_name = col_to_find["name"]

            while True:
                matching_column = None

                for actual_col in actual_sheet_columns:
                    if actual_col.lower() == current_col_name.lower():
                        matching_column = actual_col
                        break

                if matching_column:
                    validated_columns.append(matching_column)
                    break
                else:
                    description = col_to_find["description"]
                    new_col_name = questionary.text(
                        f"Coluna '{current_col_name}', {description} não encontrada. Por favor, digite o nome correto da coluna:"
                    ).ask()

                    if new_col_name is None:
                        print("Operação cancelada.")
                        return None

                    current_col_name = new_col_name

        return validated_columns

    @abstractmethod
    def execute(self, args: argparse.Namespace):
        """
        The main entry point for the command's logic.

        This method is called when the command is invoked.
        """
        pass
