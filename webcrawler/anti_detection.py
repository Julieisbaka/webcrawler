"""
Anti-detection and rate limit bypass utilities for web crawling.

This module provides various techniques to avoid detection and circumvent
basic rate limiting measures while being respectful to websites.
"""

import random
import time
import threading
from typing import List, Dict, Optional, Callable, Any
import itertools
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class UserAgentRotator:
    """
    Rotates through a list of user agent strings to avoid detection.
    
    This class manages a collection of realistic user agent strings and
    provides methods to rotate through them systematically or randomly.
    """
    
    def __init__(self, user_agents: Optional[List[str]] = None, random_rotation: bool = True):
        """
        Initialize the user agent rotator.
        
        Args:
            user_agents: List of user agent strings. If None, uses default list.
            random_rotation: If True, selects user agents randomly. If False, rotates sequentially.
        """
        self.user_agents = user_agents or self._get_default_user_agents()
        self.random_rotation = random_rotation
        self._iterator = itertools.cycle(self.user_agents)
        self._lock = threading.Lock()
    
    def _get_default_user_agents(self) -> List[str]:
        """
        Get a comprehensive list of realistic user agent strings.
        
        Returns:
            List of user agent strings representing various browsers and platforms.
        """
        return [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0',
            
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            
            # Firefox on Linux
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0',
            
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47',
            
            # Mobile user agents
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/118.0 Firefox/118.0',
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        ]
    
    def get_next(self) -> str:
        """
        Get the next user agent string.
        
        Returns:
            A user agent string based on the rotation strategy.
        """
        with self._lock:
            if self.random_rotation:
                return random.choice(self.user_agents)
            else:
                return next(self._iterator)
    
    def add_user_agent(self, user_agent: str) -> None:
        """
        Add a new user agent to the rotation list.
        
        Args:
            user_agent: User agent string to add.
        """
        with self._lock:
            if user_agent not in self.user_agents:
                self.user_agents.append(user_agent)
    
    def remove_user_agent(self, user_agent: str) -> bool:
        """
        Remove a user agent from the rotation list.
        
        Args:
            user_agent: User agent string to remove.
            
        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            try:
                self.user_agents.remove(user_agent)
                return True
            except ValueError:
                return False


class ProxyRotator:
    """
    Manages proxy rotation to distribute requests across multiple IP addresses.
    
    This class handles proxy validation, rotation, and automatic removal of
    non-functional proxies to maintain a healthy proxy pool.
    """
    
    def __init__(self, proxies: Optional[List[Dict[str, str]]] = None, 
                 validate_on_init: bool = True, timeout: float = 10.0):
        """
        Initialize the proxy rotator.
        
        Args:
            proxies: List of proxy dictionaries in requests format.
                    Example: [{'http': 'http://proxy1:8080', 'https': 'https://proxy1:8080'}]
            validate_on_init: Whether to validate proxies during initialization.
            timeout: Timeout for proxy validation requests.
        """
        self.proxies = proxies or []
        self.timeout = timeout
        self._iterator = itertools.cycle(self.proxies) if self.proxies else None
        self._lock = threading.Lock()
        self._failed_proxies = set()
        
        if validate_on_init and self.proxies:
            self._validate_proxies()
    
    def _validate_proxies(self) -> None:
        """
        Validate all proxies by making test requests.
        
        Removes non-functional proxies from the rotation list.
        """
        valid_proxies = []
        test_url = "http://httpbin.org/ip"
        
        for proxy in self.proxies:
            try:
                response = requests.get(test_url, proxies=proxy, timeout=self.timeout)
                if response.status_code == 200:
                    valid_proxies.append(proxy)
            except Exception:
                # Proxy failed validation
                pass
        
        self.proxies = valid_proxies
        self._iterator = itertools.cycle(self.proxies) if self.proxies else None
    
    def get_next(self) -> Optional[Dict[str, str]]:
        """
        Get the next proxy in the rotation.
        
        Returns:
            Proxy dictionary or None if no proxies available.
        """
        with self._lock:
            if not self.proxies or not self._iterator:
                return None
            
            # Try to get a working proxy
            attempts = 0
            max_attempts = len(self.proxies)
            
            while attempts < max_attempts:
                proxy = next(self._iterator)
                proxy_key = str(proxy)
                
                if proxy_key not in self._failed_proxies:
                    return proxy
                
                attempts += 1
            
            # All proxies failed, reset failed list and try again
            self._failed_proxies.clear()
            return next(self._iterator) if self._iterator else None
    
    def mark_failed(self, proxy: Dict[str, str]) -> None:
        """
        Mark a proxy as failed to temporarily exclude it from rotation.
        
        Args:
            proxy: The proxy dictionary that failed.
        """
        with self._lock:
            self._failed_proxies.add(str(proxy))
    
    def add_proxy(self, proxy: Dict[str, str], validate: bool = True) -> bool:
        """
        Add a new proxy to the rotation.
        
        Args:
            proxy: Proxy dictionary to add.
            validate: Whether to validate the proxy before adding.
            
        Returns:
            True if added successfully, False otherwise.
        """
        if validate:
            try:
                test_url = "http://httpbin.org/ip"
                response = requests.get(test_url, proxies=proxy, timeout=self.timeout)
                if response.status_code != 200:
                    return False
            except Exception:
                return False
        
        with self._lock:
            if proxy not in self.proxies:
                self.proxies.append(proxy)
                self._iterator = itertools.cycle(self.proxies)
                return True
        return False
    
    def has_proxies(self) -> bool:
        """
        Check if there are any available proxies.
        
        Returns:
            True if proxies are available, False otherwise.
        """
        return len(self.proxies) > 0


class DelayManager:
    """
    Manages request delays with various strategies to avoid rate limiting.
    
    This class implements multiple delay strategies including fixed delays,
    random delays, exponential backoff, and adaptive delays based on response times.
    """
    
    def __init__(self, base_delay: float = 1.0, strategy: str = "random"):
        """
        Initialize the delay manager.
        
        Args:
            base_delay: Base delay in seconds.
            strategy: Delay strategy ("fixed", "random", "exponential", "adaptive").
        """
        self.base_delay = base_delay
        self.strategy = strategy
        self._request_count = 0
        self._response_times = []
        self._last_request_time = 0
        self._lock = threading.Lock()
    
    def wait(self, response_time: Optional[float] = None) -> None:
        """
        Wait according to the configured delay strategy.
        
        Args:
            response_time: Response time of the last request for adaptive strategy.
        """
        with self._lock:
            current_time = time.time()
            
            if self.strategy == "fixed":
                delay = self.base_delay
            elif self.strategy == "random":
                delay = random.uniform(self.base_delay * 0.5, self.base_delay * 1.5)
            elif self.strategy == "exponential":
                delay = self.base_delay * (1.5 ** min(self._request_count // 10, 5))
            elif self.strategy == "adaptive":
                delay = self._calculate_adaptive_delay(response_time)
            else:
                delay = self.base_delay
            
            # Ensure minimum time has passed since last request
            time_since_last = current_time - self._last_request_time
            actual_delay = max(0, delay - time_since_last)
            
            if actual_delay > 0:
                time.sleep(actual_delay)
            
            self._last_request_time = time.time()
            self._request_count += 1
    
    def _calculate_adaptive_delay(self, response_time: Optional[float]) -> float:
        """
        Calculate delay based on response times to adapt to server performance.
        
        Args:
            response_time: Response time of the last request.
            
        Returns:
            Calculated delay in seconds.
        """
        if response_time is not None:
            self._response_times.append(response_time)
            # Keep only last 10 response times
            if len(self._response_times) > 10:
                self._response_times.pop(0)
        
        if not self._response_times:
            return self.base_delay
        
        avg_response_time = sum(self._response_times) / len(self._response_times)
        
        # Adjust delay based on average response time
        if avg_response_time > 3.0:  # Slow server
            return self.base_delay * 2.0
        elif avg_response_time > 1.0:  # Moderate server
            return self.base_delay * 1.5
        else:  # Fast server
            return self.base_delay
    
    def reset(self) -> None:
        """Reset the delay manager state."""
        with self._lock:
            self._request_count = 0
            self._response_times.clear()
            self._last_request_time = 0


class SessionManager:
    """
    Manages HTTP sessions with anti-detection features.
    
    This class creates and manages requests sessions with various anti-detection
    features including retry logic, connection pooling, and header manipulation.
    """
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.3,
                 status_forcelist: Optional[List[int]] = None):
        """
        Initialize the session manager.
        
        Args:
            max_retries: Maximum number of retries for failed requests.
            backoff_factor: Backoff factor for retry delays.
            status_forcelist: HTTP status codes to retry on.
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [429, 500, 502, 503, 504]
        self._sessions = {}
        self._lock = threading.Lock()
    
    def get_session(self, session_id: str = "default") -> requests.Session:
        """
        Get or create a configured session.
        
        Args:
            session_id: Identifier for the session.
            
        Returns:
            Configured requests session.
        """
        with self._lock:
            if session_id not in self._sessions:
                session = requests.Session()
                
                # Configure retry strategy
                retry_strategy = Retry(
                    total=self.max_retries,
                    backoff_factor=self.backoff_factor,
                    status_forcelist=self.status_forcelist,
                    allowed_methods=["HEAD", "GET", "OPTIONS"]
                )
                
                adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=10)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                # Set default headers
                session.headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                self._sessions[session_id] = session
            
            return self._sessions[session_id]
    
    def close_session(self, session_id: str) -> None:
        """
        Close and remove a session.
        
        Args:
            session_id: Identifier of the session to close.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].close()
                del self._sessions[session_id]
    
    def close_all_sessions(self) -> None:
        """Close all managed sessions."""
        with self._lock:
            for session in self._sessions.values():
                session.close()
            self._sessions.clear()


class AntiDetectionConfig:
    """
    Configuration class for anti-detection features.
    
    This class centralizes all anti-detection configuration options and provides
    validation and default values for various anti-detection strategies.
    """
    
    def __init__(self, 
                 enable_user_agent_rotation: bool = True,
                 enable_proxy_rotation: bool = False,
                 enable_header_randomization: bool = True,
                 enable_adaptive_delays: bool = True,
                 min_delay: float = 1.0,
                 max_delay: float = 5.0,
                 delay_strategy: str = "random",
                 session_rotation_interval: int = 50,
                 max_retries: int = 3,
                 timeout: float = 30.0,
                 verify_ssl: bool = True):
        """
        Initialize anti-detection configuration.
        
        Args:
            enable_user_agent_rotation: Enable user agent string rotation.
            enable_proxy_rotation: Enable proxy rotation (requires proxy list).
            enable_header_randomization: Enable HTTP header randomization.
            enable_adaptive_delays: Enable adaptive delay calculation.
            min_delay: Minimum delay between requests in seconds.
            max_delay: Maximum delay between requests in seconds.
            delay_strategy: Delay strategy ("fixed", "random", "exponential", "adaptive").
            session_rotation_interval: Number of requests before rotating session.
            max_retries: Maximum number of retries for failed requests.
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.enable_user_agent_rotation = enable_user_agent_rotation
        self.enable_proxy_rotation = enable_proxy_rotation
        self.enable_header_randomization = enable_header_randomization
        self.enable_adaptive_delays = enable_adaptive_delays
        self.min_delay = max(0, min_delay)
        self.max_delay = max(self.min_delay, max_delay)
        self.delay_strategy = delay_strategy
        self.session_rotation_interval = max(1, session_rotation_interval)
        self.max_retries = max(0, max_retries)
        self.timeout = max(1, timeout)
        self.verify_ssl = verify_ssl
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        valid_strategies = ["fixed", "random", "exponential", "adaptive"]
        if self.delay_strategy not in valid_strategies:
            raise ValueError(f"Invalid delay strategy. Must be one of: {valid_strategies}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return {
            'enable_user_agent_rotation': self.enable_user_agent_rotation,
            'enable_proxy_rotation': self.enable_proxy_rotation,
            'enable_header_randomization': self.enable_header_randomization,
            'enable_adaptive_delays': self.enable_adaptive_delays,
            'min_delay': self.min_delay,
            'max_delay': self.max_delay,
            'delay_strategy': self.delay_strategy,
            'session_rotation_interval': self.session_rotation_interval,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AntiDetectionConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration parameters.
            
        Returns:
            AntiDetectionConfig instance.
        """
        return cls(**config_dict)


def generate_random_headers() -> Dict[str, str]:
    """
    Generate randomized HTTP headers to appear more like a real browser.
    
    Returns:
        Dictionary of randomized HTTP headers.
    """
    headers = {
        'Accept': random.choice([
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ]),
        'Accept-Language': random.choice([
            'en-US,en;q=0.9',
            'en-US,en;q=0.8',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.5'
        ]),
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': random.choice(['1', '0']),
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Randomly add some optional headers
    if random.random() < 0.3:
        headers['Cache-Control'] = 'max-age=0'
    
    if random.random() < 0.2:
        headers['Sec-Fetch-Dest'] = random.choice(['document', 'empty'])
        headers['Sec-Fetch-Mode'] = random.choice(['navigate', 'cors'])
        headers['Sec-Fetch-Site'] = random.choice(['none', 'same-origin'])
    
    return headers