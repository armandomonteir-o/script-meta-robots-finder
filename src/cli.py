from ast import arg
import sys
import argparse
import logging
from pathlib import Path
import questionary
from commands import scan_metas, compare_metas

log_directory = Path("./logs")
log_directory.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_directory / "app.log")],
)


def _setup_scan_metas_command(subparsers: argparse._SubParsersAction):
    parser_scan = subparsers.add_parser(
        "scan-metas", description="Scans a list of URLs for specific meta tags."
    )
    parser_scan.add_argument("file_path", help="Path to the .xlsx file with URLs.")
    parser_scan.add_argument(
        "column_name", help="Name of the column containing the URLs."
    )
    parser_scan.add_argument(
        "--checks",
        nargs="+",
        default=["robots"],
        help="A list of meta tags to check (e.g., robots description viewport).",
    )
    parser_scan.set_defaults(func=scan_metas.run)


def _setup_compare_metas_command(subparsers: argparse._SubParsersAction):

    parser_compare = subparsers.add_parser(
        "compare-metas",
        description="Audits meta tag contents against an Excel spreadsheet.",
    )

    parser_compare.add_argument(
        "file_path",
        help="Path to the .xlsx file with URL, Meta Name, and Expected Content columns.",
    )

    parser_compare.add_argument(
        "--url-col",
        default="URL",
        help="Name of the column containing the URLs.",
    )

    parser_compare.add_argument(
        "--name-col",
        default="Meta Name",
        help="Name of the column containing the meta tag names (default: 'Meta Name').",
    )

    parser_compare.add_argument(
        "--content-col",
        default="Expected Content",
        help="Name of the column with the expected content (default: 'Expected Content').",
    )

    parser_compare.set_defaults(func=compare_metas.run)


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SEO Helper - a CLI Tool to improve technical SEO stuff"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    _setup_scan_metas_command(subparsers)
    _setup_compare_metas_command(subparsers)

    return parser


def _choose_command(parser: argparse.ArgumentParser) -> argparse.ArgumentParser | None:

    subparsers_action = next(
        (
            action
            for action in parser._actions
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


def _collect_arguments(command_parser: argparse.ArgumentParser) -> dict | None:
    """Collects required and optional arguments from the user interactively."""

    interactive_args = {}

    actions = [action for action in command_parser._actions if action.dest != "help"]
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
    command_parser: argparse.ArgumentParser, args_dict: dict, command_name: str
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


def run_interactive_mode():
    try:
        with open("src/splash.txt", "r", encoding="utf-8") as f:
            splash_screen = f.read()
        print(splash_screen)
    except FileNotFoundError:
        print("========== SEO Helper ==========")
    print("\nWelcome to SEO Helper!")

    parser = setup_parser()

    command_parser = _choose_command(parser)
    if not command_parser:
        return

    command_name = command_parser.prog.split()[-1]
    print(f"\nYou chose: {command_name}. Great choice!")
    print("\nNow, let's get the arguments for this command...")

    args_dict = _collect_arguments(command_parser)
    if not args_dict:
        return

    _execute_command(command_parser, args_dict, command_name)


def run_direct_mode():
    parser = setup_parser()
    args = parser.parse_args()
    args.func(args)


def main():
    if len(sys.argv) <= 1:
        run_interactive_mode()
    else:
        run_direct_mode()
