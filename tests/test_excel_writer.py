import pytest
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


def test_create_spreadsheet_with_empty_dataframe(tmp_path):
    """
    Verifies that an empty DataFrame is handled correctly, creating a valid file with only headers.
    """
    output_file = tmp_path / "empty_report.xlsx"

    empty_df = pd.DataFrame(
        {
            "URL": pd.Series(dtype="str"),
            "Status": pd.Series(dtype="object"),
            "Match?": pd.Series(dtype="object"),
        }
    )

    ExcelWriter.create_spreadsheet_with_results(empty_df, filename=str(output_file))

    result_df = pd.read_excel(output_file, nrows=0)

    assert_frame_equal(empty_df, result_df)


def test_assert_frame_equal_fails_for_different_data(tmp_path):
    """
    Verifies if the testing method (assert_frame_equal) correctly fails
    when comparing two different DataFrames.
    """
    output_file = tmp_path / "report.xlsx"

    df_to_write = pd.DataFrame({"URL": ["site1.com"], "robots": [True]})
    different_df = pd.DataFrame({"URL": ["site-diferente.com"], "robots": [True]})

    ExcelWriter.create_spreadsheet_with_results(df_to_write, filename=str(output_file))

    result_df = pd.read_excel(output_file, nrows=len(df_to_write))

    with pytest.raises(AssertionError):
        assert_frame_equal(result_df, different_df)
