from unittest.mock import patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal
from commands.compare_metas import CompareMetasCommand
import pytest
import requests as rq
from requests.exceptions import RequestException
from core.crawler import Crawler


@pytest.fixture
def compare_command():
    """Provides a clean instance of CompareMetasCommand for each test."""
    return CompareMetasCommand()


def test_compare_metas_execute_flow():
    """
    Integration test for the CompareMetasCommand execute method.
    """
    fake_args = MagicMock()
    fake_args.file_path = "fake_audit.xlsx"
    fake_args.url_col = "URL"
    fake_args.name_col = "Meta Name"
    fake_args.content_col = "Expected Content"

    fake_sheet_data = pd.DataFrame(
        {
            "URL": ["http://site1.com", "http://site2.com"],
            "Meta Name": ["title", "description"],
            "Expected Content": ["Título Correto", "Descrição Esperada"],
        }
    )

    fake_report_data = [
        {
            "URL": "http://site1.com",
            "Meta Name": "title",
            "Expected Content": "Título Correto",
            "Found Content": "Título Correto",
            "Match?": True,
        },
        {
            "URL": "http://site2.com",
            "Meta Name": "description",
            "Expected Content": "Descrição Esperada",
            "Found Content": "Descrição Diferente",
        },
    ]

    with patch(
        "commands.compare_metas.CompareMetasCommand._get_valid_sheet_data"
    ) as mock_get_sheet, patch(
        "commands.compare_metas.CompareMetasCommand._run_concurrent_tasks"
    ) as mock_run_tasks, patch(
        "commands.compare_metas.ExcelWriter.create_spreadsheet_with_results"
    ) as mock_excel_writer:

        mock_get_sheet.return_value = fake_sheet_data
        mock_run_tasks.return_value = fake_report_data

        command = CompareMetasCommand()
        command.execute(fake_args)

        mock_get_sheet.assert_called_once()
        mock_run_tasks.assert_called_once()
        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]
        expected_df = pd.DataFrame(fake_report_data)

        called_df = called_df.sort_values(by="URL").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="URL").reset_index(drop=True)

        assert_frame_equal(called_df, expected_df)


def test_process_row_match(compare_command):
    """
    Tests the _process_row method when the found content matches the expected content.
    """
    row_data = {
        "URL": "http://example.com",
        "Meta Name": "description",
        "Expected Content": "This is the correct description.",
    }
    row = pd.Series(row_data)

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.get_meta_content_by_name.return_value = (
        " This is the correct description.  "
    )

    with patch(
        "commands.compare_metas.Crawler", return_value=mock_crawler_instance
    ) as mock_crawler_class:
        mock_session = MagicMock(spec=rq.Session)
        result = compare_command._process_row(
            row,
            url_col="URL",
            name_col="Meta Name",
            content_col="Expected Content",
            session=mock_session,
        )

    mock_crawler_class.assert_called_once_with("http://example.com", mock_session, [])
    mock_crawler_instance.get_meta_content_by_name.assert_called_with("description")

    expected_result = {
        "URL": "http://example.com",
        "Meta Name": "description",
        "Expected Content": "This is the correct description.",
        "Found Content": " This is the correct description.  ",
        "Match?": True,
    }
    assert result == expected_result


def test_process_row_no_match(compare_command):
    """
    Tests the _process_row method when the found content does not match.
    """
    row_data = {
        "URL": "http://example.com",
        "Meta Name": "description",
        "Expected Content": "Content A",
    }
    row = pd.Series(row_data)

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.get_meta_content_by_name.return_value = "Content B"

    with patch("commands.compare_metas.Crawler", return_value=mock_crawler_instance):
        result = compare_command._process_row(
            row, "URL", "Meta Name", "Expected Content", MagicMock(spec=rq.Session)
        )

    assert result["Match?"] is False
    assert result["Found Content"] == "Content B"


def test_process_row_not_found(compare_command):
    """
    Tests the _process_row method when the meta tag is not found (Crawler returns None).
    """
    row_data = {
        "URL": "http://example.com",
        "Meta Name": "description",
        "Expected Content": "Anything",
    }
    row = pd.Series(row_data)

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.get_meta_content_by_name.return_value = None  # Tag not found

    with patch("commands.compare_metas.Crawler", return_value=mock_crawler_instance):
        result = compare_command._process_row(
            row, "URL", "Meta Name", "Expected Content", MagicMock(spec=rq.Session)
        )

    assert result["Match?"] is False
    assert result["Found Content"] == "Not Found"


def test_process_row_exception(compare_command, monkeypatch):
    """
    Tests the _process_row method when the Crawler raises an exception.
    """
    row_data = {
        "URL": "http://broken.com",
        "Meta Name": "description",
        "Expected Content": "Anything",
    }
    row = pd.Series(row_data)

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.get_meta_content_by_name.side_effect = RequestException(
        "Network Error"
    )

    mock_logger = MagicMock()
    monkeypatch.setattr("commands.compare_metas.logger", mock_logger)

    with patch("commands.compare_metas.Crawler", return_value=mock_crawler_instance):
        result = compare_command._process_row(
            row, "URL", "Meta Name", "Expected Content", MagicMock(spec=rq.Session)
        )

    mock_logger.error.assert_called_once_with(
        "Error processing URL http://broken.com: Network Error"
    )
    assert result["Match?"] is False
    assert "Error: Network Error" in result["Found Content"]
