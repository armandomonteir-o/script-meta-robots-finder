import argparse
from abc import ABC, abstractmethod


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

    @abstractmethod
    def execute(self, args: argparse.Namespace):
        """
        The main entry point for the command's logic.

        This method is called when the command is invoked.
        """
        pass
