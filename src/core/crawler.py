from concurrent.futures import ThreadPoolExecutor, as_completed
import requests as rq
from requests.exceptions import RequestException
from bs4 import BeautifulSoup, Tag
import logging
import time
from typing import List, Dict, Optional, Set

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

    def _fetch_single_sitemap_urls(self, url: str) -> Optional[Set[str]]:
        """
        Helper function to fetch and parse a single sitemap URL.

        This method is designed to be called concurrently by a ThreadPoolExecutor.
        It creates a new, temporary Crawler instance for the specified URL
        (reusing the parent's requests.Session) and recursively calls the
        main fetch_sitemap_urls() method to parse it.

        Args:
            url (str): The URL of a sitemap file (which could be
                     a final sitemap or another sitemap index).

        Returns:
            Optional[Set[str]]: A set of URLs found within that sitemap,
                                or None if processing fails for this specific URL.
        """
        try:

            child_crawler = Crawler(url, self.session, [])

            return child_crawler.fetch_sitemap_urls()

        except Exception as e:
            logger.warning(f"Failed to process child sitemap {url}: {e}")
            return None

    def fetch_sitemap_urls(self) -> Optional[Set[str]]:
        """
        Fetches and parses a sitemap file (or sitemap index file)
        recursively to extract all final URLs.

        This method first downloads the XML content from the Crawler's main URL.
        It then inspects the XML to determine if it is a sitemap index
        (containing <sitemap> tags) or a final sitemap (containing <url> tags).

        - If it's a sitemap index, it extracts all child sitemap URLs
          and uses a ThreadPoolExecutor to concurrently call this
          same method for each child sitemap.
        - If it's a final sitemap, it extracts all individual page URLs (<loc>).

        All results are aggregated into a single set to ensure uniqueness.

        Returns:
            Optional[Set[str]]: A set of all unique URL strings found in the
                                sitemap and all its children. Returns None if
                                the initial URL fetch or parsing fails.
        """
        try:

            xml_content = self.html_search()
            self.soup = BeautifulSoup(xml_content, "xml")

            all_urls = set()

            sitemap_index_tags = self.soup.find_all("sitemap")

            if sitemap_index_tags:
                print(
                    f" -> Sitemap Index detected. Analyzing {len(sitemap_index_tags)} child sitemaps..."
                )
                logger.info(
                    f"Sitemap Index found at {self.url}. Processing {len(sitemap_index_tags)} child sitemaps."
                )

                sitemap_urls_to_crawl = []
                for tag in sitemap_index_tags:
                    if isinstance(tag, Tag):
                        loc = tag.find("loc")
                        if loc:
                            sitemap_urls_to_crawl.append(loc.text.strip())

                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(self._fetch_single_sitemap_urls, url)
                        for url in sitemap_urls_to_crawl
                    ]

                    for future in as_completed(futures):
                        result_set = future.result()
                        if result_set:
                            all_urls.update(result_set)

            url_tags = self.soup.find_all("url")
            if url_tags:
                print(
                    f" -> Standard Sitemap detected. Analyzing {len(url_tags)} URLs..."
                )
                logger.info(
                    f"Standard sitemap found at {self.url}. Processing {len(url_tags)} URLs."
                )

                for tag in url_tags:
                    if isinstance(tag, Tag):
                        loc = tag.find("loc")
                        if loc:

                            all_urls.add(loc.text.strip())

            return all_urls

        except Exception as e:
            logger.error(f"Error processing sitemap {self.url}: {e}")
            return None
