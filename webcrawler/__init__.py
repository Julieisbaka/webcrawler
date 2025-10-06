"""
WebCrawler - A Python package for recursive web crawling with anti-detection features.

This package provides comprehensive tools for crawling websites recursively,
starting from a seed URL and following all discovered links. It includes
advanced anti-detection features to bypass rate limits and IP bans.

Features:
    - Recursive web crawling with configurable depth
    - User agent rotation with realistic browser strings
    - Proxy rotation for IP address distribution
    - Adaptive delay management with multiple strategies
    - HTTP header randomization
    - Session management with automatic rotation
    - Robots.txt compliance (configurable)
    - Comprehensive error handling and retry logic
    - Detailed logging and monitoring

Example:
    Basic crawling:

    >>> from webcrawler import WebCrawler
    >>> crawler = WebCrawler("https://example.com", max_depth=2)
    >>> results = crawler.crawl()
    >>> crawler.save_results('results.json')

    Advanced crawling with anti-detection:

    >>> crawler = WebCrawler(
    ...     "https://example.com",
    ...     enable_anti_detection=True,
    ...     delay_strategy="adaptive",
    ...     max_pages=100
    ... )
    >>> results = crawler.crawl()
"""

from .anti_detection import (
    AntiDetectionConfig,
    DelayManager,
    ProxyRotator,
    SessionManager,
    UserAgentRotator,
    generate_random_headers,
)
from .crawler import WebCrawler
from .exceptions import CrawlerError, InvalidURLError, RequestError
from .utils import LinkExtractor, URLValidator

__version__ = "0.0.1"
__author__ = "JulieISBaka"
__email__ = "casperschorr06@gmail.com"

__all__ = [
    # Core crawler
    "WebCrawler",
    # Utility classes
    "URLValidator",
    "LinkExtractor",
    # Exception classes
    "CrawlerError",
    "InvalidURLError",
    "RequestError",
    # Anti-detection classes
    "UserAgentRotator",
    "ProxyRotator",
    "DelayManager",
    "SessionManager",
    "AntiDetectionConfig",
    "generate_random_headers",
]
