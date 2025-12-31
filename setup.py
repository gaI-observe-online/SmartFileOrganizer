"""Setup configuration for SmartFileOrganizer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path("README.md").read_text(encoding="utf-8")

setup(
    name="smartfile-organizer",
    version="1.0.0",
    description="AI-Powered Intelligent File Organization System",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="SmartFileOrganizer Contributors",
    url="https://github.com/gaI-observe-online/SmartFileOrganizer",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click==8.1.7",
        "rich==13.7.0",
        "pyyaml==6.0.1",
        "watchdog==4.0.0",
        "ollama==0.1.0",
        "pdfplumber==0.10.0",
        "python-docx==1.1.0",
        "openpyxl==3.1.0",
        "pytesseract==0.3.10",
        "Pillow==10.0.0",
        "eml-parser==1.17.0",
    ],
    extras_require={
        "test": [
            "pytest==8.3.0",
            "pytest-cov==6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "organize=smartfile.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    keywords="file organization ai ollama productivity",
)
