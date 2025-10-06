"""
Main crawler module for the webcrawler package.

This module provides the core WebCrawler class with comprehensive anti-detection
features, rate limiting, proxy support, and extensive configuration options.
"""

import time
import json
import logging
import requests
import os
from typing import Set, List, Dict, Optional, Any, Tuple
from collections import deque
from urllib.parse import urlparse

from .utils import URLValidator, LinkExtractor, RobotsTxtParser
from .exceptions import CrawlerError, RequestError, ConfigurationError
from .anti_detection import (
    UserAgentRotator, ProxyRotator, DelayManager, SessionManager,
    AntiDetectionConfig, generate_random_headers
)


class WebCrawler:
    """
    A sophisticated web crawler with anti-detection features and rate limiting bypass.
    
    This crawler provides comprehensive functionality for recursive web crawling while
    implementing various anti-detection techniques to avoid IP bans and rate limits.
    
    Features:
        - User agent rotation with realistic browser strings
        - Proxy rotation for IP address distribution
        - Adaptive delay management with multiple strategies
        - Session management with automatic rotation
        - HTTP header randomization
        - Robots.txt compliance (configurable)
        - Comprehensive error handling and retry logic
        - Detailed logging and monitoring
    
    Example:
        Basic usage with anti-detection features:
        
        >>> from webcrawler import WebCrawler
        >>> crawler = WebCrawler(
        ...     seed_url="https://example.com",
        ...     max_depth=2,
        ...     enable_anti_detection=True,
        ...     delay_strategy="adaptive"
        ... )
        >>> results = crawler.crawl()
        >>> crawler.save_results('results.json')
        
        Advanced usage with proxy rotation:
        
        >>> proxies = [
        ...     {'http': 'http://proxy1:8080', 'https': 'https://proxy1:8080'},
        ...     {'http': 'http://proxy2:8080', 'https': 'https://proxy2:8080'}
        ... ]
        >>> crawler = WebCrawler(
        ...     seed_url="https://example.com",
        ...     proxy_list=proxies,
        ...     enable_proxy_rotation=True,
        ...     session_rotation_interval=25
        ... )
        >>> results = crawler.crawl()
    """
    
    def __init__(
        self,
        seed_url: str,
        max_depth: int = 3,
        delay: float = 1.0,
        max_pages: int = 100,
        same_domain_only: bool = True,
        respect_robots_txt: bool = True,
        user_agent: str = "WebCrawler/0.0.1 (Anti-Detection)",
        
        # Anti-detection features
        enable_anti_detection: bool = False,
        enable_user_agent_rotation: bool = False,
        enable_proxy_rotation: bool = False,
        enable_header_randomization: bool = False,
        delay_strategy: str = "fixed",
        min_delay: float = 1.0,
        max_delay: float = 5.0,
        session_rotation_interval: int = 50,
        
        # Proxy configuration
        proxy_list: Optional[List[Dict[str, str]]] = None,
        validate_proxies: bool = True,
        
        # Request configuration
        max_retries: int = 3,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        
        # Custom user agents
        custom_user_agents: Optional[List[str]] = None,
        random_user_agent_rotation: bool = True
    ):
        """
        Initialize the WebCrawler with comprehensive configuration options.
        
        Args:
            seed_url: Starting URL for crawling operations
            max_depth: Maximum crawling depth (0 = seed URL only)
            delay: Base delay between requests in seconds
            max_pages: Maximum number of pages to crawl
            same_domain_only: Restrict crawling to the same domain
            respect_robots_txt: Honor robots.txt rules and crawl delays
            user_agent: Default user agent string (used when rotation disabled)
            
            enable_anti_detection: Enable all anti-detection features automatically
            enable_user_agent_rotation: Rotate through different user agent strings
            enable_proxy_rotation: Rotate through proxy servers (requires proxy_list)
            enable_header_randomization: Randomize HTTP headers for each request
            delay_strategy: Strategy for request delays ("fixed", "random", "exponential", "adaptive")
            min_delay: Minimum delay between requests (for random/adaptive strategies)
            max_delay: Maximum delay between requests (for random/adaptive strategies)
            session_rotation_interval: Number of requests before creating new session
            
            proxy_list: List of proxy dictionaries in requests format
            validate_proxies: Test proxy functionality during initialization
            
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
            verify_ssl: Enable SSL certificate verification
            
            custom_user_agents: Custom list of user agent strings for rotation
            random_user_agent_rotation: Use random vs sequential user agent selection
            
        Raises:
            ConfigurationError: If configuration parameters are invalid
            
        Note:
            When enable_anti_detection=True, it automatically enables user agent rotation,
            header randomization, and adaptive delays. Proxy rotation requires explicit
            proxy_list configuration.
        """
        # Store basic configuration
        self.seed_url = seed_url
        self.max_depth = max_depth
        self.delay = delay
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Configure anti-detection features
        if enable_anti_detection:
            enable_user_agent_rotation = True
            enable_header_randomization = True
            delay_strategy = "adaptive" if delay_strategy == "fixed" else delay_strategy
        
        # Create anti-detection configuration
        self.anti_detection_config = AntiDetectionConfig(
            enable_user_agent_rotation=enable_user_agent_rotation,
            enable_proxy_rotation=enable_proxy_rotation and bool(proxy_list),
            enable_header_randomization=enable_header_randomization,
            enable_adaptive_delays=(delay_strategy == "adaptive"),
            min_delay=min_delay,
            max_delay=max_delay,
            delay_strategy=delay_strategy,
            session_rotation_interval=session_rotation_interval,
            max_retries=max_retries,
            timeout=timeout,
            verify_ssl=verify_ssl
        )
        
        # Validate configuration before proceeding
        self._validate_config()
        
        # Initialize data storage
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[Dict[str, Any]] = []
        self.url_queue = deque([(seed_url, 0)])  # (url, depth)
        
        # Domain and URL management
        self.base_domain = urlparse(seed_url).netloc
        allowed_domains = {self.base_domain} if same_domain_only else None
        self.url_validator = URLValidator(allowed_domains)
        self.link_extractor = LinkExtractor(self.url_validator)
        
        # Anti-detection components
        self._setup_anti_detection_components(
            proxy_list, validate_proxies, custom_user_agents, random_user_agent_rotation
        )
        
        # Robots.txt cache and session management
        self.robots_cache: Dict[str, Optional[RobotsTxtParser]] = {}
        self._request_count = 0
        self._session_id = 0
        
        # Initialize logging
        self._setup_logging()
        
        # Log configuration summary
        self.logger.info(f"WebCrawler initialized with anti-detection: {enable_anti_detection}")
        self.logger.info(f"Features enabled: UA rotation={enable_user_agent_rotation}, "
                        f"Proxy rotation={self.anti_detection_config.enable_proxy_rotation}, "
                        f"Header randomization={enable_header_randomization}")
    
    def _setup_anti_detection_components(
        self, 
        proxy_list: Optional[List[Dict[str, str]]], 
        validate_proxies: bool,
        custom_user_agents: Optional[List[str]],
        random_rotation: bool
    ) -> None:
        """
        Initialize anti-detection components based on configuration.
        
        Args:
            proxy_list: List of proxy configurations
            validate_proxies: Whether to validate proxies during setup
            custom_user_agents: Custom user agent list
            random_rotation: Use random user agent rotation
        """
        # Initialize user agent rotator
        if self.anti_detection_config.enable_user_agent_rotation:
            self.user_agent_rotator = UserAgentRotator(
                user_agents=custom_user_agents,
                random_rotation=random_rotation
            )
        else:
            self.user_agent_rotator = None
        
        # Initialize proxy rotator
        if self.anti_detection_config.enable_proxy_rotation and proxy_list:
            self.proxy_rotator = ProxyRotator(
                proxies=proxy_list,
                validate_on_init=validate_proxies,
                timeout=self.timeout
            )
            self.logger.info(f"Proxy rotator initialized with {len(proxy_list)} proxies")
        else:
            self.proxy_rotator = None
        
        # Initialize delay manager
        self.delay_manager = DelayManager(
            base_delay=self.delay,
            strategy=self.anti_detection_config.delay_strategy
        )
        
        # Initialize session manager
        self.session_manager = SessionManager(
            max_retries=self.anti_detection_config.max_retries,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 524]
        )
    
    def _setup_logging(self) -> None:
        """Configure logging for the crawler with appropriate formatting."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _validate_config(self):
        """Validate crawler configuration."""
        if not self.seed_url:
            raise ConfigurationError("Seed URL cannot be empty")
        
        if self.max_depth < 0:
            raise ConfigurationError("Max depth cannot be negative")
        
        if self.delay < 0:
            raise ConfigurationError("Delay cannot be negative")
        
        if self.max_pages <= 0:
            raise ConfigurationError("Max pages must be positive")
        
        # Basic URL validation - don't use url_validator yet as it's not created
        if not (self.seed_url.startswith('http://') or self.seed_url.startswith('https://')):
            raise ConfigurationError(f"Invalid seed URL scheme: {self.seed_url}")
    
    def _get_robots_txt(self, domain: str) -> Optional[RobotsTxtParser]:
        """
        Get robots.txt parser for a domain.
        
        Args:
            domain: Domain to get robots.txt for
            
        Returns:
            RobotsTxtParser instance or None if not available
        """
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        try:
            robots_url = f"https://{domain}/robots.txt"
            response = self.session.get(robots_url, timeout=5)
            
            if response.status_code == 200:
                parser = RobotsTxtParser(response.text, self.user_agent)
                self.robots_cache[domain] = parser
                return parser
                
        except Exception as e:
            self.logger.debug(f"Could not fetch robots.txt for {domain}: {e}")
        
        # Cache empty result to avoid repeated requests
        self.robots_cache[domain] = None
        return None
    
    def _can_crawl_url(self, url: str) -> bool:
        """
        Check if URL can be crawled according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if crawling is allowed, False otherwise
        """
        if not self.respect_robots_txt:
            return True
        
        parsed = urlparse(url)
        robots_parser = self._get_robots_txt(parsed.netloc)
        
        if robots_parser:
            return robots_parser.can_crawl(parsed.path)
        
        return True
    
    def _get_current_session(self) -> requests.Session:
        """
        Get the current session, rotating if necessary.
        
        Returns:
            Current requests session with appropriate configuration.
        """
        # Rotate session if interval reached
        if (self._request_count > 0 and 
            self._request_count % self.anti_detection_config.session_rotation_interval == 0):
            
            self.session_manager.close_session(f"session_{self._session_id}")
            self._session_id += 1
            self.logger.debug(f"Rotated to new session: session_{self._session_id}")
        
        session = self.session_manager.get_session(f"session_{self._session_id}")
        
        # Update session configuration
        session.verify = self.anti_detection_config.verify_ssl
        session.timeout = self.anti_detection_config.timeout
        
        # Set user agent
        if self.user_agent_rotator:
            current_ua = self.user_agent_rotator.get_next()
            session.headers['User-Agent'] = current_ua
        else:
            session.headers['User-Agent'] = self.user_agent
        
        # Add randomized headers if enabled
        if self.anti_detection_config.enable_header_randomization:
            random_headers = generate_random_headers()
            session.headers.update(random_headers)
        
        return session
    
    def _get_current_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get the current proxy configuration.
        
        Returns:
            Proxy dictionary or None if proxy rotation disabled.
        """
        if self.proxy_rotator and self.anti_detection_config.enable_proxy_rotation:
            return self.proxy_rotator.get_next()
        return None
    
    def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single page with comprehensive anti-detection measures.
        
        This method implements the core page crawling logic with support for:
        - User agent rotation
        - Proxy rotation with failover
        - HTTP header randomization
        - Adaptive delay management
        - Comprehensive error handling
        - Response time monitoring
        
        Args:
            url: The URL to crawl
            
        Returns:
            Dictionary containing comprehensive page data:
            {
                'url': str,
                'title': str,
                'meta_description': str,
                'links': List[str],
                'status_code': Optional[int],
                'error': Optional[str],
                'timestamp': float,
                'content_type': Optional[str],
                'content_length': Optional[int],
                'response_time': Optional[float],
                'user_agent_used': str,
                'proxy_used': Optional[str],
                'retry_count': int
            }
        """
        start_time = time.time()
        page_data = {
            'url': url,
            'title': '',
            'meta_description': '',
            'links': [],
            'status_code': None,
            'error': None,
            'timestamp': start_time,
            'content_type': None,
            'content_length': None,
            'response_time': None,
            'user_agent_used': '',
            'proxy_used': None,
            'retry_count': 0
        }
        
        session = None
        current_proxy = None
        
        try:
            self.logger.info(f"Crawling: {url}")
            
            # Check robots.txt compliance
            if not self._can_crawl_url(url):
                page_data['error'] = "Blocked by robots.txt"
                return page_data
            
            # Get configured session and proxy
            session = self._get_current_session()
            current_proxy = self._get_current_proxy()
            page_data['user_agent_used'] = session.headers.get('User-Agent', '')
            page_data['proxy_used'] = str(current_proxy) if current_proxy else None
            
            # Make request with retry logic
            response = None
            max_proxy_retries = 3 if current_proxy else 1
            
            for proxy_retry in range(max_proxy_retries):
                try:
                    request_start = time.time()
                    response = session.get(
                        url,
                        proxies=current_proxy,
                        timeout=self.anti_detection_config.timeout,
                        verify=self.anti_detection_config.verify_ssl
                    )
                    page_data['response_time'] = time.time() - request_start
                    break
                    
                except (requests.exceptions.ProxyError, 
                        requests.exceptions.ConnectTimeout,
                        requests.exceptions.ConnectionError) as e:
                    
                    if current_proxy and self.proxy_rotator:
                        self.logger.warning(f"Proxy failed for {url}: {e}")
                        self.proxy_rotator.mark_failed(current_proxy)
                        current_proxy = self.proxy_rotator.get_next()
                        page_data['retry_count'] += 1
                        
                        if current_proxy is None:
                            page_data['error'] = "All proxies failed"
                            return page_data
                    else:
                        raise
            
            if response is None:
                page_data['error'] = "Failed to get response after retries"
                return page_data
            
            # Process successful response
            page_data['status_code'] = response.status_code
            page_data['content_type'] = response.headers.get('content-type', '')
            page_data['content_length'] = len(response.content)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    # Extract page information
                    page_data['title'] = self.link_extractor.extract_title(response.text)
                    page_data['meta_description'] = self.link_extractor.extract_meta_description(response.text)
                    page_data['links'] = self.link_extractor.extract_links(response.text, url)
                    
                    self.logger.debug(f"Extracted {len(page_data['links'])} links from {url}")
                else:
                    page_data['error'] = f"Non-HTML content: {content_type}"
            else:
                page_data['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            page_data['error'] = "Request timeout"
            self.logger.warning(f"Timeout crawling {url}")
            
        except requests.exceptions.ConnectionError as e:
            page_data['error'] = f"Connection error: {str(e)[:100]}"
            self.logger.warning(f"Connection error crawling {url}: {e}")
            
        except requests.exceptions.RequestException as e:
            page_data['error'] = f"Request error: {str(e)[:100]}"
            self.logger.warning(f"Request error crawling {url}: {e}")
            
        except Exception as e:
            page_data['error'] = f"Unexpected error: {str(e)[:100]}"
            self.logger.error(f"Unexpected error crawling {url}: {e}")
        
        finally:
            # Update request count
            self._request_count += 1
            
            # Apply delay management
            if page_data['response_time']:
                self.delay_manager.wait(page_data['response_time'])
            else:
                self.delay_manager.wait()
            
        return page_data
    
    def crawl(self) -> List[Dict[str, Any]]:
        """
        Execute the complete crawling process with anti-detection features.
        
        This method orchestrates the entire crawling operation, implementing:
        - Intelligent queue management
        - Session rotation and proxy failover
        - Adaptive delay strategies
        - Comprehensive error recovery
        - Real-time monitoring and logging
        
        Returns:
            List of dictionaries containing detailed crawling results for each page.
            Each dictionary includes page content, metadata, timing information,
            and anti-detection details.
            
        Raises:
            CrawlerError: If critical crawling failures occur
            
        Note:
            The method automatically handles proxy failures, rate limiting responses,
            and other common crawling obstacles. Progress is logged in real-time,
            and partial results are preserved even if crawling is interrupted.
        """
        self.logger.info(f"Starting advanced crawl from: {self.seed_url}")
        self.logger.info(f"Configuration: depth={self.max_depth}, pages={self.max_pages}")
        self.logger.info(f"Anti-detection: UA rotation={bool(self.user_agent_rotator)}, "
                        f"Proxy rotation={bool(self.proxy_rotator)}, "
                        f"Strategy={self.anti_detection_config.delay_strategy}")
        
        if self.proxy_rotator:
            self.logger.info(f"Proxy pool: {len(self.proxy_rotator.proxies)} proxies available")
        
        pages_crawled = 0
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        try:
            while self.url_queue and pages_crawled < self.max_pages:
                current_url, depth = self.url_queue.popleft()
                
                # Skip already visited URLs
                if current_url in self.visited_urls:
                    continue
                
                # Skip if depth limit exceeded
                if depth > self.max_depth:
                    continue
                
                # Mark URL as visited
                self.visited_urls.add(current_url)
                
                # Crawl the page with anti-detection measures
                page_data = self.crawl_page(current_url)
                self.crawled_data.append(page_data)
                pages_crawled += 1
                
                # Handle crawling results
                if page_data['error']:
                    consecutive_failures += 1
                    self.logger.warning(f"Failed to crawl {current_url}: {page_data['error']}")
                    
                    # Check for too many consecutive failures
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error(f"Too many consecutive failures ({consecutive_failures}), "
                                        f"aborting crawl")
                        break
                else:
                    consecutive_failures = 0  # Reset failure counter
                    
                    # Add discovered links to queue if not at max depth
                    if depth < self.max_depth and page_data['links']:
                        new_links_added = 0
                        for link in page_data['links']:
                            if link not in self.visited_urls:
                                self.url_queue.append((link, depth + 1))
                                new_links_added += 1
                        
                        self.logger.debug(f"Added {new_links_added} new URLs to queue from {current_url}")
                
                # Log progress periodically
                if pages_crawled % 10 == 0:
                    self.logger.info(f"Progress: {pages_crawled}/{self.max_pages} pages crawled, "
                                   f"{len(self.url_queue)} URLs in queue")
                
                # Handle rate limiting responses
                if page_data.get('status_code') == 429:
                    self.logger.warning("Rate limiting detected, increasing delays")
                    self.delay_manager.base_delay *= 1.5
                
        except KeyboardInterrupt:
            self.logger.info("Crawling interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error during crawling: {e}")
            raise CrawlerError(f"Crawling failed: {e}")
        finally:
            # Cleanup sessions
            self.session_manager.close_all_sessions()
        
        # Log final statistics
        successful_pages = len([p for p in self.crawled_data if not p['error']])
        self.logger.info(f"Crawling completed: {pages_crawled} pages crawled, "
                        f"{successful_pages} successful, "
                        f"{pages_crawled - successful_pages} failed")
        
        return self.crawled_data
    
    def get_anti_detection_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics about anti-detection feature usage.
        
        Returns:
            Dictionary containing comprehensive anti-detection statistics including
            user agent usage, proxy performance, delay patterns, and success rates.
        """
        stats = {
            'total_requests': self._request_count,
            'session_rotations': self._session_id,
            'anti_detection_config': self.anti_detection_config.to_dict(),
        }
        
        # User agent statistics
        if self.user_agent_rotator:
            stats['user_agents'] = {
                'total_available': len(self.user_agent_rotator.user_agents),
                'rotation_strategy': 'random' if self.user_agent_rotator.random_rotation else 'sequential'
            }
        
        # Proxy statistics
        if self.proxy_rotator:
            stats['proxy_stats'] = {
                'total_proxies': len(self.proxy_rotator.proxies),
                'failed_proxies': len(self.proxy_rotator._failed_proxies),
                'success_rate': (len(self.proxy_rotator.proxies) - len(self.proxy_rotator._failed_proxies)) / len(self.proxy_rotator.proxies) if self.proxy_rotator.proxies else 0
            }
        
        # Response time statistics
        response_times = [p.get('response_time') for p in self.crawled_data if p.get('response_time')]
        if response_times:
            stats['response_times'] = {
                'average': sum(response_times) / len(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'total_samples': len(response_times)
            }
        
        return stats
    
    def add_proxy(self, proxy: Dict[str, str], validate: bool = True) -> bool:
        """
        Add a new proxy to the rotation pool during crawling.
        
        Args:
            proxy: Proxy configuration dictionary
            validate: Whether to validate proxy before adding
            
        Returns:
            True if successfully added, False otherwise
        """
        if not self.proxy_rotator:
            self.logger.warning("Proxy rotation not enabled, cannot add proxy")
            return False
        
        success = self.proxy_rotator.add_proxy(proxy, validate)
        if success:
            self.logger.info(f"Added new proxy to rotation pool")
        else:
            self.logger.warning(f"Failed to add proxy to rotation pool")
        
        return success
    
    def update_delay_strategy(self, strategy: str, base_delay: Optional[float] = None) -> None:
        """
        Update the delay strategy during crawling.
        
        Args:
            strategy: New delay strategy ("fixed", "random", "exponential", "adaptive")
            base_delay: New base delay value
        """
        if strategy not in ["fixed", "random", "exponential", "adaptive"]:
            raise ValueError(f"Invalid delay strategy: {strategy}")
        
        self.delay_manager.strategy = strategy
        if base_delay is not None:
            self.delay_manager.base_delay = base_delay
        
        self.logger.info(f"Updated delay strategy to: {strategy}")
    
    def get_proxy_health(self) -> Dict[str, Any]:
        """
        Get current proxy pool health status.
        
        Returns:
            Dictionary with proxy pool health information
        """
        if not self.proxy_rotator:
            return {'proxy_rotation_enabled': False}
        
        total_proxies = len(self.proxy_rotator.proxies)
        failed_proxies = len(self.proxy_rotator._failed_proxies)
        
        return {
            'proxy_rotation_enabled': True,
            'total_proxies': total_proxies,
            'healthy_proxies': total_proxies - failed_proxies,
            'failed_proxies': failed_proxies,
            'health_percentage': ((total_proxies - failed_proxies) / total_proxies * 100) if total_proxies > 0 else 0
        }
    
    def save_results(self, filename: str = 'crawl_results.json', indent: int = 2):
        """
        Save crawled data to JSON file.
        
        Args:
            filename: Output filename
            indent: JSON indentation level
        """
        try:
            # Securely resolve the output path to prevent directory traversal and absolute path usage.
            base_dir = os.getcwd()
            # Optionally, output to a subdirectory: e.g. base_dir = os.path.join(base_dir, 'results')
            full_path = os.path.abspath(os.path.normpath(os.path.join(base_dir, filename)))
            if not full_path.startswith(base_dir):
                raise CrawlerError(f"Invalid output filename: {filename} (path traversal is not allowed)")
            # Optionally, check file extension (uncomment if you want this extra restriction)
            # if not full_path.lower().endswith('.json'):
            #     raise CrawlerError("Output filename must end with .json")
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(self.crawled_data, f, indent=indent, ensure_ascii=False)
            self.logger.info(f"Results saved to {full_path}")
        except Exception as e:
            raise CrawlerError(f"Failed to save results: {e}")
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the crawling results.
        
        Returns:
            Dictionary containing crawl statistics
        """
        total_pages = len(self.crawled_data)
        successful_pages = len([p for p in self.crawled_data if not p['error']])
        total_links = sum(len(p['links']) for p in self.crawled_data)
        
        domains_found = set()
        for page in self.crawled_data:
            if not page['error']:
                domains_found.add(urlparse(page['url']).netloc)
        
        return {
            'total_pages_crawled': total_pages,
            'successful_pages': successful_pages,
            'failed_pages': total_pages - successful_pages,
            'total_links_found': total_links,
            'unique_urls_discovered': len(self.visited_urls),
            'domains_found': len(domains_found),
            'max_depth_reached': max((0,) + tuple(
                len([p for p in self.crawled_data if not p['error']]) - 1 
                for p in self.crawled_data if not p['error']
            ))
        }
    
    def print_summary(self):
        """Print a summary of the crawling results."""
        summary = self.get_summary()
        
        print(f"\\n=== Crawl Summary ===")
        print(f"Total pages crawled: {summary['total_pages_crawled']}")
        print(f"Successful pages: {summary['successful_pages']}")
        print(f"Failed pages: {summary['failed_pages']}")
        print(f"Total links found: {summary['total_links_found']}")
        print(f"Unique URLs discovered: {summary['unique_urls_discovered']}")
        print(f"Domains found: {summary['domains_found']}")
    
    def get_failed_urls(self) -> List[Dict]:
        """
        Get list of URLs that failed to crawl.
        
        Returns:
            List of failed page data
        """
        return [page for page in self.crawled_data if page['error']]
    
    def get_successful_urls(self) -> List[Dict]:
        """
        Get list of URLs that were successfully crawled.
        
        Returns:
            List of successful page data
        """
        return [page for page in self.crawled_data if not page['error']]