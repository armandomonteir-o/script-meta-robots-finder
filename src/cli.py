import sys
import argparse
import logging
from pathlib import Path
from commands.scan_metas import run as run_scan_metas

log_directory = Path("./logs")

log_directory.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_directory / "app.log")],
)


def run_interactive_mode():
    try:
        with open("src/splash.txt", "r", encoding="utf-8") as f:
            splash_screen = f.read()
        print(splash_screen)
    except FileNotFoundError:
        print("========== SEO Helper ==========")

    print("\nWelcome to SEO Helper!")


def run_direct_mode():

    parser = argparse.ArgumentParser(
        description="SEO Helper - a CLI Tool to improve technical SEO stuff"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    parser_scan = subparsers.add_parser(
        "scan_metas", help="Scans a list of URLs for specific meta tags."
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

    args = parser.parse_args()

    if args.command == "scan-metas":
        run_scan_metas(args)


def main():

    if len(sys.argv) <= 1:
        run_interactive_mode()
    else:
        run_direct_mode()


if __name__ == "__main__":
    main()
