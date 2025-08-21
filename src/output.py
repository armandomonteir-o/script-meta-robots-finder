from typing import List, Union
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def create_spreadsheet_with_results(urls: List[str], results: List[Union[bool, str]]):

    data = {"urls:": urls, "results": results}

    sheet = pd.DataFrame(data)

    sheet.to_excel("resultados.xlsx", index=False)
    logger.info("Spreadsheet created successfully")
    print("Spreadsheet created successfully")
