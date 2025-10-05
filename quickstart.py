#!/usr/bin/env python3
"""
Quick start script for testing the webcrawler package locally.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    return result.returncode == 0

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    return run_command("pip install -r requirements.txt")

def install_package():
    """Install the package in development mode."""
    print("Installing webcrawler package in development mode...")
    return run_command("pip install -e .")

def test_installation():
    """Test that the package is properly installed."""
    print("Testing installation...")
    
    # Test import
    try:
        from webcrawler import WebCrawler
        print("✓ Package import successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Test CLI
    print("Testing CLI...")
    result = subprocess.run([sys.executable, "-m", "webcrawler.cli", "--help"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ CLI test successful")
    else:
        print("✗ CLI test failed")
        return False
    
    return True

def run_example():
    """Run a basic example."""
    print("Running basic example...")
    
    try:
        from webcrawler import WebCrawler
        
        # Create a simple crawler
        crawler = WebCrawler(
            seed_url="https://httpbin.org",
            max_depth=1,
            delay=2.0,
            max_pages=5
        )
        
        print("Starting crawl (this may take a few seconds)...")
        results = crawler.crawl()
        
        summary = crawler.get_summary()
        print(f"\\nCrawl completed!")
        print(f"Pages crawled: {summary['total_pages_crawled']}")
        print(f"Links found: {summary['total_links_found']}")
        
        # Save results
        crawler.save_results("quickstart_results.json")
        print("Results saved to quickstart_results.json")
        
        return True
        
    except Exception as e:
        print(f"Example failed: {e}")
        return False

def main():
    """Main quickstart function."""
    print("WebCrawler Package Quick Start")
    print("==============================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Install package
    if not install_package():
        print("Failed to install package")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("Installation test failed")
        sys.exit(1)
    
    # Run example
    print("\\nRunning a quick example...")
    if run_example():
        print("\\n✓ Quick start completed successfully!")
        
        print("\\nNext steps:")
        print("1. Try the CLI: webcrawler --help")
        print("2. Run examples: python examples/basic_example.py")
        print("3. Check the documentation in README.md")
        print("4. Build the package: python build.py all")
    else:
        print("\\n✗ Example failed, but package is installed")
    
    print("\\nFor more information, see README.md")

if __name__ == "__main__":
    main()