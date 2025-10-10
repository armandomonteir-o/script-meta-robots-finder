from unittest.mock import patch, Mock
from src.core.crawler import Crawler


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
    with patch("src.core.crawler.Crawler.html_search") as mock_html_search:
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
    with patch("src.core.crawler.Crawler.html_search") as mock_html_search:
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
    with patch("src.core.crawler.Crawler.html_search") as mock_html_search:
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
    with patch("src.core.crawler.Crawler.html_search") as mock_html_search:
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
    with patch("src.core.crawler.Crawler.html_search") as mock_html_search:
        mock_html_search.return_value = fake_html_malformed_tag
        mock_session = Mock()
        crawler_instance = Crawler(
            "http://fakeurl.com", session=mock_session, tags_to_check=[]
        )
        result = crawler_instance.get_meta_content_by_name("description")
        assert result is None
