import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from unittest.mock import MagicMock, patch
from commands.base_command import Command
from reporting.excel_reader import ExcelReader


class ConcreteCommand(Command):
    """A concrete implementation of the abstract Command class for testing purposes."""

    def setup_args(self, parser):
        pass

    def execute(self, args):
        pass


@pytest.fixture
def command():
    """Provides a clean instance of ConcreteCommand for each test."""
    return ConcreteCommand()


def test_normalize_filepath(command):
    """Tests that filepaths are correctly suffixed with .xlsx if missing."""
    assert command._normalize_filepath("file.xlsx") == "file.xlsx"
    assert command._normalize_filepath("file") == "file.xlsx"
    assert command._normalize_filepath("archive.xls") == "archive.xls.xlsx"


def test_clean_dataframe(command):
    """Tests that rows with empty or None values in the URL column are dropped."""
    data = {
        "URL": ["http://a.com", " ", "http://c.com", None, "http://d.com"],
        "OutraColuna": [1, 2, 3, 4, 5],
    }
    df = pd.DataFrame(data)

    expected_data = {
        "URL": ["http://a.com", "http://c.com", "http://d.com"],
        "OutraColuna": [1, 3, 5],
    }
    expected_df = pd.DataFrame(expected_data).reset_index(drop=True)

    cleaned_df = command._clean_dataframe(df, "URL").reset_index(drop=True)

    assert_frame_equal(cleaned_df, expected_df)


def test_get_valid_sheet_data_success(command):
    """Tests the happy path for _get_valid_sheet_data, where the file exists."""
    fake_df = pd.DataFrame({"col1": [1, 2]})

    with patch("commands.base_command.ExcelReader") as mock_excel_reader:

        mock_excel_reader.return_value.read_spreadsheet.return_value = fake_df

        result_df = command._get_valid_sheet_data("dummy_path.xlsx")

        assert_frame_equal(result_df, fake_df)

        mock_excel_reader.return_value.read_spreadsheet.assert_called_once()


def test_get_valid_sheet_data_retry_and_success(command, monkeypatch):
    """Tests the retry logic for _get_valid_sheet_data when file is not found initially."""
    fake_df = pd.DataFrame({"col1": [1, 2]})

    # questionary.text().ask() simulation
    monkeypatch.setattr(
        "questionary.text", lambda _: MagicMock(ask=lambda: "correct_path.xlsx")
    )

    with patch("commands.base_command.ExcelReader") as mock_excel_reader:

        mock_excel_reader.return_value.read_spreadsheet.side_effect = [
            FileNotFoundError,
            fake_df,
        ]

        result_df = command._get_valid_sheet_data("wrong.xlsx")

        assert_frame_equal(result_df, fake_df)
        assert mock_excel_reader.return_value.read_spreadsheet.call_count == 2


def test_get_valid_sheet_data_cancel(command, monkeypatch):
    """Tests the _get_valid_sheet_data logic when the user cancels the prompt."""

    # questionary.text().ask() simulation
    monkeypatch.setattr("questionary.text", lambda _: MagicMock(ask=lambda: None))

    with patch("commands.base_command.ExcelReader") as mock_excel_reader:

        mock_excel_reader.return_value.read_spreadsheet.side_effect = FileNotFoundError

        result_df = command._get_valid_sheet_data("wrong.xlsx")

        assert result_df is None


def test_get_validated_urls_from_column_success(command):
    """Tests the happy path for _get_validated_urls_from_column."""
    df = pd.DataFrame({"URL List": ["http://a.com", "http://b.com"]})

    with patch.object(
        ExcelReader, "read_column", return_value=["http://a.com", "http://b.com"]
    ) as mock_read:
        urls = command._get_validated_urls_from_column("URL List", df)

        assert urls == ["http://a.com", "http://b.com"]
        mock_read.assert_called_once_with(df, "URL List")


