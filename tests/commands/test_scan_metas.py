from unittest.mock import patch, MagicMock
import pandas as pd
from commands.scan_metas import ScanMetasCommand
import pytest
from core.crawler import Crawler
from requests.exceptions import RequestException
import requests as rq


@pytest.fixture
def scan_command():
    """Provides a clean instance of ScanMetasCommand for each test."""
    return ScanMetasCommand()


def test_scan_metas_execute_flow_after_refactor(scan_command):
    """
    Integration test for the refactored ScanMetasCommand execute method.
    Verifies the flow by mocking the new validation helper methods.
    """
    fake_args = MagicMock()
    fake_args.file_path = "fake/path.xlsx"
    fake_args.column_name = "URL"
    fake_args.checks = ["robots"]

    fake_sheet_data = pd.DataFrame({"URL": ["http://site1.com", "http://site2.com"]})
    fake_urls = ["http://site1.com", "http://site2.com"]

    fake_report_data = [
        {"URL": "http://site1.com", "robots": True},
        {"URL": "http://site2.com", "robots": False},
    ]

    with patch(
        "commands.scan_metas.ScanMetasCommand._get_valid_sheet_data"
    ) as mock_get_sheet, patch(
        "commands.scan_metas.ScanMetasCommand._get_validated_urls_from_column"
    ) as mock_get_urls, patch(
        "commands.scan_metas.ScanMetasCommand._run_concurrent_tasks"
    ) as mock_run_tasks, patch(
        "commands.scan_metas.ExcelWriter.create_spreadsheet_with_results"
    ) as mock_excel_writer:

        mock_get_sheet.return_value = fake_sheet_data
        mock_get_urls.return_value = fake_urls
        mock_run_tasks.return_value = fake_report_data

        scan_command.execute(fake_args)

        mock_get_sheet.assert_called_once()
        mock_get_urls.assert_called_once()
        mock_run_tasks.assert_called_once()
        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]
        expected_df = pd.DataFrame(fake_report_data)

        called_df = called_df.sort_values(by="URL").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="URL").reset_index(drop=True)

        pd.testing.assert_frame_equal(called_df, expected_df)


def test_process_url_success(scan_command):
    """
    Tests the _process_url method for a successful crawl.
    Ensures it correctly calls the Crawler and formats the success dictionary.
    """
    url_teste = "http://example.com"
    checks_teste = ["robots", "viewport"]
    sessao_mock = MagicMock(spec=rq.Session)

    mock_scan_results = {"robots": True, "viewport": False}

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.execute_scan.return_value = mock_scan_results

    with patch(
        "commands.scan_metas.Crawler", return_value=mock_crawler_instance
    ) as mock_crawler_class:

        result = scan_command._process_url(url_teste, checks_teste, sessao_mock)

        mock_crawler_class.assert_called_once_with(url_teste, sessao_mock, checks_teste)

        mock_crawler_instance.execute_scan.assert_called_once()

        expected_result = {
            "URL": "http://example.com",
            "robots": True,
            "viewport": False,
        }
        assert result == expected_result


def test_process_url_exception(scan_command, monkeypatch):
    """
    Tests the _process_url method when the Crawler raises an exception.
    Ensures the exception is caught, logged, and an error dictionary is returned.
    """
    url_teste = "http://broken-site.com"
    checks_teste = ["robots"]
    sessao_mock = MagicMock(spec=rq.Session)

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.execute_scan.side_effect = RequestException(
        "Falha de conexão"
    )

    mock_logger = MagicMock()
    monkeypatch.setattr("commands.scan_metas.logger", mock_logger)

    with patch("commands.scan_metas.Crawler", return_value=mock_crawler_instance):

        result = scan_command._process_url(url_teste, checks_teste, sessao_mock)

        mock_logger.error.assert_called_once_with(
            f"'{url_teste}' generated an exception: Falha de conexão"
        )

        expected_result = {"URL": "http://broken-site.com", "robots": "Error"}
        assert result == expected_result
