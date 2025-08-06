"""
Base Instance Widget - Abstract Foundation for Server/Client GUI Components

This module provides the abstract base class for all instance-specific GUI
widgets in the REST Tester application. It implements the Template Method
pattern to ensure consistent structure and behavior across different instance
types while allowing customization for specific needs.

Key Features:
    - Common UI structure with config/log separation
    - Standardized signal interface for status changes
    - Consistent layout management with splitter controls
    - Abstract methods for subclass customization
    - Integrated logging widget for real-time feedback

Architecture Benefits:
    - Eliminates code duplication between server and client widgets
    - Ensures consistent user experience across instance types
    - Provides extension points for specific functionality
    - Centralizes common behavior like status management

Design Pattern:
    Implements the Template Method pattern with abstract methods for
    customization points and concrete methods for common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QFormLayout
from PySide6.QtCore import Qt, Signal, QObject

from .log_widget import InstanceLogWidget


class BaseInstanceWidget(QWidget):
    """
    Abstract base class for server and client instance widgets.
    
    This class provides the fundamental structure and behavior that all
    instance widgets share, while defining clear extension points for
    specific functionality. It manages the common lifecycle, UI layout,
    and status tracking that is consistent across all instance types.
    
    Template Method Pattern:
        - _setup_base_ui(): Concrete implementation of common structure
        - _setup_instance_ui(): Abstract - subclass-specific UI setup
        - _connect_signals(): Abstract - subclass-specific signal handling
        - _update_ui_state(): Abstract - subclass-specific state updates
    
    Common Functionality:
        - Splitter-based layout with configuration and logging areas
        - Status tracking and change notification
        - Consistent widget proportions and styling
        - Integration with logging system
    
    Signals:
        status_changed(bool): Emitted when running status changes
        params_updated(dict): Emitted when configuration parameters change
    """
    
    # Common signals for all instance types
    status_changed = Signal(bool)  # True = running, False = stopped
    params_updated = Signal(dict)  # Configuration parameter changes
    
    def __init__(self, instance: Any, parent: Optional[QWidget] = None):
        """
        Initialize base widget with instance and optional parent.
        
        Args:
            instance: The underlying server or client instance object
            parent: Optional parent widget for Qt hierarchy
        """
        super().__init__(parent)
        
        self.instance = instance
        self.is_running = False
        
        # Execute initialization sequence using template method pattern
        self._setup_base_ui()
        self._setup_instance_ui()
        self._connect_signals()
    
    def _setup_base_ui(self):
        """
        Setup the common UI structure shared by all instance types.
        
        Creates a standardized layout with:
        - Vertical splitter separating configuration and logging areas
        - Form layout for configuration parameters
        - Integrated log widget for real-time feedback
        - Appropriate proportional sizing (70% config, 30% log)
        """
        # Main container layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create vertical splitter for resizable config/log areas
        self.splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.splitter)
        
        # Configuration area (top section)
        self.config_widget = QWidget()
        self.form_layout = QFormLayout(self.config_widget)
        self.splitter.addWidget(self.config_widget)
        
        # Logging area (bottom section)
        self.log_widget = InstanceLogWidget(self.instance.name)
        self.splitter.addWidget(self.log_widget)
        
        # Set proportional sizing (config area gets more space)
        self.splitter.setStretchFactor(0, 7)  # 70% for configuration
        self.splitter.setStretchFactor(1, 3)  # 30% for logging
    
    @abstractmethod
    def _setup_instance_ui(self):
        """
        Setup instance-specific UI elements.
        
        This method must be implemented by subclasses to create the
        specific form fields, buttons, and controls needed for their
        particular instance type (server vs client).
        
        Implementation should:
        - Add form fields to self.form_layout
        - Create instance-specific controls
        - Configure initial widget states
        """
        raise NotImplementedError("Subclasses must implement _setup_instance_ui")
    
    @abstractmethod
    def _connect_signals(self):
        """
        Connect instance-specific signals and slots.
        
        This method must be implemented by subclasses to establish
        the signal connections specific to their functionality.
        
        Implementation should:
        - Connect form field signals to handlers
        - Connect control button signals
        - Setup any custom signal routing
        """
        raise NotImplementedError("Subclasses must implement _connect_signals")
    
    @abstractmethod
    def start_instance(self):
        """
        Start the instance (server or client).
        
        This method must be implemented by subclasses to handle the
        specific startup procedure for their instance type.
        """
        raise NotImplementedError("Subclasses must implement start_instance")
    
    @abstractmethod
    def stop_instance(self):
        """
        Stop the instance (server or client).
        
        This method must be implemented by subclasses to handle the
        specific shutdown procedure for their instance type.
        """
        raise NotImplementedError("Subclasses must implement stop_instance")
    
    def set_running(self, is_running: bool):
        """
        Update the running status and notify observers.
        
        This method provides a centralized way to update the instance
        running status and ensures that all dependent UI elements and
        observers are properly notified of the change.
        
        Args:
            is_running: True if instance is running, False if stopped
        """
        if self.is_running != is_running:
            self.is_running = is_running
            self._update_ui_state()
            self.status_changed.emit(is_running)
    
    @abstractmethod
    def _update_ui_state(self):
        """
        Update UI elements based on current running state.
        
        This method must be implemented by subclasses to handle
        state-dependent UI changes such as:
        - Enabling/disabling form fields
        - Changing button text and styling
        - Updating status indicators
        """
        raise NotImplementedError("Subclasses must implement _update_ui_state")
    
    def get_instance_name(self) -> str:
        """
        Get the display name of this instance.
        
        Returns:
            str: Human-readable instance identifier
        """
        return self.instance.name
    
    def get_running_status(self) -> bool:
        """
        Get the current operational status of the instance.
        
        Returns:
            bool: True if instance is currently running, False otherwise
        """
        return self.is_running
    
    def lock_fields(self):
        """
        Disable form fields to prevent modification during operation.
        
        This utility method can be used by subclasses to disable
        configuration fields when the instance is running and
        changes would be disruptive.
        """
        self.config_widget.setEnabled(False)
    
    def unlock_fields(self):
        """
        Enable form fields to allow configuration changes.
        
        This utility method can be used by subclasses to re-enable
        configuration fields when the instance is stopped and
        changes are safe to make.
        """
        self.config_widget.setEnabled(True)
