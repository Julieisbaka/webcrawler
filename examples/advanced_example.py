"""
Advanced example showing various webcrawler features.
"""

from webcrawler import WebCrawler
import json

def advanced_example():
    """Advanced crawling example with custom configuration."""
    print("=== Advanced Crawling Example ===")
    
    # Create crawler with advanced settings
    crawler = WebCrawler(
        seed_url="https://quotes.toscrape.com",  # Good test site
        max_depth=3,
        delay=1.0,
        max_pages=25,
        same_domain_only=True,
        respect_robots_txt=True,
        user_agent="AdvancedCrawler/1.0"
    )
    
    print(f"Starting crawl of {crawler.seed_url}")
    print(f"Configuration: depth={crawler.max_depth}, pages={crawler.max_pages}")
    
    # Start crawling
    results = crawler.crawl()
    
    # Get detailed summary
    summary = crawler.get_summary()
    print(f"\\nCrawl Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Save results with pretty formatting
    crawler.save_results('advanced_example_results.json', indent=4)
    
    # Analyze results
    successful = crawler.get_successful_urls()
    failed = crawler.get_failed_urls()
    
    print(f"\\nSuccessful pages: {len(successful)}")
    print(f"Failed pages: {len(failed)}")
    
    # Show titles of successful pages
    if successful:
        print(f"\\nPage titles found:")
        for i, page in enumerate(successful[:5], 1):
            title = page['title'] or 'No title'
            print(f"  {i}. {title[:60]}{'...' if len(title) > 60 else ''}")
    
    # Show error types
    if failed:
        error_types = {}
        for page in failed:
            error = page['error']
            error_types[error] = error_types.get(error, 0) + 1
        
        print(f"\\nError types:")
        for error, count in error_types.items():
            print(f"  {error}: {count}")
    
    return results

def cross_domain_example():
    """Example of cross-domain crawling."""
    print("\\n=== Cross-Domain Crawling Example ===")
    
    crawler = WebCrawler(
        seed_url="https://httpbin.org",
        max_depth=2,
        delay=1.5,
        max_pages=15,
        same_domain_only=False,  # Allow cross-domain
        respect_robots_txt=True
    )
    
    results = crawler.crawl()
    
    # Analyze domains found
    domains = set()
    for page in crawler.get_successful_urls():
        from urllib.parse import urlparse
        domains.add(urlparse(page['url']).netloc)
    
    print(f"Found {len(domains)} different domains:")
    for domain in sorted(domains):
        print(f"  {domain}")
    
    return results

def main():
    """Run all examples."""
    try:
        # Run advanced example
        advanced_example()
        
        # Run cross-domain example
        cross_domain_example()
        
        print("\\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")

if __name__ == "__main__":
    main()