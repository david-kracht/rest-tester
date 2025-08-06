"""
Application Lifecycle Management

This module provides comprehensive lifecycle management for the REST Tester
application, handling initialization, execution, signal handling, and cleanup.

Key Responsibilities:
    - Qt Application setup and configuration
    - Main window lifecycle management
    - Graceful shutdown signal handling
    - Resource cleanup and memory management
    - Error handling and logging integration

Design Pattern:
    Implements the Application Controller pattern with dependency injection
    for clean separation of concerns and testability.
"""

import sys
import signal
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from ..service.logging_config import get_logger, shutdown_logging
from .config_locator import ConfigLocator


class ApplicationManager:
    """
    Manages the complete application lifecycle from startup to shutdown.
    
    This class orchestrates the entire application flow, ensuring proper
    initialization order, signal handling, and resource cleanup. It acts
    as the central coordinator between the Qt framework, configuration
    system, and GUI components.
    
    Attributes:
        logger: Application-wide logger instance
        config_locator: Configuration file discovery service
        app: Qt application instance
        main_window: Primary GUI window
        _signal_timer: Timer for Unix signal processing
    """
    
    def __init__(self):
        """Initialize the application manager with required services."""
        self.logger = get_logger("ApplicationManager")
        self.config_locator = ConfigLocator()
        self.app: Optional[QApplication] = None
        self.main_window = None
        self._signal_timer: Optional[QTimer] = None
    
    def initialize(self) -> bool:
        """
        Initialize the application and all critical components.
        
        Performs the complete application startup sequence:
        1. Creates Qt application instance
        2. Locates and loads configuration
        3. Initializes main window
        4. Sets up signal handling for graceful shutdown
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Note:
            GUI imports are deferred until needed to improve startup time
            and allow for better error handling of missing dependencies.
        """
        try:
            # Deferred import to avoid circular dependencies and improve startup
            from ..gui_model import ConfigModel, MainWindow
            
            # Initialize Qt application with system arguments
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("REST Tester")
            self.app.setApplicationVersion("1.0.0")
            
            # Locate and load configuration with fallback handling
            config_path = self.config_locator.find_config_path()
            config = ConfigModel(config_path)
            
            # Create and configure main window
            self.main_window = MainWindow(config)
            self._setup_main_window()
            
            # Enable graceful shutdown handling
            self._setup_signal_handling()
            
            self.logger.info("Application initialized successfully")
            return True
            
        except ImportError as e:
            self.logger.error(f"Missing required dependencies: {e}")
            self.logger.error("Please ensure PySide6 and other dependencies are installed")
            return False
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def _setup_main_window(self):
        """
        Configure the main window with appropriate size and visibility.
        
        Sets reasonable default dimensions and ensures the window is
        properly displayed to the user.
        """
        if not self.main_window:
            self.logger.warning("Main window not available for setup")
            return
            
        # Set responsive window dimensions
        self.main_window.setMinimumSize(800, 600)
        self.main_window.resize(1200, 800)
        self.main_window.show()
        
        self.logger.debug("Main window configured and displayed")
    
    def _setup_signal_handling(self):
        """
        Configure Unix signal handling for graceful application shutdown.
        
        Sets up SIGINT (Ctrl+C) handling to allow clean shutdown when
        the application is run from a terminal. Uses a QTimer to ensure
        Python signal handling works correctly with the Qt event loop.
        
        Technical Note:
            Qt's event loop can interfere with Python's signal handling.
            The timer ensures signals are processed regularly.
        """
        if not self.app or not self.main_window:
            self.logger.warning("Cannot setup signal handling - components not available")
            return
            
        def signal_handler(signum, frame):
            """Handle shutdown signals gracefully."""
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received {signal_name} - initiating graceful shutdown")
            self.shutdown()
        
        # Register signal handler for common termination signals
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create timer to allow Python signal processing in Qt event loop
        self._signal_timer = QTimer(self.app)
        self._signal_timer.start(100)  # Check every 100ms for signals
        self._signal_timer.timeout.connect(lambda: None)  # Keep event loop responsive
        
        self.logger.debug("Signal handling configured")
    
    
    def run(self) -> int:
        """
        Execute the main application loop and return exit code.
        
        Starts the Qt event loop and handles any runtime exceptions.
        This method blocks until the application is closed.
        
        Returns:
            int: Application exit code (0 = success, 1 = error, other = Qt exit code)
            
        Note:
            Cleanup is performed automatically in the finally block
            regardless of how the application terminates.
        """
        if not self.app:
            self.logger.error("Cannot run - application not initialized")
            return 1
            
        try:
            self.logger.info("Starting application event loop")
            return self.app.exec()
        except Exception as e:
            self.logger.error(f"Runtime error in application: {e}")
            return 1
        finally:
            # Ensure cleanup runs regardless of exit method
            self.cleanup()
    
    def shutdown(self):
        """
        Initiate graceful application shutdown.
        
        Closes the main window and signals the Qt application to quit.
        This method is typically called by signal handlers or user actions.
        """
        self.logger.info("Initiating application shutdown")
        
        if self.main_window:
            self.main_window.close()
        if self.app:
            self.app.quit()
    
    def cleanup(self):
        """
        Perform comprehensive resource cleanup.
        
        Ensures all resources are properly released, including:
        - Configuration resources
        - Logging system shutdown
        - Any other allocated resources
        
        This method is designed to be safe to call multiple times.
        """
        try:
            self.logger.debug("Starting resource cleanup")
            
            # Clean up configuration resources
            if hasattr(self, 'config_locator'):
                self.config_locator.cleanup()
            
            # Shutdown logging system (this should be last)
            shutdown_logging()
            
        except Exception as e:
            # Use print since logger may not be available during cleanup
            print(f"Warning: Error during cleanup: {e}")
