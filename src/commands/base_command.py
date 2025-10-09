import argparse
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List
import requests as rq
from tqdm import tqdm
import pandas as pd


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

    @abstractmethod
    def execute(self, args: argparse.Namespace):
        """
        The main entry point for the command's logic.

        This method is called when the command is invoked.
        """
        pass
