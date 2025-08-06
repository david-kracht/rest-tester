"""
Configuration File Discovery and Management

This module implements a hierarchical configuration discovery system that
supports multiple deployment scenarios (development, user, package) with
appropriate fallback mechanisms.

Configuration Priority (highest to lowest):
    1. Development: resources/config.yaml (project root)
    2. User: config.yaml (current working directory)
    3. Package: Embedded config.yaml from installed package

Key Features:
    - Automatic fallback between configuration sources
    - Temporary file management for package resources
    - Comprehensive logging for configuration discovery
    - Resource cleanup to prevent memory leaks

Design Pattern:
    Implements the Chain of Responsibility pattern for configuration
    discovery with proper resource management.
"""

import os
import importlib.resources
from pathlib import Path
from typing import Optional, ContextManager
from ..service.logging_config import get_logger


class ConfigLocator:
    """
    Handles hierarchical configuration file discovery and lifecycle management.
    
    This class implements a robust configuration discovery mechanism that
    adapts to different deployment environments while maintaining proper
    resource cleanup and error handling.
    
    Attributes:
        logger: Class-specific logger for configuration operations
        _temp_config_context: Context manager for temporary package resources
        
    Usage:
        locator = ConfigLocator()
        config_path = locator.find_config_path()
        # ... use configuration ...
        locator.cleanup()  # Important: cleanup temporary resources
    """
    
    def __init__(self):
        """Initialize the configuration locator with logging."""
        self.logger = get_logger("ConfigLocator")
        self._temp_config_context: Optional[ContextManager] = None
    
    def find_config_path(self) -> str:
        """
        Discover configuration file using hierarchical priority system.
        
        Searches for configuration files in order of preference:
        1. Development environment (project root/resources/config.yaml)
        2. User-specific configuration (cwd/config.yaml)
        3. Package default configuration (embedded resource)
        
        Returns:
            str: Absolute path to the configuration file
            
        Raises:
            FileNotFoundError: If no configuration file can be located
            
        Note:
            When using package resources, temporary files are created and
            must be cleaned up using the cleanup() method.
        """
        # Priority 1: Development configuration (project structure)
        dev_config = Path("resources/config.yaml")
        if dev_config.exists():
            abs_path = dev_config.absolute()
            self.logger.info(f"Using development config: {abs_path}")
            return str(abs_path)

        # Priority 2: User-specific configuration (working directory)
        user_config = Path("config.yaml")
        if user_config.exists():
            abs_path = user_config.absolute()
            self.logger.info(f"Using user config: {abs_path}")
            return str(abs_path)

        # Priority 3: Package embedded configuration (fallback)
        return self._get_package_config()
    
    def _get_package_config(self) -> str:
        """
        Extract configuration from package resources to temporary file.
        
        Creates a temporary file from the embedded package configuration
        resource. This is necessary because some configuration libraries
        require file paths rather than file-like objects.
        
        Returns:
            str: Path to temporary configuration file
            
        Raises:
            FileNotFoundError: If package resource cannot be located or accessed
            
        Technical Note:
            Uses importlib.resources for Python 3.9+ compatibility with
            proper resource management through context managers.
        """
        try:
            # Access package resource using modern importlib.resources API
            resources_ref = importlib.resources.files('rest_tester') / 'resources' / 'config.yaml'
            
            if not resources_ref.is_file():
                raise FileNotFoundError("Package config.yaml resource not found")
            
            # Create temporary file context (must be cleaned up later)
            self._temp_config_context = importlib.resources.as_file(resources_ref)
            temp_path = self._temp_config_context.__enter__()
            
            self.logger.info(f"Using package config: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Failed to access package configuration: {e}")
            raise FileNotFoundError(f"Cannot load package configuration: {e}")
    
    def cleanup(self):
        """
        Clean up temporary resources and release file handles.
        
        Properly closes any temporary files created from package resources
        to prevent resource leaks. This method is safe to call multiple
        times and should be called when the configuration is no longer needed.
        
        Note:
            This is particularly important when using package resources,
            as they may create temporary files that need explicit cleanup.
        """
        if self._temp_config_context:
            try:
                self._temp_config_context.__exit__(None, None, None)
                self.logger.debug("Temporary configuration resources cleaned up")
            except Exception as e:
                self.logger.warning(f"Error during configuration cleanup: {e}")
            finally:
                self._temp_config_context = None
