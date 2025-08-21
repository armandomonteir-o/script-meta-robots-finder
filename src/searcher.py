import requests as rq
from bs4 import BeautifulSoup
from logging import log


def html_search(url: str) -> str:

    res = rq.get(url)

    if res.status_code == 200:
        return res.text
    else:
        raise ConnectionError


def find_metarobots(res: str) -> bool:
    soup = BeautifulSoup(res, "html.parser")

    meta_datas = soup.find_all("meta", {"name": "robots"})

    return len(meta_datas) > 0
