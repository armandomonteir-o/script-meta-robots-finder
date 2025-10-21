import sys
import argparse
import logging
from pathlib import Path
import questionary
from commands.scan_metas import ScanMetasCommand
from commands.compare_metas import CompareMetasCommand
from commands.sitemap_check import SitemapCheckCommand

log_directory = Path("./logs")
log_directory.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_directory / "app.log")],
)


class CliApp:
    def __init__(self):
        """
        Initializes the application and registers all available commands.
        """
        logging.info("CliApp initialized.")
        self.commands = {
            "scan-metas": ScanMetasCommand(),
            "compare-metas": CompareMetasCommand(),
            "sitemap-check": SitemapCheckCommand(),
        }
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="SEO Helper - a CLI Tool to improve technical SEO stuff"
        )

        subparsers = parser.add_subparsers(
            dest="command", required=True, help="Available commands"
        )

        for name, command_instance in self.commands.items():

            command_parser = subparsers.add_parser(name)

            command_instance.setup_args(command_parser)

            command_parser.set_defaults(func=command_instance.execute)

        return parser

    def _choose_command(self) -> argparse.ArgumentParser | None:

        subparsers_action = next(
            (
                action
                for action in self.parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )

        if subparsers_action is None:
            print("Error: Could not find commands configuration.")
            return

        command_choices = [
            f"{name}: {sub_parser.description}"
            for name, sub_parser in subparsers_action.choices.items()
        ]

        if not command_choices:
            print("No commands available")
            return

        chosen_command_str = questionary.select(
            "Which command would you like to run?",
            choices=command_choices,
            use_indicator=True,
        ).ask()

        if chosen_command_str is None:
            print("\nExiting. See you next time!")
            return None

        chosen_command_name = chosen_command_str.split(":")[0]
        return subparsers_action.choices[chosen_command_name]

    def _collect_arguments(
        self, command_parser: argparse.ArgumentParser
    ) -> dict | None:
        """Collects required and optional arguments from the user interactively."""

        interactive_args = {}

        actions = [
            action for action in command_parser._actions if action.dest != "help"
        ]
        required_actions = [action for action in actions if action.required]
        optional_actions = [action for action in actions if not action.required]

        print("\nPlease provide the following information:\n")

        for action in required_actions:
            user_input = questionary.text(f"{action.help}").ask()
            if user_input is None:
                print("\nOperation cancelled. Exiting.")
                return None
            interactive_args[action.dest] = user_input

        if optional_actions:
            configure_optionals = questionary.confirm(
                "Would you like to configure the optional arguments?"
            ).ask()

            if configure_optionals:
                print("\nPlease configure the optional arguments:\n")
                for action in optional_actions:
                    prompt = f"{action.help} (Default: {action.default})"
                    user_input = questionary.text(prompt).ask()

                    if user_input is None:
                        print("\nOperation cancelled. Exiting.")
                        return None

                    if user_input.strip():
                        if action.nargs == "+":
                            interactive_args[action.dest] = user_input.split()
                        else:
                            interactive_args[action.dest] = user_input

        return interactive_args

    def _execute_command(
        self,
        command_parser: argparse.ArgumentParser,
        args_dict: dict,
        command_name: str,
    ):

        final_args = argparse.Namespace(**args_dict)

        for action in command_parser._actions:
            if not hasattr(final_args, action.dest):
                setattr(final_args, action.dest, action.default)

        command_function = command_parser.get_default("func")
        if command_function:
            command_function(final_args)
        else:
            print(f"Error: No function associated with command '{command_name}'.")

    def run_interactive_mode(self):
        try:
            with open("src/splash.txt", "r", encoding="utf-8") as f:
                splash_screen = f.read()
            print(splash_screen)
        except FileNotFoundError:
            print("========== SEO Helper ==========")
        print("\nWelcome to SEO Helper!")

        command_parser = self._choose_command()
        if not command_parser:
            return

        command_name = command_parser.prog.split()[-1]
        print(f"\nYou chose: {command_name}. Great choice!")
        print("\nNow, let's get the arguments for this command...")

        args_dict = self._collect_arguments(command_parser)
        if not args_dict:
            return

        logging.info(f"Command chose: { command_name},")
        logging.info(f"Collected arguments: { args_dict},")
        self._execute_command(command_parser, args_dict, command_name)

    def run_direct_mode(self):
        try:
            args = self.parser.parse_args()
            args.func(args)
        except Exception as e:
            logging.error(
                f"An unexpected error occurred in direct mode: {e}", exc_info=True
            )
            print(f"\nAn unexpected error occurred: {e}")

    def run(self):
        if len(sys.argv) <= 1:
            logging.info("Running in interactive mode.")
            self.run_interactive_mode()
        else:
            logging.info("Running in direct mode.")
            self.run_direct_mode()


def main():
    app = CliApp()
    app.run()
