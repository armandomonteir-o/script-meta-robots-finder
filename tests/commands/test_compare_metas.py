from unittest.mock import patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal
from commands.compare_metas import CompareMetasCommand


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
