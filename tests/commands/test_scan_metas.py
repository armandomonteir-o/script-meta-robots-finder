from unittest.mock import patch, MagicMock
import pandas as pd
from commands.scan_metas import ScanMetasCommand


def test_scan_metas_execute_flow():
    """
    Integration test for the ScanMetasCommand execute method.
    Verifies the overall flow from reading data to writing the final report.
    """

    fake_args = MagicMock()
    fake_args.file_path = "fake/path.xlsx"
    fake_args.column_name = "URL"
    fake_args.checks = ["robots"]

    fake_urls = ["http://site1.com", "http://site2.com"]

    fake_report_data = [
        {"URL": "http://site1.com", "robots": True},
        {"URL": "http://site2.com", "robots": False},
    ]

    with patch("commands.scan_metas.ExcelReader") as MockExcelReader, patch(
        "commands.scan_metas.ScanMetasCommand._process_url"
    ) as mock_process_url, patch(
        "commands.scan_metas.ExcelWriter.create_spreadsheet_with_results"
    ) as mock_excel_writer:

        MockExcelReader.return_value.read_spreadsheet.return_value = pd.DataFrame()
        MockExcelReader.return_value.read_column.return_value = fake_urls
        mock_process_url.side_effect = [
            {"URL": "http://site1.com", "robots": True},
            {"URL": "http://site2.com", "robots": False},
        ]

        command = ScanMetasCommand()
        command.execute(fake_args)

        mock_excel_writer.assert_called_once()

        called_df = mock_excel_writer.call_args[0][0]
        expected_df = pd.DataFrame(fake_report_data)

        called_df = called_df.sort_values(by="URL").reset_index(drop=True)
        expected_df = expected_df.sort_values(by="URL").reset_index(drop=True)

        pd.testing.assert_frame_equal(called_df, expected_df)