def test_get_validated_urls_from_column_retry(command, monkeypatch):
    """Tests the retry logic for _get_validated_urls_from_column when column is not found."""
    df = pd.DataFrame({"CorrectColumn": ["http://a.com"]})

    monkeypatch.setattr(
        "questionary.text", lambda _: MagicMock(ask=lambda: "CorrectColumn")
    )

    with patch.object(ExcelReader, "read_column") as mock_read:

        mock_read.side_effect = [KeyError, ["http://a.com"]]

        urls = command._get_validated_urls_from_column("WrongColumn", df)

        assert urls == ["http://a.com"]
        assert mock_read.call_count == 2


def test_get_validated_urls_from_column_cancel(command, monkeypatch):
    """Tests the _get_validated_urls_from_column logic when the user cancels the prompt."""
    df = pd.DataFrame({"CorrectColumn": ["http://a.com"]})

    monkeypatch.setattr("questionary.text", lambda _: MagicMock(ask=lambda: None))

    with patch.object(ExcelReader, "read_column") as mock_read:
        mock_read.side_effect = KeyError

        urls = command._get_validated_urls_from_column("WrongColumn", df)

        assert urls is None
        mock_read.assert_called_once_with(df, "WrongColumn")


def test_ensure_multiple_columns_exist_success(command):
    """Tests _ensure_multiple_columns_exist happy path and case-insensitivity."""
    df = pd.DataFrame({"URL": [1], "meta name": [2], "Expected Content": [3]})

    required_cols = [
        {"name": "url", "description": "URL column"},
        {"name": "Meta Name", "description": "Tag name column"},
    ]

    validated = command._ensure_multiple_columns_exist(required_cols, df)

    assert validated == ["URL", "meta name"]


def test_ensure_multiple_columns_exist_retry(command, monkeypatch):
    """Tests the retry logic for _ensure_multiple_columns_exist."""
    df = pd.DataFrame({"url_col": [1_2_3], "content_col": ["abc"]})

    required_cols = [
        {"name": "URL", "description": "URL column"},
        {"name": "Content", "description": "Content column"},
    ]

    mock_ask = MagicMock()
    mock_ask.side_effect = ["url_col", "content_col"]
    monkeypatch.setattr("questionary.text", lambda _: MagicMock(ask=mock_ask))

    validated = command._ensure_multiple_columns_exist(required_cols, df)

    assert validated == ["url_col", "content_col"]
    assert mock_ask.call_count == 2


def test_ensure_multiple_columns_exist_cancel(command, monkeypatch):
    """Tests the cancellation logic for _ensure_multiple_columns_exist."""
    df = pd.DataFrame({"url_col": [123], "content_col": ["abc"]})

    required_cols = [
        {"name": "URL", "description": "URL column"},
        {"name": "Content", "description": "Content column"},
    ]

    monkeypatch.setattr("questionary.text", lambda _: MagicMock(ask=lambda: None))

    validated = command._ensure_multiple_columns_exist(required_cols, df)

    assert validated is None


def test_run_concurrent_tasks_success(command):
    """Tests that the concurrent task runner processes all tasks and returns results."""

    tasks = ["a", "b", "c"]

    def simple_task_function(task_item, session):
        assert session is not None
        return {"result": task_item.upper()}

    desc_provider = lambda task: task

    with patch("commands.base_command.tqdm", MagicMock()):
        results = command._run_concurrent_tasks(
            tasks=tasks, task_function=simple_task_function, desc_provider=desc_provider
        )

    result_set = {tuple(sorted(d.items())) for d in results}
    expected_set = {
        tuple(sorted({"result": "A"}.items())),
        tuple(sorted({"result": "B"}.items())),
        tuple(sorted({"result": "C"}.items())),
    }

    assert len(results) == len(expected_set)
    assert result_set == expected_set


def test_run_concurrent_tasks_empty(command):
    """Tests that the concurrent runner handles an empty task list correctly."""

    results = command._run_concurrent_tasks(
        tasks=[], task_function=lambda x, y: x, desc_provider=lambda x: x
    )

    assert results == []
