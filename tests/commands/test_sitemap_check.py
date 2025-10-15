# Em tests/commands/test_sitemap_check.py

from unittest.mock import patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal
from commands.sitemap_check import SitemapCheck


def test_sitemap_check_execute_flow():
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
        "commands.sitemap_check.SitemapCheck._get_valid_sheet_data"
    ) as mock_get_sheet, patch(
        "commands.sitemap_check.SitemapCheck._ensure_multiple_columns_exist"
    ) as mock_ensure_cols, patch(
        "commands.sitemap_check.SitemapCheck._fetch_and_prepare_sitemap_set"
    ) as mock_fetch_sitemap, patch(
        "commands.sitemap_check.SitemapCheck._run_concurrent_tasks"
    ) as mock_run_tasks, patch(
        "commands.sitemap_check.ExcelWriter.create_spreadsheet_with_results"
    ) as mock_excel_writer:

        mock_get_sheet.return_value = fake_sheet_data
        mock_ensure_cols.return_value = ["Sitemap", "Expected URLs"]
        mock_fetch_sitemap.return_value = fake_sitemap_urls_set
        mock_run_tasks.return_value = expected_report_data

        command = SitemapCheck()
        command.execute(fake_args)

        mock_get_sheet.assert_called_once()
        mock_ensure_cols.assert_called_once()
        mock_fetch_sitemap.assert_called_once()
        mock_run_tasks.assert_called_once()
        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]

        called_df = called_df.sort_values(by="Expected URLs").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="Expected URLs").reset_index(drop=True)

        assert_frame_equal(called_df, expected_df)
