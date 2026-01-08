#!/usr/bin/env python3
"""Entry point for SmartFileOrganizer CLI."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from smartfile.cli.main import cli

if __name__ == '__main__':
    cli()
