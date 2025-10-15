import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup, Tag
import logging
import time
from typing import List, Dict, Optional

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

    def get_meta_content_by_name(self, meta_name: str) -> str | None:
        """Finds a meta tag by name and returns its content.

        Args:
            meta_name (str): The name of the meta tag to find (e.g., 'description').

        Returns:
            str | None: The content of the meta tag if found, otherwise None.
        """
        if self.soup is None:
            try:
                res = self.html_search()
                self.soup = BeautifulSoup(res, "html.parser")
            except RequestException:
                return None

        meta_tag = self.soup.find("meta", {"name": meta_name})

        if isinstance(meta_tag, Tag) and "content" in meta_tag.attrs:
            return str(meta_tag["content"])
        else:
            return None

    def fetch_sitemap_urls(self) -> Optional[List[str]]:
        """
        Fetches and parses a sitemap.xml file to extract all URLs.

        Returns:
            Optional[List[str]]: A list of URLs found in the sitemap,
                                 or None if an error occurs (e.g., network error, invalid XML).
        """
        try:

            xml_content = self.html_search()

            self.soup = BeautifulSoup(xml_content, "xml")

            loc_tags = self.soup.find_all("loc")

            urls = [tag.text for tag in loc_tags]

            return urls
        except Exception as e:
            logger.error(f"Error processing sitemap {self.url}: {e}")
            return None
