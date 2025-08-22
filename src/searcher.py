import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def html_search(url: str) -> str:
    """Fetches the HTML content of a given URL.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the URL.
    """

    try:
        res = rq.get(url, timeout=10)
        res.raise_for_status()
        return res.text
    except RequestException as e:
        logger.error(f"Failed to access URL {url}: {e}")
        raise e


def find_metarobots(res: str) -> bool:
    """Finds the meta robots tag in the HTML content.

    Args:
        res (str): The HTML content to search.

    Returns:
        bool: True if the meta robots tag is found, False otherwise.
    """
    soup = BeautifulSoup(res, "html.parser")

    meta_datas = soup.find_all("meta", {"name": "robots"})

    return len(meta_datas) > 0
