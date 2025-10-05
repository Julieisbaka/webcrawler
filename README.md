# WebCrawler

A Python package for recursive web crawling with advanced anti-detection features to bypass IP bans and rate limits.

## Features

### Core Crawling
- **Recursive Crawling**: Starts from a seed URL and follows all links found on each page
- **Depth Control**: Configurable maximum crawling depth to prevent infinite loops
- **Domain Filtering**: Option to crawl only within the same domain or across domains
- **URL Filtering**: Validates URLs and filters out unwanted file types
- **Robots.txt Support**: Respects robots.txt rules and crawl delays (configurable)

### Anti-Detection Features 🛡️
- **User Agent Rotation**: Rotates through realistic browser user agent strings
- **Proxy Rotation**: Distributes requests across multiple IP addresses
- **HTTP Header Randomization**: Randomizes headers to appear more human-like
- **Adaptive Delay Management**: Multiple delay strategies (fixed, random, exponential, adaptive)
- **Session Management**: Automatic session rotation to avoid detection patterns
- **Retry Logic**: Intelligent retry with exponential backoff for failed requests
- **SSL Verification Control**: Configurable SSL certificate verification

### Advanced Configuration
- **Multiple Delay Strategies**: Choose from fixed, random, exponential, or adaptive delays
- **Proxy Health Monitoring**: Automatic proxy validation and failure handling
- **Request Monitoring**: Track response times and adapt crawling behavior
- **Comprehensive Error Handling**: Detailed error reporting and recovery
- **Real-time Statistics**: Monitor anti-detection feature effectiveness

## Installation

### From PyPI (when published)
```bash
pip install webcrawler
```

### From Source
```bash
git clone <repository-url>
cd webcrawler
pip install .
```

### Development Installation
```bash
git clone <repository-url>
cd webcrawler
pip install -e .[dev]
```

## Usage

### Command Line Interface

The CLI now supports comprehensive anti-detection features:

```bash
# Basic crawling
webcrawler https://example.com

# Enable all anti-detection features
webcrawler https://example.com --anti-detection

# Custom anti-detection configuration
webcrawler https://example.com \
    --user-agent-rotation \
    --header-randomization \
    --delay-strategy adaptive \
    --min-delay 2 --max-delay 8 \
    --session-rotation 25

# Proxy rotation (requires proxy list)
webcrawler https://example.com \
    --proxy-rotation \
    --proxy-file proxies.txt \
    --validate-proxies

# Advanced configuration
webcrawler https://example.com \
    --anti-detection \
    --max-retries 5 \
    --timeout 45 \
    --stats \
    --verbose
```

### Programmatic Usage

#### Basic Anti-Detection

```python
from webcrawler import WebCrawler

# Enable automatic anti-detection
crawler = WebCrawler(
    seed_url="https://example.com",
    max_depth=2,
    max_pages=50,
    enable_anti_detection=True,  # Enables UA rotation, header randomization, adaptive delays
    delay_strategy="adaptive"
)

results = crawler.crawl()
crawler.save_results('results.json')

# Get anti-detection statistics
stats = crawler.get_anti_detection_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Session rotations: {stats['session_rotations']}")
```

#### Advanced Anti-Detection with Proxies

```python
# Configure proxy rotation
proxy_list = [
    {'http': 'http://proxy1:8080', 'https': 'https://proxy1:8080'},
    {'http': 'http://proxy2:8080', 'https': 'https://proxy2:8080'},
]

crawler = WebCrawler(
    seed_url="https://example.com",
    enable_anti_detection=True,
    enable_proxy_rotation=True,
    proxy_list=proxy_list,
    session_rotation_interval=25,
    min_delay=1.0,
    max_delay=5.0,
    max_retries=3
)

results = crawler.crawl()

# Monitor proxy health
proxy_health = crawler.get_proxy_health()
print(f"Proxy success rate: {proxy_health['health_percentage']:.1f}%")
```

#### Custom User Agents and Headers

