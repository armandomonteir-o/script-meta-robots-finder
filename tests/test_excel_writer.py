# tests/test_excel_writer.py

import pandas as pd
from pandas.testing import assert_frame_equal
from src.reporting.excel_writer import ExcelWriter


def test_create_spreadsheet_with_results(tmp_path):
    """
    Verifies that a spreadsheet is created with the correct data.
    """

    output_dir = tmp_path / "results"

    output_file = output_dir / "results.xlsx"

    test_df = pd.DataFrame({"URL": ["http://site1.com"], "robots": [True]})

    ExcelWriter.create_spreadsheet_with_results(test_df, filename=str(output_file))

    result_df = pd.read_excel(output_file, nrows=len(test_df))

    assert_frame_equal(test_df, result_df)
