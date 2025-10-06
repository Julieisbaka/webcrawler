"""
Custom exceptions for the webcrawler package.
"""


class CrawlerError(Exception):
    """Base exception for crawler-related errors."""

    pass


class InvalidURLError(CrawlerError):
    """Raised when an invalid URL is encountered."""

    pass


class RequestError(CrawlerError):
    """Raised when a network request fails."""

    pass


class ConfigurationError(CrawlerError):
    """Raised when crawler configuration is invalid."""

    pass


class RobotsTxtError(CrawlerError):
    """Raised when robots.txt parsing fails."""

    pass
