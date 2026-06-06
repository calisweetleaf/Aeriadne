"""
CTMv3 module entry point.

Enables: python -m ctmv3 <command> [args]
Dispatches to ctmv3.core.cli.main()
"""

from ctmv3.core.cli import main

if __name__ == "__main__":
    main()
