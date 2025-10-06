"""
Basic tests for the webcrawler package.
"""

from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest

from webcrawler import WebCrawler
from webcrawler.exceptions import ConfigurationError, InvalidURLError
from webcrawler.utils import LinkExtractor, URLValidator


class TestURLValidator:
    """Tests for URLValidator class."""

    def test_valid_http_url(self):
        validator = URLValidator()
        assert validator.is_valid_url("http://example.com")

    def test_valid_https_url(self):
        validator = URLValidator()
        assert validator.is_valid_url("https://example.com")

    def test_invalid_scheme(self):
        validator = URLValidator()
        assert not validator.is_valid_url("ftp://example.com")
        assert not validator.is_valid_url("file:///path/to/file")

    def test_skip_file_extensions(self):
        validator = URLValidator()
        assert not validator.is_valid_url("https://example.com/file.pdf")
        assert not validator.is_valid_url("https://example.com/image.jpg")
        assert not validator.is_valid_url("https://example.com/archive.zip")

    def test_domain_filtering(self):
        allowed_domains = {"example.com"}
        validator = URLValidator(allowed_domains)

        assert validator.is_valid_url("https://example.com/page")
        assert not validator.is_valid_url("https://other.com/page")

    def test_normalize_url(self):
        validator = URLValidator()

        # Test relative URL resolution
        result = validator.normalize_url("page.html", "https://example.com/")
        assert result == "https://example.com/page.html"

        # Test query parameter preservation
        result = validator.normalize_url("page?param=value", "https://example.com/")
        assert result == "https://example.com/page?param=value"

        # Test fragment removal
        result = validator.normalize_url("page#section", "https://example.com/")
        assert result == "https://example.com/page"


class TestLinkExtractor:
    """Tests for LinkExtractor class."""

    def test_extract_basic_links(self):
        validator = URLValidator()
        extractor = LinkExtractor(validator)

        html = """
        <html>
            <body>
                <a href="https://example.com/page1">Link 1</a>
                <a href="https://example.com/page2">Link 2</a>
            </body>
        </html>
        """

        links = extractor.extract_links(html, "https://example.com/")
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links

    def test_extract_relative_links(self):
        validator = URLValidator()
        extractor = LinkExtractor(validator)

        html = """
        <html>
            <body>
                <a href="/absolute">Absolute</a>
                <a href="relative.html">Relative</a>
            </body>
        </html>
        """

        links = extractor.extract_links(html, "https://example.com/")
        assert "https://example.com/absolute" in links
        assert "https://example.com/relative.html" in links

    def test_extract_title(self):
        validator = URLValidator()
        extractor = LinkExtractor(validator)

        html = "<html><head><title>Test Page</title></head></html>"
        title = extractor.extract_title(html)
        assert title == "Test Page"

    def test_extract_meta_description(self):
        validator = URLValidator()
        extractor = LinkExtractor(validator)

        html = """
        <html>
            <head>
                <meta name="description" content="Test description">
            </head>
        </html>
        """

        description = extractor.extract_meta_description(html)
        assert description == "Test description"


class TestWebCrawler:
    """Tests for WebCrawler class."""

    def test_initialization(self):
        crawler = WebCrawler("https://example.com")
        assert crawler.seed_url == "https://example.com"
        assert crawler.max_depth == 3
        assert crawler.delay == 1.0
        assert crawler.max_pages == 100

    def test_invalid_seed_url(self):
        with pytest.raises(ConfigurationError):
            WebCrawler("invalid-url")

    def test_invalid_max_depth(self):
        with pytest.raises(ConfigurationError):
            WebCrawler("https://example.com", max_depth=-1)

    def test_invalid_max_pages(self):
        with pytest.raises(ConfigurationError):
            WebCrawler("https://example.com", max_pages=0)

    @patch("webcrawler.crawler.requests.Session.get")
    def test_crawl_single_page(self, mock_get):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><title>Test</title><a href="/page2">Link</a></html>'
        mock_response.content = (
            b'<html><title>Test</title><a href="/page2">Link</a></html>'
        )
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        crawler = WebCrawler("https://example.com", max_depth=0, max_pages=1)
        results = crawler.crawl()

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com"
        assert results[0]["title"] == "Test"
        assert results[0]["status_code"] == 200

    def test_get_summary(self):
        crawler = WebCrawler("https://example.com")

        # Add some mock data
        crawler.crawled_data = [
            {"url": "https://example.com", "error": None, "links": ["link1", "link2"]},
            {
                "url": "https://example.com/page2",
                "error": "Connection error",
                "links": [],
            },
        ]
        crawler.visited_urls = {"https://example.com", "https://example.com/page2"}

        summary = crawler.get_summary()
        assert summary["total_pages_crawled"] == 2
        assert summary["successful_pages"] == 1
        assert summary["failed_pages"] == 1
        assert summary["total_links_found"] == 2

    def test_get_failed_urls(self):
        crawler = WebCrawler("https://example.com")

        crawler.crawled_data = [
            {"url": "https://example.com", "error": None},
            {"url": "https://example.com/page2", "error": "Connection error"},
        ]

        failed = crawler.get_failed_urls()
        assert len(failed) == 1
        assert failed[0]["url"] == "https://example.com/page2"

    def test_get_successful_urls(self):
        crawler = WebCrawler("https://example.com")

        crawler.crawled_data = [
            {"url": "https://example.com", "error": None},
            {"url": "https://example.com/page2", "error": "Connection error"},
        ]

        successful = crawler.get_successful_urls()
        assert len(successful) == 1
        assert successful[0]["url"] == "https://example.com"


if __name__ == "__main__":
    pytest.main([__file__])
