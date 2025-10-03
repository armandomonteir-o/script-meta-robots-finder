import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class Crawler:
    def __init__(self, url: str, session: rq.Session):
        self.url = url
        self.session = session

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

    def find_metarobots(self) -> bool:
        """Finds the meta robots tag in the HTML content.

        Args:
            res (str): The HTML content to search.

        Returns:
            bool: True if the meta robots tag is found, False otherwise.
        """
        res = self.html_search()

        soup = BeautifulSoup(res, "html.parser")

        meta_datas = soup.find_all("meta", {"name": "robots"})

        return len(meta_datas) > 0

    def link_checker(self):
        """Checks a single link for the meta robots tag.

        Args:
            link (str): The URL to check.

        Returns:
            Union[bool, str]: True if the tag is found, False if not, and "Error" if an exception occurs.
        """
        try:

            finder = self.find_metarobots()

            if finder == True:
                logger.info(f"SUCCESS: Meta tag 'robots' found in: {self.url}")
                return True
            else:
                logger.info(f"PARTIAL: Meta tag 'robots' not found in: {self.url}")
                return False
        except RequestException as e:
            logger.error((f"ERROR: URL check for {self.url} failed. Reason: {e}"))
            return "Error"
        except Exception as e:
            logger.critical(f"UNEXPECTED ERROR when processing {self.url}: {e}")
            return "Error"
