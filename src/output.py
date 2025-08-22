from typing import List, Union
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def create_spreadsheet_with_results(urls: List[str], results: List[Union[bool, str]]):
    """Creates a spreadsheet with the results of the meta robots search.

    Args:
        urls (List[str]): A list of URLs that were searched.
        results (List[Union[bool, str]]): A list of results for each URL.
    """

    data = {"urls:": urls, "results": results}

    sheet = pd.DataFrame(data)

    sheet.to_excel("resultados.xlsx", index=False)
    logger.info("Spreadsheet created successfully")
    print("Spreadsheet created successfully")
