#!/usr/bin/env python3
"""
REST Tester - Main Application Entry Point

Copyright (c) 2025 David Kracht
Licensed under the MIT License. See LICENSE file in the project root.

This module serves as the primary entry point for the REST Tester application,
providing a unified interface for testing REST APIs through both server and
client functionality with a Qt-based GUI.

Architecture:
    - Uses ApplicationManager for lifecycle management
    - Implements clean separation of concerns
    - Provides proper error handling and exit codes

Example:
    $ python -m rest_tester.main
    $ rest-tester --version
"""

import sys
import argparse
from .core.application_manager import ApplicationManager


def parse_arguments():
    """
    Parse and validate command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
        
    Note:
        Currently handles only --version flag. Can be extended
        for additional CLI options like --config or --debug.
    """
    from . import __version__
    
    parser = argparse.ArgumentParser(
        description="REST Tester - Comprehensive testing tool for REST APIs",
        prog="rest-tester",
        epilog="Visit https://github.com/david-kracht/rest-tester for documentation"
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args()


def main():
    """
    Main application entry point with proper error handling.
    
    This function orchestrates the entire application lifecycle:
    1. Parses command line arguments
    2. Initializes the application manager
    3. Runs the Qt application
    4. Handles graceful shutdown
    
    Returns:
        None: Exits with appropriate exit code via sys.exit()
        
    Exit Codes:
        0: Success
        1: Initialization failure
        Other: Qt application exit code
    """
    # Parse command line arguments (--version handled automatically)
    parse_arguments()
    
    # Initialize application manager with dependency injection
    app_manager = ApplicationManager()
    
    # Attempt initialization - exit if critical failure
    if not app_manager.initialize():
        sys.exit(1)
    
    # Run application and propagate exit code
    exit_code = app_manager.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
