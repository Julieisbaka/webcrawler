"""
Setup configuration for the webcrawler package.
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='webcrawler',
    version='0.0.1',
    author='JulieISBaka',
    author_email='casperschorr06@gmail.com',
    description='A Python package for recursive web crawling with anti-detection features',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/webcrawler',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=1.0.0',
            'pre-commit>=2.20.0',
            'isort>=5.0.0',
            'pylint>=2.0.0',
        ],
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'webcrawler=webcrawler.cli:main',
        ],
    },
    keywords='web crawler spider scraping recursive crawling',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/webcrawler/issues',
        'Source': 'https://github.com/yourusername/webcrawler',
        'Documentation': 'https://webcrawler.readthedocs.io/',
    },
    include_package_data=True,
    zip_safe=False,
)