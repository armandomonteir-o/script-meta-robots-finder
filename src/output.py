import pandas as pd
import logging

logger = logging.getLogger(__name__)


def create_planilha_with_results(urls: list[str], results: list[bool | str]):

    data = {"urls:": urls, "results": results}

    sheet = pd.DataFrame(data)

    sheet.to_excel("resultados.xlsx", index=False)
    logger.info(f"Planilha criada com sucesso")
