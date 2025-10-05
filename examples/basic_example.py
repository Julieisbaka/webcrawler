"""
Basic example of using the webcrawler package.
"""

from webcrawler import WebCrawler

def basic_example():
    """Basic crawling example with conservative settings."""
    print("=== Basic Crawling Example ===")
    
    # Create crawler with conservative settings
    crawler = WebCrawler(
        seed_url="https://example.com",
        max_depth=1,  # Only go 1 level deep
        delay=2.0,    # 2 second delay between requests
        max_pages=10  # Limit to 10 pages
    )
    
    # Start crawling
    results = crawler.crawl()
    
    # Show results
    summary = crawler.get_summary()
    print(f"Crawled {summary['total_pages_crawled']} pages")
    print(f"Found {summary['total_links_found']} links")
    
    # Save to file
    crawler.save_results('basic_example_results.json')
    
    return results

if __name__ == "__main__":
    basic_example()