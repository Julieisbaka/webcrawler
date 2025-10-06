"""
Command-line interface for the webcrawler package with anti-detection features.

This module provides a comprehensive command-line interface for the WebCrawler
with support for all anti-detection features including proxy rotation, user agent
rotation, header randomization, and adaptive delay strategies.
"""

import argparse
import logging
import sys
import os
from typing import Optional, List, Dict

from .crawler import WebCrawler
from .exceptions import CrawlerError, ConfigurationError


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser for CLI with anti-detection options."""
    parser = argparse.ArgumentParser(
        description='WebCrawler - Recursively crawl websites with anti-detection features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic crawling:
    %(prog)s https://example.com
    %(prog)s https://example.com --max-depth 3 --max-pages 100
  
  Anti-detection features:
    %(prog)s https://example.com --anti-detection
    %(prog)s https://example.com --user-agent-rotation --delay-strategy adaptive
    %(prog)s https://example.com --header-randomization --min-delay 2 --max-delay 8
  
  Proxy usage:
    %(prog)s https://example.com --proxy-file proxies.txt --proxy-rotation
    %(prog)s https://example.com --session-rotation 25 --max-retries 5
  
  Advanced configuration:
    %(prog)s https://example.com --anti-detection --cross-domain --timeout 45
        """
    )
    
    # Required arguments
    parser.add_argument(
        'url',
        help='Seed URL to start crawling from'
    )
    
    # Basic crawling options
    basic_group = parser.add_argument_group('Basic Options')
    basic_group.add_argument(
        '--max-depth', '-d',
        type=int,
        default=3,
        help='Maximum crawling depth (default: 3)'
    )
    
    basic_group.add_argument(
        '--max-pages', '-p',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    
    basic_group.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Base delay between requests in seconds (default: 1.0)'
    )
    
    basic_group.add_argument(
        '--cross-domain',
        action='store_true',
        help='Allow crawling across different domains'
    )
    
    basic_group.add_argument(
        '--ignore-robots',
        action='store_true',
        help='Ignore robots.txt rules'
    )
    
    basic_group.add_argument(
        '--timeout',
        type=float,
        default=30.0,
        help='Request timeout in seconds (default: 30.0)'
    )
    
    # Anti-detection features
    antidet_group = parser.add_argument_group('Anti-Detection Features')
    antidet_group.add_argument(
        '--anti-detection',
        action='store_true',
        help='Enable all anti-detection features automatically'
    )
    
    antidet_group.add_argument(
        '--user-agent-rotation',
        action='store_true',
        help='Rotate through different user agent strings'
    )
    
    antidet_group.add_argument(
        '--header-randomization',
        action='store_true',
        help='Randomize HTTP headers for each request'
    )
    
    antidet_group.add_argument(
        '--delay-strategy',
        choices=['fixed', 'random', 'exponential', 'adaptive'],
        default='fixed',
        help='Delay strategy between requests (default: fixed)'
    )
    
    antidet_group.add_argument(
        '--min-delay',
        type=float,
        default=1.0,
        help='Minimum delay for random/adaptive strategies (default: 1.0)'
    )
    
    antidet_group.add_argument(
        '--max-delay',
        type=float,
        default=5.0,
        help='Maximum delay for random/adaptive strategies (default: 5.0)'
    )
    
    antidet_group.add_argument(
        '--session-rotation',
        type=int,
        default=50,
        help='Rotate session every N requests (default: 50)'
    )
    
    # Proxy options
    proxy_group = parser.add_argument_group('Proxy Options')
    proxy_group.add_argument(
        '--proxy-rotation',
        action='store_true',
        help='Enable proxy rotation (requires --proxy-file or --proxy-list)'
    )
    
    proxy_group.add_argument(
        '--proxy-file',
        help='File containing proxy list (one per line: protocol://host:port)'
    )
    
    proxy_group.add_argument(
        '--proxy-list',
        nargs='+',
        help='List of proxies (format: protocol://host:port)'
    )
    
    proxy_group.add_argument(
        '--validate-proxies',
        action='store_true',
        default=True,
        help='Validate proxies before use (default: True)'
    )
    
    # Request options
    request_group = parser.add_argument_group('Request Options')
    request_group.add_argument(
        '--user-agent',
        default='WebCrawler/0.0.1 (Anti-Detection)',
        help='Default user agent string (default: WebCrawler/0.0.1)'
    )
    
    request_group.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed requests (default: 3)'
    )
    
    request_group.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='Disable SSL certificate verification'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output', '-o',
        default='crawl_results.json',
        help='Output file for results (default: crawl_results.json)'
    )
    
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    output_group.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed anti-detection statistics'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='WebCrawler 0.0.1 by JulieISBaka'
    )
    
    return parser


