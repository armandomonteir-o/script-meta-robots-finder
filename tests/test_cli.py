import sys
import logging
from unittest.mock import patch, MagicMock
import pytest
from cli import CliApp


@pytest.fixture
def app():
    """Provides a clean instance of CliApp for each test."""
    return CliApp()


def test_cli_run_direct_scan_metas(app, monkeypatch):
    """
    Verifies that scan-metas command executes correctly in direct (CLI) mode with proper arguments.
    Tests argument parsing and command execution with mocked command handler.
    """

    test_args = [
        "main.py",
        "scan-metas",
        "some/file.xlsx",
        "URL",
        "--checks",
        "robots",
        "viewport",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    mock_scan_execute = MagicMock()

    monkeypatch.setattr(app.commands["scan-metas"], "execute", mock_scan_execute)
    app.parser._actions[1].choices["scan-metas"].set_defaults(func=mock_scan_execute)

    app.run()

    mock_scan_execute.assert_called_once()

    called_args = mock_scan_execute.call_args[0][0]
    assert called_args.file_path == "some/file.xlsx"
    assert called_args.checks == ["robots", "viewport"]
    assert called_args.command == "scan-metas"


def test_cli_run_direct_compare_metas(app, monkeypatch):
    """
    Verifies that compare-metas command executes correctly in direct (CLI) mode.
    Tests argument parsing with optional parameters and command execution with mocked handler.
    """

    test_args = [
        "main.py",
        "compare-metas",
        "another/file.xlsx",
        "--url-col",
        "MyURL",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    mock_compare_execute = MagicMock()

    monkeypatch.setattr(app.commands["compare-metas"], "execute", mock_compare_execute)
    app.parser._actions[1].choices["compare-metas"].set_defaults(
        func=mock_compare_execute
    )

    app.run()

    mock_compare_execute.assert_called_once()
    called_args = mock_compare_execute.call_args[0][0]

    assert called_args.file_path == "another/file.xlsx"
    assert called_args.url_col == "MyURL"
    assert called_args.name_col == "Meta Name"


def test_cli_run_interactive_mode_scan_metas(app, monkeypatch):
    """
    Verifies the scan-metas command's interactive mode workflow.
    Tests the complete interactive flow including command selection, argument collection,
    and proper execution with mocked user inputs and command handler.
    """

    monkeypatch.setattr(sys, "argv", ["main.py"])

    monkeypatch.setattr(
        "questionary.select",
        lambda message, choices, use_indicator: MagicMock(
            ask=lambda: "scan-metas: Audits for the existence of specific meta tags."
        ),
    )

    mock_responses = {
        "Path to the .xlsx file with URLs.": "interactive/file.xlsx",
        "Name of the column containing the URLs.": "MyURLs",
        "A list of meta tags to check (e.g., robots description viewport).": "robots og:title",
    }

    def mock_questionary_text(message, **kwargs):
        logging.info(f"Mock text prompt: {message}")
        answer = mock_responses.get(message)
        if answer is None:
            logging.warning(f"No mock response for message: {message}")
            return MagicMock(ask=lambda: "robots og:title")
        return MagicMock(ask=lambda: answer)

    def mock_questionary_confirm(message, **kwargs):

        return MagicMock(ask=lambda: True)

    monkeypatch.setattr("questionary.text", mock_questionary_text)
    monkeypatch.setattr("questionary.confirm", mock_questionary_confirm)

    mock_scan_execute = MagicMock()

    monkeypatch.setattr(app.commands["scan-metas"], "execute", mock_scan_execute)
    app.parser._actions[1].choices["scan-metas"].set_defaults(func=mock_scan_execute)

    mock_open = MagicMock(side_effect=FileNotFoundError("Mocked File Not Found"))
    monkeypatch.setattr("builtins.open", mock_open)

    app.run()

    mock_scan_execute.assert_called_once()
    called_args = mock_scan_execute.call_args[0][0]

    assert called_args.file_path == "interactive/file.xlsx"
    assert called_args.column_name == "MyURLs"
    assert called_args.checks == ["robots", "og:title"]
    assert called_args.command == "scan-metas"


def test_cli_run_interactive_mode_cancel_command(app, monkeypatch):
    """
    Verifies that the application gracefully handles command cancellation in interactive mode.
    Tests that no command is executed when the user cancels during command selection.
    """

    monkeypatch.setattr(sys, "argv", ["main.py"])

    monkeypatch.setattr(
        "questionary.select",
        lambda message, choices, use_indicator: MagicMock(ask=lambda: None),
    )

    mock_open = MagicMock(side_effect=FileNotFoundError("Mocked File Not Found"))
    monkeypatch.setattr("builtins.open", mock_open)

    mock_scan_execute = MagicMock()
    monkeypatch.setattr(app.commands["scan-metas"], "execute", mock_scan_execute)

    app.run()

    mock_scan_execute.assert_not_called()


def test_cli_run_interactive_mode_cancel_args(app, monkeypatch):
    """
    Verifies that the application gracefully handles argument input cancellation in interactive mode.
    Tests that no command is executed when the user cancels during argument collection.
    """

    monkeypatch.setattr(sys, "argv", ["main.py"])

    monkeypatch.setattr(
        "questionary.select",
        lambda message, choices, use_indicator: MagicMock(
            ask=lambda: "scan-metas: Audits for the existence of specific meta tags."
        ),
    )

    monkeypatch.setattr("questionary.text", lambda message: MagicMock(ask=lambda: None))

    mock_open = MagicMock(side_effect=FileNotFoundError("Mocked File Not Found"))
    monkeypatch.setattr("builtins.open", mock_open)

    mock_scan_execute = MagicMock()
    monkeypatch.setattr(app.commands["scan-metas"], "execute", mock_scan_execute)

    app.run()

    mock_scan_execute.assert_not_called()
