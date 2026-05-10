#!/usr/bin/env python3
"""
ProcPilot Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="procpilot",
    version="1.0.0",
    author="gitstq",
    author_email="",
    description="🚀 ProcPilot - Lightweight Terminal Process Intelligence Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/procpilot",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "procpilot=procpilot.cli:main",
        ],
    },
    keywords="process manager monitor terminal tui cli system",
    project_urls={
        "Bug Reports": "https://github.com/gitstq/procpilot/issues",
        "Source": "https://github.com/gitstq/procpilot",
    },
)
