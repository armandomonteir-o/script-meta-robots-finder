from unittest.mock import patch, Mock
from core.crawler import Crawler
from requests.exceptions import RequestException


def test_find_meta_by_name_should_return_true_if_tag_exists():
    """
    Verifies that find_meta_by_name returns True when the target meta tag exists.
    """
    fake_html_with_tag = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="robots" content="index, follow">
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html_with_tag
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.find_meta_by_name("robots")
        assert result is True


def test_find_meta_by_name_should_return_false_if_tag_not_exists():
    """
    Verifies that find_meta_by_name returns False when the target meta tag is missing.
    """
    fake_html_without_tag = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="title" content="Meta title">
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html_without_tag
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.find_meta_by_name("robots")
        assert result is False


def test_get_meta_content_by_name_should_return_content():
    """
    Verifies that get_meta_content_by_name correctly extracts the content from a meta tag.
    """
    expected_content = "This is the test description."
    fake_html = f"""
    <html>
        <head>
            <meta name="description" content="{expected_content}">
        </head>
        <body></body>
    </html>
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.get_meta_content_by_name("description")
        assert result == expected_content


def test_get_meta_content_by_name_should_return_none_if_tag_not_exists():
    """
    Verifies that get_meta_content_by_name returns None if the target tag does not exist.
    """
    fake_html = """
    <html>
        <head>
            <meta name="title" content="A different tag">
        </head>
        <body></body>
    </html>
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.get_meta_content_by_name("description")
        assert result is None


def test_get_meta_content_by_name_should_return_none_if_content_missing():
    """
    Verifies that get_meta_content_by_name returns None if the tag exists but lacks the 'content' attribute.
    """
    fake_html_malformed_tag = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description">
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html_malformed_tag
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.get_meta_content_by_name("description")
        assert result is None


def test_fetch_sitemap_urls_parses_simple_sitemap():
    """
    Verifies that fetch_sitemap_urls correctly extracts URLs from a simple final sitemap.
    """
    fake_simple_sitemap_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.com/page1</loc>
      </url>
      <url>
        <loc> https://example.com/page2 </loc>
      </url>
      <url>
         </url>
    </urlset>
    """
    expected_urls = {"https://example.com/page1", "https://example.com/page2"}

    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_simple_sitemap_xml
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com/sitemap.xml", session=mock_session, tags_to_check=[]
        )

        result_urls = crawler_instance.fetch_sitemap_urls()

        assert result_urls == expected_urls
        mock_html_search.assert_called_once()


def test_fetch_sitemap_urls_parses_sitemap_index():
    """
    Verifies that fetch_sitemap_urls processes a sitemap index,
    fetching and aggregating URLs from child sitemaps.
    """
    fake_index_xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://example.com/sitemap_part1.xml</loc>
      </sitemap>
      <sitemap>
        <loc> https://example.com/sitemap_part2.xml </loc>
      </sitemap>
    </sitemapindex>
    """
    fake_sitemap_part1_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/part1/pageA</loc></url>
    </urlset>
    """
    fake_sitemap_part2_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/part2/pageB</loc></url>
      <url><loc>https://example.com/part1/pageA</loc></url> </urlset>
    """
    expected_urls = {
        "https://example.com/part1/pageA",
        "https://example.com/part2/pageB",
    }

    def mock_search_side_effect(self_instance):
        if self_instance.url == "https://example.com/sitemap_index.xml":
            return fake_index_xml
        elif self_instance.url == "https://example.com/sitemap_part1.xml":
            return fake_sitemap_part1_xml
        elif self_instance.url == "https://example.com/sitemap_part2.xml":
            return fake_sitemap_part2_xml
        raise ValueError(f"Unexpected URL in mock: {self_instance.url}")

    with patch(
        "core.crawler.Crawler.html_search",
        side_effect=mock_search_side_effect,
        autospec=True,
    ) as mock_html_search:
        mock_session = Mock()
        crawler_instance = Crawler(
            "https://example.com/sitemap_index.xml",
            session=mock_session,
            tags_to_check=[],
        )

        result_urls = crawler_instance.fetch_sitemap_urls()

        assert result_urls == expected_urls
        assert mock_html_search.call_count == 3


def test_fetch_sitemap_urls_handles_network_error():
    """
    Verifies that fetch_sitemap_urls returns None when html_search fails.
    """
    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.side_effect = RequestException("Simulated connection failure")
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://brokenurl.com/sitemap.xml", session=mock_session, tags_to_check=[]
        )

        result = crawler_instance.fetch_sitemap_urls()

        assert result is None
        mock_html_search.assert_called_once()


def test_fetch_sitemap_urls_handles_invalid_xml():
    """
    Verifies that fetch_sitemap_urls returns an empty set
    when the content fetched is not valid XML or not a sitemap format.
    """
    fake_invalid_xml = "<html><body>This is not XML</body></html>"

    with patch("core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_invalid_xml
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com/invalid.xml", session=mock_session, tags_to_check=[]
        )

        result = crawler_instance.fetch_sitemap_urls()

        assert result == set()
        mock_html_search.assert_called_once()
