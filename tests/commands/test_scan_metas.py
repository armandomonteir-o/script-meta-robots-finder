from unittest.mock import patch, MagicMock
import pandas as pd
from commands.scan_metas import ScanMetasCommand


def test_scan_metas_execute_flow_after_refactor():
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

        # Instanciamos e executamos o comando
        command = ScanMetasCommand()
        command.execute(fake_args)

        mock_get_sheet.assert_called_once()
        mock_get_urls.assert_called_once()
        mock_run_tasks.assert_called_once()
        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]
        expected_df = pd.DataFrame(fake_report_data)

        called_df = called_df.sort_values(by="URL").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="URL").reset_index(drop=True)

        pd.testing.assert_frame_equal(called_df, expected_df)