def validate_args(args) -> Optional[str]:
    """
    Validate command line arguments.
    
    Returns:
        Error message if validation fails, None otherwise
    """
    if args.max_depth < 0:
        return "Max depth cannot be negative"
    
    if args.max_pages <= 0:
        return "Max pages must be positive"
    
    if args.delay < 0:
        return "Delay cannot be negative"
    
    if not args.url.startswith(('http://', 'https://')):
        return "URL must start with http:// or https://"
    
    return None


PROXY_FILES_DIR = "proxies"

def load_proxies_from_file(filepath: str) -> List[Dict[str, str]]:
    """
    Load proxy list from file.
    
    Args:
        filepath: Path to file containing proxy URLs
        
    Returns:
        List of proxy dictionaries
    """
    proxies = []
    # Only allow filenames, not paths
    if os.path.isabs(filepath) or os.path.basename(filepath) != filepath:
        print(f"Error: Only filenames are allowed, not paths. Access to files outside directory '{PROXY_FILES_DIR}' is not allowed.")
        return []
    base_dir = os.path.abspath(PROXY_FILES_DIR)
    requested_path = os.path.abspath(os.path.join(base_dir, filepath))
    try:
        with open(requested_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse proxy URL (e.g., http://user:pass@host:port)
                    proxy_dict = {
                        'http': line,
                        'https': line
                    }
                    proxies.append(proxy_dict)
    except Exception as e:
        print(f"Error loading proxies from {requested_path}: {e}")
    
    return proxies


def parse_proxy_list(proxy_strings: List[str]) -> List[Dict[str, str]]:
    """
    Parse command line proxy list.
    
    Args:
        proxy_strings: List of proxy URL strings
        
    Returns:
        List of proxy dictionaries
    """
    proxies = []
    for proxy_str in proxy_strings:
        proxy_dict = {
            'http': proxy_str,
            'https': proxy_str
        }
        proxies.append(proxy_dict)
    
    return proxies


def main():
    """Enhanced CLI entry point with comprehensive anti-detection support."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Load proxies if specified
    proxy_list = None
    if args.proxy_file:
        proxy_list = load_proxies_from_file(args.proxy_file)
        if not proxy_list:
            print(f"Warning: No valid proxies loaded from {args.proxy_file}")
    elif args.proxy_list:
        proxy_list = parse_proxy_list(args.proxy_list)
    
    if args.proxy_rotation and not proxy_list:
        print("Error: Proxy rotation enabled but no proxies provided", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create crawler with comprehensive configuration
        crawler = WebCrawler(
            seed_url=args.url,
            max_depth=args.max_depth,
            delay=args.delay,
            max_pages=args.max_pages,
            same_domain_only=not args.cross_domain,
            respect_robots_txt=not args.ignore_robots,
            user_agent=args.user_agent,
            
            # Anti-detection features
            enable_anti_detection=args.anti_detection,
            enable_user_agent_rotation=args.user_agent_rotation or args.anti_detection,
            enable_proxy_rotation=args.proxy_rotation,
            enable_header_randomization=args.header_randomization or args.anti_detection,
            delay_strategy=args.delay_strategy,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            session_rotation_interval=args.session_rotation,
            
            # Proxy configuration
            proxy_list=proxy_list,
            validate_proxies=args.validate_proxies,
            
            # Request configuration
            max_retries=args.max_retries,
            timeout=args.timeout,
            verify_ssl=not args.no_ssl_verify
        )
        
        # Display configuration summary
        print(f"Starting advanced crawl of {args.url}")
        print(f"Configuration:")
        print(f"  Max depth: {args.max_depth}")
        print(f"  Max pages: {args.max_pages}")
        print(f"  Base delay: {args.delay}s")
        print(f"  Delay strategy: {args.delay_strategy}")
        print(f"  Cross-domain: {args.cross_domain}")
        print(f"  Respect robots.txt: {not args.ignore_robots}")
        print(f"  Timeout: {args.timeout}s")
        
        # Anti-detection summary
        print(f"\\nAnti-Detection Features:")
        print(f"  Auto anti-detection: {args.anti_detection}")
        print(f"  User agent rotation: {args.user_agent_rotation or args.anti_detection}")
        print(f"  Proxy rotation: {args.proxy_rotation}")
        print(f"  Header randomization: {args.header_randomization or args.anti_detection}")
        print(f"  Session rotation: every {args.session_rotation} requests")
        
        if proxy_list:
            print(f"  Loaded proxies: {len(proxy_list)}")
        
        print()
        
        # Start crawling
        results = crawler.crawl()
        
        # Print summary
        crawler.print_summary()
        
        # Show anti-detection statistics if requested
        if args.stats:
            print(f"\\n=== Anti-Detection Statistics ===")
            stats = crawler.get_anti_detection_stats()
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for sub_key, sub_value in value.items():
                        print(f"  {sub_key}: {sub_value}")
                else:
                    print(f"{key}: {value}")
            
            # Proxy health if available
            proxy_health = crawler.get_proxy_health()
            if proxy_health['proxy_rotation_enabled']:
                print(f"\\n=== Proxy Health ===")
                print(f"Total proxies: {proxy_health['total_proxies']}")
                print(f"Healthy proxies: {proxy_health['healthy_proxies']}")
                print(f"Failed proxies: {proxy_health['failed_proxies']}")
                print(f"Health percentage: {proxy_health['health_percentage']:.1f}%")
        
        # Save results
        crawler.save_results(args.output)
        print(f"\\nResults saved to {args.output}")
        
        # Show sample results
        successful = crawler.get_successful_urls()
        if successful:
            print(f"\\n=== Sample Results (first 5) ===")
            for i, page in enumerate(successful[:5]):
                print(f"\\n{i+1}. {page['url']}")
                print(f"   Title: {page['title'][:60]}{'...' if len(page['title']) > 60 else ''}")
                print(f"   Links found: {len(page['links'])}")
                
                # Show anti-detection info if available
                if page.get('user_agent_used'):
                    ua_short = page['user_agent_used'][:50] + "..." if len(page['user_agent_used']) > 50 else page['user_agent_used']
                    print(f"   User agent: {ua_short}")
                
                if page.get('proxy_used') and page['proxy_used'] != 'None':
                    print(f"   Proxy used: {page['proxy_used']}")
                
                if page.get('response_time'):
                    print(f"   Response time: {page['response_time']:.2f}s")
                
                if page.get('retry_count', 0) > 0:
                    print(f"   Retries: {page['retry_count']}")
        
        # Show failed URLs if any
        failed = crawler.get_failed_urls()
        if failed:
            print(f"\\n=== Failed URLs (first 10) ===")
            for page in failed[:10]:
                print(f"{page['url']} - {page['error']}")
            if len(failed) > 10:
                print(f"... and {len(failed) - 10} more")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except CrawlerError as e:
        print(f"Crawler error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\nCrawling interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()