"""
Utility classes and functions for the webcrawler package.
"""

import re
from urllib.parse import urljoin, urlparse
from typing import List, Set
from bs4 import BeautifulSoup

from .exceptions import InvalidURLError


class URLValidator:
    """Validates and normalizes URLs."""
    
    # Common file extensions to skip
    SKIP_EXTENSIONS = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.exe', '.msi', '.dmg', '.deb', '.rpm',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.css', '.js', '.json', '.xml', '.rss'
    }
    
    # Valid URL schemes
    VALID_SCHEMES = {'http', 'https'}
    
    def __init__(self, allowed_domains: Set[str] = None):
        """
        Initialize URL validator.
        
        Args:
            allowed_domains: Set of allowed domains. If None, all domains are allowed.
        """
        self.allowed_domains = allowed_domains or set()
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and should be crawled.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only HTTP/HTTPS
            if parsed.scheme not in self.VALID_SCHEMES:
                return False
            
            # Check domain restrictions
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                return False
            
            # Skip unwanted file extensions
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(ext) for ext in self.SKIP_EXTENSIONS):
                return False
            
            # Skip certain patterns (optional)
            skip_patterns = [
                r'/admin/',
                r'/login',
                r'/logout',
                r'/register',
                r'/api/',
                r'\.php$',
                r'\.asp$',
                r'\.jsp$'
            ]
            
            if any(re.search(pattern, url) for pattern in skip_patterns):
                return False
            
            return True
            
        except Exception:
            return False
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Convert relative URLs to absolute URLs and normalize.
        
        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Normalized absolute URL
            
        Raises:
            InvalidURLError: If URL cannot be normalized
        """
        try:
            # Join with base URL to handle relative links
            absolute_url = urljoin(base_url, url)
            
            # Parse and reconstruct to normalize
            parsed = urlparse(absolute_url)
            
            # Remove fragment (anchor)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Add query if present
            if parsed.query:
                normalized += f"?{parsed.query}"
                
            # Remove trailing slash from path (except root)
            if normalized.endswith('/') and len(parsed.path) > 1:
                normalized = normalized[:-1]
                
            return normalized
            
        except Exception as e:
            raise InvalidURLError(f"Cannot normalize URL '{url}': {e}")


class LinkExtractor:
    """Extracts links from HTML content."""
    
    def __init__(self, url_validator: URLValidator):
        """
        Initialize link extractor.
        
        Args:
            url_validator: URL validator instance
        """
        self.url_validator = url_validator
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all valid links from HTML content.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative links
            
        Returns:
            List of valid, normalized URLs
        """
        links = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all anchor tags with href
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                
                if not href or href.startswith('#'):
                    continue
                
                try:
                    normalized_url = self.url_validator.normalize_url(href, base_url)
                    
                    if self.url_validator.is_valid_url(normalized_url):
                        links.append(normalized_url)
                        
                except InvalidURLError:
                    # Skip invalid URLs
                    continue
                    
        except Exception:
            # If parsing fails, return empty list
            pass
            
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
                
        return unique_links
    
    def extract_title(self, html_content: str) -> str:
        """
        Extract page title from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Page title or empty string if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            
            if title_tag:
                return title_tag.get_text().strip()
                
        except Exception:
            pass
            
        return ""
    
    def extract_meta_description(self, html_content: str) -> str:
        """
        Extract meta description from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Meta description or empty string if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            
            if meta_desc and meta_desc.get('content'):
                return meta_desc['content'].strip()
                
        except Exception:
            pass
            
        return ""


class RobotsTxtParser:
    """Simple robots.txt parser."""
    
    def __init__(self, robots_txt_content: str, user_agent: str = '*'):
        """
        Initialize robots.txt parser.
        
        Args:
            robots_txt_content: Content of robots.txt file
            user_agent: User agent to check rules for
        """
        self.user_agent = user_agent.lower()
        self.disallowed_paths = set()
        self.crawl_delay = 0
        
        self._parse_robots_txt(robots_txt_content)
    
    def _parse_robots_txt(self, content: str):
        """Parse robots.txt content and extract rules."""
        current_user_agent = None
        applies_to_us = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse directives
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                
                if directive == 'user-agent':
                    current_user_agent = value.lower()
                    applies_to_us = (current_user_agent == '*' or 
                                   current_user_agent == self.user_agent)
                
                elif applies_to_us:
                    if directive == 'disallow':
                        if value:
                            self.disallowed_paths.add(value)
                    elif directive == 'crawl-delay':
                        try:
                            self.crawl_delay = max(self.crawl_delay, float(value))
                        except ValueError:
                            pass
    
    def can_crawl(self, url_path: str) -> bool:
        """
        Check if a URL path can be crawled according to robots.txt.
        
        Args:
            url_path: URL path to check
            
        Returns:
            True if crawling is allowed, False otherwise
        """
        for disallowed in self.disallowed_paths:
            if url_path.startswith(disallowed):
                return False
        return True