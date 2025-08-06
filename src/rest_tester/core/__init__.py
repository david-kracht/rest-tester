"""
Core application components.
Contains fundamental application infrastructure and lifecycle management.
"""

from .config_locator import ConfigLocator
from .application_manager import ApplicationManager
from .service_facade import ServiceFacade
from .validation_service import ValidationService

__all__ = ['ConfigLocator', 'ApplicationManager', 'ServiceFacade', 'ValidationService']
