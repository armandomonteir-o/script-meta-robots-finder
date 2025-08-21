import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def html_search(url: str) -> str:

    try:
        res = rq.get(url, timeout=10)
        res.raise_for_status()
        return res.text
    except RequestException as e:
        logger.error(f"Falha ao acessar a URL {url}: {e}")
        raise e


def find_metarobots(res: str) -> bool:
    soup = BeautifulSoup(res, "html.parser")

    meta_datas = soup.find_all("meta", {"name": "robots"})

    return len(meta_datas) > 0
