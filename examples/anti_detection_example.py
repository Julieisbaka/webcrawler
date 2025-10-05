"""
Advanced example showcasing anti-detection features of the webcrawler package.

This example demonstrates various anti-detection techniques including:
- User agent rotation
- Proxy rotation
- Adaptive delay strategies
- Header randomization
- Session management
"""

from webcrawler import WebCrawler, AntiDetectionConfig
import json
import time

def example_basic_anti_detection():
    """Example using basic anti-detection features."""
    print("=== Basic Anti-Detection Example ===")
    
    # Create crawler with automatic anti-detection
    crawler = WebCrawler(
        seed_url="https://httpbin.org",
        max_depth=2,
        max_pages=15,
        enable_anti_detection=True,  # Enables UA rotation, header randomization, adaptive delays
        delay_strategy="adaptive",
        min_delay=1.0,
        max_delay=4.0,
        session_rotation_interval=5  # Rotate session every 5 requests
    )
    
    print(f"Starting crawl with anti-detection enabled...")
    results = crawler.crawl()
    
    # Show anti-detection statistics
    stats = crawler.get_anti_detection_stats()
    print(f"\\nAnti-Detection Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Session rotations: {stats['session_rotations']}")
    
    if 'user_agents' in stats:
        print(f"  User agents available: {stats['user_agents']['total_available']}")
        print(f"  UA rotation strategy: {stats['user_agents']['rotation_strategy']}")
    
    if 'response_times' in stats:
        rt = stats['response_times']
        print(f"  Average response time: {rt['average']:.2f}s")
        print(f"  Response time range: {rt['min']:.2f}s - {rt['max']:.2f}s")
    
    # Save results with detailed information
    crawler.save_results('anti_detection_basic_results.json')
    return results

def example_proxy_rotation():
    """Example using proxy rotation (requires actual proxies)."""
    print("\\n=== Proxy Rotation Example ===")
    
    # Example proxy list (these are dummy proxies for demonstration)
    # In real usage, you would provide working proxy servers
    proxy_list = [
        {'http': 'http://proxy1.example.com:8080', 'https': 'https://proxy1.example.com:8080'},
        {'http': 'http://proxy2.example.com:8080', 'https': 'https://proxy2.example.com:8080'},
        {'http': 'http://proxy3.example.com:8080', 'https': 'https://proxy3.example.com:8080'},
    ]
    
    # Note: This example will fail with dummy proxies, but shows the configuration
    try:
        crawler = WebCrawler(
            seed_url="https://httpbin.org/ip",  # Good for testing IP changes
            max_depth=1,
            max_pages=5,
            enable_anti_detection=True,
            enable_proxy_rotation=True,
            proxy_list=proxy_list,
            validate_proxies=False,  # Skip validation for demo
            session_rotation_interval=2,
            timeout=10.0
        )
        
        print("Proxy rotation configuration:")
        proxy_health = crawler.get_proxy_health()
        print(f"  Total proxies: {proxy_health['total_proxies']}")
        print(f"  Proxy rotation enabled: {proxy_health['proxy_rotation_enabled']}")
        
        # This would work with real proxies
        # results = crawler.crawl()
        print("  (Skipping actual crawl due to dummy proxies)")
        
    except Exception as e:
        print(f"Expected error with dummy proxies: {e}")

def example_custom_configuration():
    """Example with custom anti-detection configuration."""
    print("\\n=== Custom Anti-Detection Configuration ===")
    
    # Create custom configuration
    anti_detection_config = AntiDetectionConfig(
        enable_user_agent_rotation=True,
        enable_header_randomization=True,
        enable_adaptive_delays=True,
        min_delay=2.0,
        max_delay=6.0,
        delay_strategy="random",
        session_rotation_interval=10,
        max_retries=5,
        timeout=20.0
    )
    
    # Custom user agent list
    custom_user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    ]
    
    crawler = WebCrawler(
        seed_url="https://httpbin.org",
        max_depth=1,
        max_pages=8,
        enable_user_agent_rotation=True,
        enable_header_randomization=True,
        delay_strategy="random",
        min_delay=2.0,
        max_delay=6.0,
        session_rotation_interval=3,
        custom_user_agents=custom_user_agents,
        random_user_agent_rotation=True,
        max_retries=5
    )
    
    print("Custom configuration applied:")
    print(f"  Custom user agents: {len(custom_user_agents)}")
    print(f"  Delay strategy: random (2.0s - 6.0s)")
    print(f"  Session rotation: every 3 requests")
    print(f"  Max retries: 5")
    
    results = crawler.crawl()
    
    # Show detailed results
    print(f"\\nCrawl completed with custom configuration")
    for i, page in enumerate(results[:3]):
        print(f"\\nPage {i+1}: {page['url']}")
        print(f"  User Agent: {page.get('user_agent_used', 'N/A')[:60]}...")
        print(f"  Response Time: {page.get('response_time', 0):.2f}s")
        print(f"  Retries: {page.get('retry_count', 0)}")
        print(f"  Status: {'Success' if not page['error'] else page['error']}")
    
    return results

def example_delay_strategies():
    """Demonstrate different delay strategies."""
    print("\\n=== Delay Strategy Comparison ===")
    
    strategies = ["fixed", "random", "exponential", "adaptive"]
    
    for strategy in strategies:
        print(f"\\nTesting {strategy} delay strategy:")
        
        crawler = WebCrawler(
            seed_url="https://httpbin.org",
            max_depth=0,  # Only crawl seed URL
            max_pages=3,
            delay_strategy=strategy,
            min_delay=1.0,
            max_delay=3.0,
            enable_anti_detection=True
        )
        
        start_time = time.time()
        results = crawler.crawl()
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / len(results) if results else 0
        
        print(f"  Pages crawled: {len(results)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per request: {avg_time_per_request:.2f}s")
        
        # Show response times
        response_times = [p.get('response_time', 0) for p in results if p.get('response_time')]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            print(f"  Average server response time: {avg_response:.2f}s")

def main():
    """Run all anti-detection examples."""
    print("WebCrawler Anti-Detection Features Demo")
    print("=" * 45)
    
    try:
        # Run examples
        example_basic_anti_detection()
        
        # Note: Proxy example will show configuration but skip actual crawling
        example_proxy_rotation()
        
        example_custom_configuration()
        
        example_delay_strategies()
        
        print("\\n" + "=" * 45)
        print("Anti-detection demo completed!")
        print("\\nKey takeaways:")
        print("- Use enable_anti_detection=True for automatic protection")
        print("- Customize delay strategies based on target website behavior")
        print("- Proxy rotation requires working proxy servers")
        print("- Monitor response times to optimize delay settings")
        print("- Session rotation helps avoid detection patterns")
        
    except Exception as e:
        print(f"Error running anti-detection demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()