"""
Server Instance GUI Widget Module

This module implements the graphical user interface for REST server instance management
within the REST Tester application. It provides a comprehensive interface for configuring,
controlling, and monitoring HTTP server instances with real-time parameter updates
and dynamic endpoint management.

Key Features:
    - Complete server configuration interface with validation
    - Real-time parameter updates for running servers (response delay, response content)
    - Dynamic UI state management based on server status
    - HTTP methods selection with checkbox groups
    - Signal-based communication with server management system
    - Factory-pattern widget creation for consistent UI
    - Template-based response configuration with Jinja2 support
    - Comprehensive logging integration with visual feedback

Architecture:
    - Inherits from BaseInstanceWidget for common functionality
    - Uses FormFieldFactory for consistent widget creation
    - Implements Observer pattern with Qt signals for state changes
    - Provides callback-based parameter updates for running servers
    - Integrates validation system for input field management

UI Components:
    - Host and route configuration with validation
    - HTTP methods selection via checkbox groups
    - Response template editor with Jinja2 support
    - Timing configuration (delays)
    - Flag configuration (autostart)
    - Start/Stop control with visual state feedback
    - Real-time logging output display

Classes:
    - ServerInstanceWidget: Main widget for server instance management

Dependencies:
    - PySide6: Qt framework for GUI components
    - BaseInstanceWidget: Common instance widget functionality
    - FormFieldFactory: Consistent widget creation patterns
    - validate: Input validation and formatting utilities
    - ConfigModel: Data model for configuration management
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QLineEdit, QCheckBox, QPushButton, 
    QHBoxLayout, QTextEdit, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from .model import ConfigModel
from .validate import validate_and_format_qedit, on_edit_qedit, on_focus_qedit
from .base_instance_widget import BaseInstanceWidget
from .form_field_factory import CommonFieldBuilder, FormFieldFactory


class ServerInstanceWidget(BaseInstanceWidget):
    """
    Graphical user interface widget for REST server instance management.
    
    This widget provides a comprehensive interface for configuring and controlling
    HTTP server instances. It supports real-time parameter updates for certain
    server properties, dynamic state management, and seamless integration with
    the server management system through Qt's signal-slot mechanism.
    
    The widget implements a factory-based approach for UI creation, ensuring
    consistency across different instance types while providing server-specific
    functionality including HTTP methods selection, response template configuration,
    and timing parameters.
    
    Key Features:
        - Dynamic parameter updates for response content and delays
        - Visual state management with start/stop controls
        - HTTP methods selection via checkbox groups
        - Template-based response configuration
        - Comprehensive validation for all input fields
        - Real-time logging display integration
        - Thread-safe parameter updates during execution
        
    Signals:
        start_requested(object): Emitted when server start is requested
        stop_requested(object): Emitted when server stop is requested
        params_changed(object, dict): Emitted when parameters change during execution
        
    Attributes:
        server: The server instance model this widget manages
        Various UI elements for configuration and control
    """
    
    # Additional server-specific signals beyond base class
    start_requested = Signal(object)  # object = server_instance
    stop_requested = Signal(object)   # object = server_instance
    params_changed = Signal(object, dict)  # object = server_instance, dict = changed params
    
    def __init__(self, server_instance) -> None:
        """
        Initialize server widget with instance model.
        
        Args:
            server_instance: The server model object to manage
            
        Note:
            Server instance must be set before calling super().__init__()
            to ensure proper initialization order for UI setup.
        """
        self.server = server_instance  # Set before calling super()
        super().__init__(server_instance)
    
    def _setup_instance_ui(self) -> None:
        """
        Setup server-specific UI elements.
        
        This method is called by the base class during initialization
        to create the server-specific configuration interface.
        """
        self._setup_config_ui()
    
    def _connect_signals(self) -> None:
        """
        Connect server-specific signals.
        
        This method provides a hook for connecting additional signals
        beyond those handled by the base class. Currently placeholder
        for future server-specific signal connections.
        """
        # Server-specific signal connections will be added here
        pass
    
    def start_instance(self) -> None:
        """
        Request start of the server instance.
        
        Emits the start_requested signal to notify the management
        system that this server should be started.
        """
        self.start_requested.emit(self.server)
    
    def stop_instance(self) -> None:
        """
        Request stop of the server instance.
        
        Emits the stop_requested signal to notify the management
        system that this server should be stopped.
        """
        self.stop_requested.emit(self.server)
    
    def _update_ui_state(self) -> None:
        """
        Update UI elements based on current running state.
        
        This method coordinates UI state changes including button
        styling and field enablement based on whether the server
        is currently running or stopped.
        """
        self._update_button_style()
        if self.is_running:
            self.lock_fields()
        else:
            self.unlock_fields()
    
    def _setup_config_ui(self) -> None:
        """
        Setup the complete configuration UI using FormFieldFactory pattern.
        
        This method creates all necessary UI elements for server configuration
        including host settings, route configuration, HTTP methods selection,
        response template editor, timing parameters, and control buttons.
        It uses the factory pattern for consistent widget creation.
        
        UI Components Created:
            - Host field with validation
            - Autostart flag checkbox
            - Initial delay and response delay timing fields
            - Route field for endpoint configuration
            - HTTP methods checkbox group for method selection
            - Response template editor with Jinja2 support
            - Start/Stop toggle button with state styling
            
        Signal Connections:
            Response delay field is connected to change handlers that
            support real-time parameter updates for running servers.
        """
        builder = CommonFieldBuilder(self.server, self.form_layout)
        
        # Host field with validation
        builder.add_host_field(self.server.get_value('host'))
        
        # Flags configuration (only autostart for server)
        flags_config = [('autostart', 'Autostart', self.server.get_value('autostart'))]
        layout, checkboxes = FormFieldFactory.create_flags_layout(self.server, flags_config)
        self.form_layout.addRow("Flags", layout)
        self.autostart_box = checkboxes['autostart']
        
        # Timing configuration fields
        builder.add_initial_delay_field(self.server.get_value('initial_delay_sec'))
        builder.add_response_delay_field(self.server.get_value('response_delay_sec'))
        
        # Route field for endpoint configuration
        builder.add_route_field(self.server.get_value('route'))
        
        # Response delay field with real-time update support
        self.delay_edit = builder.fields['response_delay']
        self.delay_edit.textChanged.connect(lambda: self._on_response_delay_changed())
        
        # HTTP methods checkbox group for method selection
        default_methods = self.server.defaults.get('methodes', [])
        current_methods = self.server.get_value('methodes') or []
        layout, button_group, checkboxes = builder.add_methods_checkboxes(
            default_methods, current_methods, self._on_methods_changed
        )
        self.methods_group = button_group
        
        # Response template editor with Jinja2 support
        builder.add_response_field(self.server.get_value('response'))
        
        # Control buttons layout
        self.buttons_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.clicked.connect(self._on_toggle_clicked)
        self._update_button_style()
        
        self.buttons_layout.addWidget(self.toggle_btn)
        self.form_layout.addRow("Actions", self.buttons_layout)
        
        # Store field references for state management
        self.host_edit = builder.fields['host']
        self.initial_delay_edit = builder.fields['initial_delay']
        self.route_edit = builder.fields['route']
        self.response_edit = builder.fields['response']
    
    def _on_methods_changed(self, selected_methods: List[str]) -> None:
        """
        Handle changes to HTTP methods selection.
        
        Args:
            selected_methods: List of currently selected HTTP methods
            
        This method ensures that at least one method is always selected
        and updates the server model with the current selection. It provides
        fallback behavior to prevent servers from having no supported methods.
        
        Validation:
            - Ensures at least one method is always selected
            - Automatically selects first available method if none selected
            - Updates server model with validated method list
        """
        # Ensure at least one method is selected for server functionality
        if not selected_methods:
            # Re-check first available method if no method is selected
            if hasattr(self, 'methods_group') and self.methods_group.buttons():
                first_button = self.methods_group.buttons()[0]
                first_button.setChecked(True)
                selected_methods = [first_button.text()]
        
        # Update server model with validated method selection
        self.server.set_value('methodes', selected_methods)
    
    def _on_toggle_clicked(self) -> None:
        """
        Handle start/stop toggle button click events.
        
        This method determines the current state and emits the appropriate
        signal to either start or stop the server instance. The actual
        state management is handled by the parent management system.
        """
        if self.is_running:
            self.stop_requested.emit(self.server)
        else:
            self.start_requested.emit(self.server)

    def _update_button_style(self) -> None:
        """
        Update toggle button styling based on current running state.
        
        Provides visual feedback for the current server state:
        - Running: Red "Stop" button with styled appearance
        - Stopped: Default "Start" button with standard styling
        
        The styling uses CSS-like syntax for consistent appearance
        across different platform themes.
        """
        if self.is_running:
            self.toggle_btn.setText("Stop")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: 1px solid #b71c1c;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
                QPushButton:pressed {
                    background-color: #9a0007;
                }
            """)
        else:
            self.toggle_btn.setText("Start")
            self.toggle_btn.setStyleSheet("")  # Standard button style

    def _on_response_delay_changed(self) -> None:
        """
        Handle response delay field changes with real-time updates.
        
        This method processes response delay changes and applies them
        immediately to running servers. It validates the input and emits
        parameter change signals for live server update.
        
        Validation:
            - Applies standard validation through validation system
            - Converts to float for numeric validation
            - Ignores invalid values to prevent server disruption
        """
        on_edit_qedit(self.server, self.delay_edit, 'response_delay_sec')
        if self.is_running:
            try:
                response_delay_sec = float(self.delay_edit.text())
                self.params_changed.emit(self.server, {'response_delay_sec': response_delay_sec})
            except ValueError:
                pass  # Ignore invalid values during live editing

    def _on_response_changed(self) -> None:
        """
        Handle response template changes with real-time updates.
        
        This method processes response template changes and applies them
        immediately to running servers. The response supports Jinja2
        templating for dynamic response generation.
        
        Note:
            This method is defined but not currently connected to response
            field changes. It's available for future enhancement of
            real-time response template updates.
        """
        on_edit_qedit(self.server, self.response_edit, 'response')
        if self.is_running:
            response = self.response_edit.toPlainText()
            self.params_changed.emit(self.server, {'response': response})
    
    def set_running(self, running: bool) -> None:
        """
        Set the running state and update UI accordingly.
        
        Args:
            running: True if server is running, False if stopped
            
        This method calls the base class implementation and ensures
        proper UI state management across the widget hierarchy.
        """
        super().set_running(running)  # Call base class method
    
    def lock_fields(self) -> None:
        """
        Lock configuration fields when server is running.
        
        This method disables fields that cannot be changed during
        server execution, while keeping fields enabled that support
        real-time updates (response delay and response content).
        
        Locked Fields:
            - Host configuration (requires restart)
            - Autostart flag (initialization parameter)
            - Initial delay (startup parameter)
            - Route configuration (affects endpoint registration)
            
        Unlocked Fields:
            - Response delay (supports real-time updates)
            - Response content (supports real-time updates)
        """
        self.host_edit.setEnabled(False)
        self.autostart_box.setEnabled(False)
        self.initial_delay_edit.setEnabled(False)
        self.route_edit.setEnabled(False)
        # Response and Response Delay remain unlocked for dynamic updates
        
    def unlock_fields(self) -> None:
        """
        Unlock all configuration fields when server is stopped.
        
        This method re-enables all configuration fields when the server
        is not running, allowing full reconfiguration of the server
        instance before the next execution.
        """
        self.host_edit.setEnabled(True)
        self.autostart_box.setEnabled(True)
        self.initial_delay_edit.setEnabled(True)
        self.route_edit.setEnabled(True)
    
    def get_log_signal_handler(self):
        """
        Get the log signal handler for this server instance.
        
        Returns:
            The signal handler object for integrating with the logging system
            
        This method provides access to the logging signal handler for
        this specific server instance, enabling targeted log output
        and monitoring capabilities.
        """
        return self.log_widget.get_signal_handler()