```python
from webcrawler import WebCrawler, generate_random_headers

# Custom user agent list
custom_user_agents = [
    'MyBot/1.0 (compatible)',
    'CustomCrawler/2.0',
    'DataBot/1.5'
]

crawler = WebCrawler(
    seed_url="https://example.com",
    enable_user_agent_rotation=True,
    enable_header_randomization=True,
    custom_user_agents=custom_user_agents,
    random_user_agent_rotation=True
)

results = crawler.crawl()
```

#### Delay Strategy Comparison

```python
strategies = ["fixed", "random", "exponential", "adaptive"]

for strategy in strategies:
    crawler = WebCrawler(
        seed_url="https://example.com",
        delay_strategy=strategy,
        min_delay=1.0,
        max_delay=5.0,
        max_pages=10
    )
    
    results = crawler.crawl()
    stats = crawler.get_anti_detection_stats()
    
    print(f"{strategy} strategy:")
    if 'response_times' in stats:
        print(f"  Avg response time: {stats['response_times']['average']:.2f}s")
```

## Package Structure

```
webcrawler/
├── webcrawler/           # Main package directory
│   ├── __init__.py      # Package initialization
│   ├── crawler.py       # Main WebCrawler class
│   ├── utils.py         # Utility classes (URLValidator, LinkExtractor)
│   ├── exceptions.py    # Custom exceptions
│   └── cli.py           # Command-line interface
├── examples/            # Example scripts
│   ├── basic_example.py
│   └── advanced_example.py
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_webcrawler.py
├── setup.py            # Package setup (legacy)
├── pyproject.toml      # Modern Python packaging
├── requirements.txt    # Dependencies
├── build.py           # Build and deployment script
├── quickstart.py      # Quick installation test
├── MANIFEST.in        # Package data files
├── LICENSE            # MIT License
└── README.md          # This file
```

## Quick Start

1. **Clone and install**:
```bash
git clone <repository-url>
cd webcrawler
python quickstart.py
```

2. **Test the CLI**:
```bash
webcrawler --help
webcrawler https://httpbin.org --max-pages 5
```

3. **Run examples**:
```bash
python examples/basic_example.py
python examples/advanced_example.py
```

## Development

### Building the Package

```bash
# Clean, test, lint, and build
python build.py all

# Individual actions
python build.py clean
python build.py test
python build.py lint
python build.py build
```

### Running Tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=webcrawler
```

### Code Formatting

```bash
# Format code
python -m black webcrawler

# Check formatting
python -m black --check webcrawler

# Lint code
python -m flake8 webcrawler --max-line-length=88
```

## Output

The crawler saves data in JSON format with the following structure:

```json
[
  {
    "url": "https://example.com",
    "title": "Example Domain",
    "links": ["https://example.com/page1", "https://example.com/page2"],
    "status_code": 200,
    "error": null,
    "timestamp": 1696464000.123
  }
]
```

## Important Notes

### Ethical Considerations

- **Respect robots.txt**: This crawler doesn't check robots.txt by default. Consider adding this feature for production use.
- **Rate Limiting**: Always use appropriate delays between requests to avoid overwhelming servers.
- **Terms of Service**: Make sure you have permission to crawl the websites you're targeting.

### Performance Tips

- Start with small `max_depth` and `max_pages` values for testing
- Use longer delays for fragile or slow websites
- Consider using `same_domain_only=True` to avoid crawling the entire internet

### Common Use Cases

1. **Website Structure Analysis**: Understanding how pages are linked
2. **Broken Link Detection**: Finding dead links on a website
3. **Content Discovery**: Finding all pages on a domain
4. **SEO Analysis**: Analyzing internal linking structure

## Error Handling

The crawler handles various types of errors:
- Network timeouts
- Connection errors
- HTTP error codes
- Invalid URLs
- Parsing errors

All errors are logged and stored in the results for analysis.

## Files

- `web_crawler.py`: Main crawler implementation
- `examples.py`: Example usage scripts
- `requirements.txt`: Python dependencies
- `README.md`: This documentation

## Dependencies

- `requests`: For HTTP requests
- `beautifulsoup4`: For HTML parsing
- `lxml`: XML/HTML parser (faster than default)

## License

This project is for educational purposes. Use responsibly and in accordance with website terms of service.