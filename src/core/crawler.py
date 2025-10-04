import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import logging
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class Crawler:
    def __init__(self, url: str, session: rq.Session, tags_to_check: List[str]):
        self.url = url
        self.session = session
        self.tags_to_check = tags_to_check
        self.soup = None

    def html_search(self) -> str:
        """Fetches the HTML content of a given URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content of the URL.
        """

        try:
            res = self.session.get(self.url, timeout=10, headers=HEADERS)
            res.raise_for_status()
            return res.text
        except RequestException as e:
            logger.error(f"Failed to access URL {self.url}: {e}")
            raise e
        finally:
            time.sleep(1)

    def find_meta_by_name(self, meta_name: str) -> bool:
        """Finds the meta tag (defined in meta_name) in the HTML content.

        Args:
            res (str): The HTML content to search.

        Returns:
            bool: True if the meta_name tag is found, False otherwise.
        """
        if self.soup is None:
            try:
                res = self.html_search()
                self.soup = BeautifulSoup(res, "html.parser")
            except RequestException:
                return False

        meta_datas = self.soup.find_all("meta", {"name": meta_name})
        return len(meta_datas) > 0

    def execute_scan(self) -> Dict[str, bool]:

        res = {}

        for tag in self.tags_to_check:
            is_found = self.find_meta_by_name(tag)
            res[tag] = is_found

        return res
