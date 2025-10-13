import pandas as pd
from reporting.excel_reader import ExcelReader
from pandas.testing import assert_frame_equal
import pytest


def test_read_spreadsheet(tmp_path):
    """
    Verifies that read_spreadsheet correctly reads data from an Excel file.
    """

    test_dir = tmp_path
    test_file_path = test_dir / "test_data.xlsx"

    expected_df = pd.DataFrame(
        {
            "URL": ["http://site1.com", "http://site2.com"],
            "Meta Name": ["description", "title"],
        }
    )

    expected_df.to_excel(test_file_path, index=False)

    reader = ExcelReader(str(test_file_path))

    result_df = reader.read_spreadsheet()

    assert_frame_equal(result_df, expected_df)


def test_read_spreadsheet_raises_file_not_found():
    """
    Verifies that read_spreadsheet raises FileNotFoundError for a non-existent file.
    """

    reader = ExcelReader("path/that/does/not/exist.xlsx")

    with pytest.raises(FileNotFoundError):
        reader.read_spreadsheet()


def test_read_column_returns_correct_list():
    """
    Verifies that read_column correctly extracts a column into a list.
    """
    test_df = pd.DataFrame(
        {
            "URL": ["site1.com", "site2.com", "site3.com"],
            "Status": [200, 404, 200],
        }
    )

    expected_list = ["site1.com", "site2.com", "site3.com"]

    result_list = ExcelReader.read_column(test_df, "URL")

    assert result_list == expected_list


def test_read_column_raises_key_error_for_missing_column():
    """
    Verifies that read_column raises a KeyError if the column does not exist.
    """

    test_df = pd.DataFrame({"URL": ["site1.com"]})

    with pytest.raises(KeyError):
        ExcelReader.read_column(test_df, "Coluna Inexistente")


def test_read_column_is_case_insensitive():
    """
    Verifies that read_column can find a column regardless of the case provided.
    """
    test_df = pd.DataFrame({"URL": ["site1.com", "site2.com"]})
    expected_list = ["site1.com", "site2.com"]

    result_list = ExcelReader.read_column(test_df, "url")

    assert result_list == expected_list
