from unittest.mock import patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal
from commands.sitemap_check import SitemapCheckCommand
import pytest
import requests as rq
from core.crawler import Crawler


@pytest.fixture
def sitemap_command():
    """Provides a clean instance of SitemapCheckCommand for each test."""
    return SitemapCheckCommand()


def test_sitemap_check_execute_flow(sitemap_command):
    """
    Integration test for the SitemapCheck command's execute method.

    This test verifies the entire orchestration flow by mocking all external
    dependencies, such as file reading and network calls, ensuring that
    the command logic correctly processes data and generates the expected report.
    """

    fake_args = MagicMock()
    fake_args.file_path = "fake/sitemap_audit.xlsx"
    fake_args.sitemap_col = "Sitemap"
    fake_args.urls_col = "Expected URLs"

    fake_sheet_data = pd.DataFrame(
        {
            "Sitemap": ["http://test.com/sitemap.xml", "http://test.com/sitemap.xml"],
            "Expected URLs": ["http://test.com/page-1", "http://test.com/page-2"],
        }
    )

    fake_sitemap_urls_set = {
        "http://test.com/page-1",
        "http://test.com/other-page",
    }

    expected_report_data = [
        {"Expected URLs": "http://test.com/page-1", "Found in Sitemap?": True},
        {"Expected URLs": "http://test.com/page-2", "Found in Sitemap?": False},
    ]
    expected_df = pd.DataFrame(expected_report_data)

    with patch(
        "commands.sitemap_check.SitemapCheckCommand._get_valid_sheet_data"
    ) as mock_get_sheet, patch(
        "commands.sitemap_check.SitemapCheckCommand._ensure_multiple_columns_exist"
    ) as mock_ensure_cols, patch(
        "commands.sitemap_check.SitemapCheckCommand._fetch_and_prepare_sitemap_set"
    ) as mock_fetch_sitemap, patch(
        "commands.sitemap_check.SitemapCheckCommand._run_concurrent_tasks"
    ) as mock_run_tasks, patch(
        "commands.sitemap_check.ExcelWriter.create_spreadsheet_with_results"
    ) as mock_excel_writer:

        mock_get_sheet.return_value = fake_sheet_data
        mock_ensure_cols.return_value = ["Sitemap", "Expected URLs"]
        mock_fetch_sitemap.return_value = fake_sitemap_urls_set
        mock_run_tasks.return_value = expected_report_data

        sitemap_command.execute(fake_args)

        mock_get_sheet.assert_called_once()
        mock_ensure_cols.assert_called_once()
        mock_fetch_sitemap.assert_called_once()
        mock_run_tasks.assert_called_once()
        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]

        called_df = called_df.sort_values(by="Expected URLs").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="Expected URLs").reset_index(drop=True)

        assert_frame_equal(called_df, expected_df)


def test_process_row_url_found(sitemap_command):
    """
    Tests that _process_row correctly identifies a URL that is present in the sitemap set.
    """

    sitemap_urls_set = {"http://example.com/page1", "http://example.com/page2"}
    row_data = {"Expected URLS": "http://example.com/page1"}
    row = pd.Series(row_data)

    result = sitemap_command._process_row(row, "Expected URLS", sitemap_urls_set)

    expected_result = {
        "Expected URLS": "http://example.com/page1",
        "Found in Sitemap?": True,
    }
    assert result == expected_result


def test_process_row_url_not_found(sitemap_command):
    """
    Tests that _process_row correctly identifies a URL that is NOT present in the sitemap set.
    """
    sitemap_urls_set = {"http://example.com/page1", "http://example.com/page2"}
    row_data = {"Expected URLS": "http://example.com/page3"}
    row = pd.Series(row_data)

    result = sitemap_command._process_row(row, "Expected URLS", sitemap_urls_set)

    expected_result = {
        "Expected URLS": "http://example.com/page3",
        "Found in Sitemap?": False,
    }
    assert result == expected_result


def test_process_row_url_strips_whitespace(sitemap_command):
    """
    Tests that _process_row correctly strips whitespace from the URL before checking
    and returns the stripped URL.
    """
    sitemap_urls_set = {"http://example.com/page1"}

    row_data = {"Expected URLS": "  http://example.com/page1  "}
    row = pd.Series(row_data)

    result = sitemap_command._process_row(row, "Expected URLS", sitemap_urls_set)

    assert result["Found in Sitemap?"] is True
    assert result["Expected URLS"] == "http://example.com/page1"


def test_fetch_and_prepare_sitemap_set_success(sitemap_command):
    """
    Tests the success path for fetching and parsing a sitemap URL.
    Ensures the Crawler is instantiated and called correctly, and its set of URLs is returned.
    """
    sitemap_url = "http://example.com/sitemap.xml"
    fake_sheet_data = pd.DataFrame({"Sitemap": [sitemap_url]})

    expected_urls_set = {"http://example.com/page1", "http://example.com/page2"}

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.fetch_sitemap_urls.return_value = expected_urls_set

    mock_session = MagicMock(spec=rq.Session)
    mock_session_context_manager = MagicMock()
    mock_session_context_manager.__enter__.return_value = mock_session

    with patch(
        "commands.sitemap_check.rq.Session", return_value=mock_session_context_manager
    ), patch(
        "commands.sitemap_check.Crawler", return_value=mock_crawler_instance
    ) as mock_crawler_class:

        result_set = sitemap_command._fetch_and_prepare_sitemap_set(
            fake_sheet_data, "Sitemap"
        )

        mock_crawler_class.assert_called_once_with(sitemap_url, mock_session, [])

        mock_crawler_instance.fetch_sitemap_urls.assert_called_once()

        assert result_set == expected_urls_set


def test_fetch_and_prepare_sitemap_set_failure(sitemap_command):
    """
    Tests the failure path for fetching a sitemap (e.g., crawler returns None),
    expecting the method to propagate the None.
    """
    sitemap_url = "http://example.com/sitemap.xml"
    fake_sheet_data = pd.DataFrame({"Sitemap": [sitemap_url]})

    mock_crawler_instance = MagicMock(spec=Crawler)
    mock_crawler_instance.fetch_sitemap_urls.return_value = None

    mock_session = MagicMock(spec=rq.Session)
    mock_session_context_manager = MagicMock()
    mock_session_context_manager.__enter__.return_value = mock_session

    with patch(
        "commands.sitemap_check.rq.Session", return_value=mock_session_context_manager
    ), patch(
        "commands.sitemap_check.Crawler", return_value=mock_crawler_instance
    ) as mock_crawler_class:

        result_set = sitemap_command._fetch_and_prepare_sitemap_set(
            fake_sheet_data, "Sitemap"
        )

        mock_crawler_class.assert_called_once_with(sitemap_url, mock_session, [])

        mock_crawler_instance.fetch_sitemap_urls.assert_called_once()

        assert result_set is None
