#!/usr/bin/env python3
"""
Build and deployment script for the webcrawler package.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result.returncode == 0

def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    dirs_to_clean = ['build', 'dist', 'webcrawler.egg-info', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}")
    
    # Clean __pycache__ recursively
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                full_path = os.path.join(root, dir_name)
                shutil.rmtree(full_path)
                print(f"Removed {full_path}")

def run_tests():
    """Run the test suite."""
    print("Running tests...")
    if not run_command("python -m pytest tests/ -v", check=False):
        print("Warning: Some tests failed")
        return False
    return True

def run_linting():
    """Run code linting."""
    print("Running code linting...")
    success = True
    
    # Run flake8
    if not run_command("python -m flake8 webcrawler --max-line-length=88", check=False):
        print("Warning: Flake8 found issues")
        success = False
    
    # Run black (dry run)
    if not run_command("python -m black --check webcrawler", check=False):
        print("Warning: Black formatting issues found")
        success = False
    
    return success

def build_package():
    """Build the package."""
    print("Building package...")
    
    # Build source distribution
    if not run_command("python setup.py sdist"):
        return False
    
    # Build wheel
    if not run_command("python setup.py bdist_wheel"):
        return False
    
    print("Package built successfully!")
    return True

def install_package():
    """Install the package in development mode."""
    print("Installing package in development mode...")
    return run_command("pip install -e .")

def upload_to_pypi():
    """Upload package to PyPI."""
    print("Uploading to PyPI...")
    print("Note: Make sure you have twine installed and configured!")
    
    # Check distribution
    if not run_command("python -m twine check dist/*"):
        return False
    
    # Upload to test PyPI first
    print("Uploading to test PyPI...")
    if not run_command("python -m twine upload --repository testpypi dist/*", check=False):
        print("Failed to upload to test PyPI")
    
    # Ask user if they want to upload to real PyPI
    response = input("Upload to real PyPI? (y/N): ")
    if response.lower() == 'y':
        return run_command("python -m twine upload dist/*")
    
    return True

def main():
    """Main build script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build and deploy webcrawler package")
    parser.add_argument("action", choices=[
        "clean", "test", "lint", "build", "install", "upload", "all"
    ], help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "clean":
        clean_build()
    
    elif args.action == "test":
        run_tests()
    
    elif args.action == "lint":
        run_linting()
    
    elif args.action == "build":
        clean_build()
        build_package()
    
    elif args.action == "install":
        install_package()
    
    elif args.action == "upload":
        upload_to_pypi()
    
    elif args.action == "all":
        print("Running full build pipeline...")
        
        # Clean first
        clean_build()
        
        # Run tests
        if not run_tests():
            print("Tests failed, aborting build")
            sys.exit(1)
        
        # Run linting
        run_linting()  # Non-blocking
        
        # Build package
        if not build_package():
            print("Build failed")
            sys.exit(1)
        
        print("\\nBuild pipeline completed successfully!")
        print("\\nNext steps:")
        print("1. Install with: python build.py install")
        print("2. Test CLI with: webcrawler --help")
        print("3. Upload with: python build.py upload")

if __name__ == "__main__":
    main()