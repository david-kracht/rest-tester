"""
Client Instance GUI Widget Module

This module implements the graphical user interface for REST client instance management
within the REST Tester application. It provides a comprehensive interface for configuring,
controlling, and monitoring HTTP client instances with real-time parameter updates
and dynamic state management.

Key Features:
    - Complete client configuration interface with validation
    - Real-time parameter updates for running clients
    - Dynamic UI state management based on client status
    - Signal-based communication with client management system
    - Factory-pattern widget creation for consistent UI
    - Thread-safe parameter updates during client execution
    - Comprehensive logging integration with visual feedback

Architecture:
    - Inherits from BaseInstanceWidget for common functionality
    - Uses FormFieldFactory for consistent widget creation
    - Implements Observer pattern with Qt signals for state changes
    - Provides callback-based parameter updates for running clients
    - Integrates validation system for input field management

UI Components:
    - Host configuration with validation
    - HTTP method selection via radio buttons
    - Request route and payload editors with template support
    - Timing configuration (delays, periods)
    - Flag configuration (autostart, loop mode)
    - Start/Stop control with visual state feedback
    - Real-time logging output display

Classes:
    - ClientInstanceWidget: Main widget for client instance management

Dependencies:
    - PySide6: Qt framework for GUI components
    - BaseInstanceWidget: Common instance widget functionality
    - FormFieldFactory: Consistent widget creation patterns
    - validate: Input validation and formatting utilities
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QLineEdit, QCheckBox, QHBoxLayout, QTextEdit, 
    QRadioButton, QPushButton
)
from PySide6.QtCore import Signal, Qt
from .validate import validate_and_format_qedit, on_edit_qedit, on_focus_qedit
from .base_instance_widget import BaseInstanceWidget
from .form_field_factory import CommonFieldBuilder, FormFieldFactory


class ClientInstanceWidget(BaseInstanceWidget):
    """
    Graphical user interface widget for REST client instance management.
    
    This widget provides a comprehensive interface for configuring and controlling
    HTTP client instances. It supports real-time parameter updates, dynamic state
    management, and seamless integration with the client management system through
    Qt's signal-slot mechanism.
    
    The widget implements a factory-based approach for UI creation, ensuring
    consistency across different instance types while providing client-specific
    functionality including HTTP method selection, request configuration,
    and timing parameters.
    
    Key Features:
        - Dynamic parameter updates for running clients
        - Visual state management with start/stop controls
        - Comprehensive validation for all input fields
        - Real-time logging display integration
        - Template-based request configuration
        - Thread-safe parameter updates during execution
        
    Signals:
        start_requested(object): Emitted when client start is requested
        stop_requested(object): Emitted when client stop is requested
        params_changed(object, dict): Emitted when parameters change during execution
        
    Attributes:
        client: The client instance model this widget manages
        Various UI elements for configuration and control
    """
    
    # Additional client-specific signals beyond base class
    start_requested = Signal(object)  # object = client_instance
    stop_requested = Signal(object)   # object = client_instance
    params_changed = Signal(object, dict)  # object = client_instance, dict = changed params
    
    def __init__(self, client_instance) -> None:
        """
        Initialize client widget with instance model.
        
        Args:
            client_instance: The client model object to manage
            
        Note:
            Client instance must be set before calling super().__init__()
            to ensure proper initialization order for UI setup.
        """
        self.client = client_instance  # Set before calling super()
        super().__init__(client_instance)
    
    def _setup_instance_ui(self) -> None:
        """
        Setup client-specific UI elements.
        
        This method is called by the base class during initialization
        to create the client-specific configuration interface.
        """
        self._setup_config_ui()
    
    def _connect_signals(self) -> None:
        """
        Connect client-specific signals.
        
        This method provides a hook for connecting additional signals
        beyond those handled by the base class. Currently placeholder
        for future client-specific signal connections.
        """
        # Client-specific signal connections will be added here
        pass
    
    def start_instance(self) -> None:
        """
        Request start of the client instance.
        
        Emits the start_requested signal to notify the management
        system that this client should be started.
        """
        self.start_requested.emit(self.client)
    
    def stop_instance(self) -> None:
        """
        Request stop of the client instance.
        
        Emits the stop_requested signal to notify the management
        system that this client should be stopped.
        """
        self.stop_requested.emit(self.client)
    
    def _update_ui_state(self) -> None:
        """
        Update UI elements based on current running state.
        
        This method coordinates UI state changes including button
        styling and field enablement based on whether the client
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
        
        This method creates all necessary UI elements for client configuration
        including host settings, timing parameters, HTTP methods, request
        configuration, and control buttons. It uses the factory pattern
        for consistent widget creation and integrates validation callbacks.
        
        UI Components Created:
            - Host field with validation
            - Autostart and loop flag checkboxes
            - Initial delay and period timing fields
            - Route field with template support
            - HTTP method radio button group
            - Request payload editor with template support
            - Start/Stop toggle button with state styling
            
        Signal Connections:
            All relevant fields are connected to change handlers that
            support real-time parameter updates for running clients.
        """
        builder = CommonFieldBuilder(self.client, self.form_layout)
        
        # Host field with validation
        builder.add_host_field(self.client.get_value('host'))
        
        # Flags configuration (autostart and loop)
        flags_config = [
            ('autostart', 'Autostart', self.client.get_value('autostart')),
            ('loop', 'Loop', self.client.get_value('loop'))
        ]
        layout, checkboxes = FormFieldFactory.create_flags_layout(self.client, flags_config)
        self.form_layout.addRow("Flags", layout)
        self.autostart_box = checkboxes['autostart']
        self.loop_box = checkboxes['loop']
        
        # Timing configuration fields
        builder.add_initial_delay_field(self.client.get_value('initial_delay_sec'))
        builder.add_period_field(self.client.get_value('period_sec'))
        
        # Route field with real-time update support
        self.route_edit = builder.add_route_field(self.client.get_value('route'))
        self.route_edit.textChanged.connect(lambda: self._on_route_changed())
        
        # Period field with real-time update support
        self.period_edit = builder.fields['period']
        self.period_edit.textChanged.connect(lambda: self._on_period_changed())
        
        # HTTP method radio button group
        layout, radio_buttons = FormFieldFactory.create_radio_group(
            self.client, 'methode', self.client.server_methods, 
            self.client.get_value('methode'), self._on_method_changed
        )
        self.form_layout.addRow("Methode", layout)
        self.methode_checks = radio_buttons
        
        # Request payload editor with template support
        self.request_edit = builder.add_request_field(
            self.client.get_value('request') if self.client.get_value('request') else ""
        )
        self.request_edit.textChanged.connect(lambda: self._on_request_changed())
        
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
    
    def _on_toggle_clicked(self) -> None:
        """
        Handle start/stop toggle button click events.
        
        This method determines the current state and emits the appropriate
        signal to either start or stop the client instance. The actual
        state management is handled by the parent management system.
        """
        if self.is_running:
            self.stop_requested.emit(self.client)
        else:
            self.start_requested.emit(self.client)

    def _update_button_style(self) -> None:
        """
        Update toggle button styling based on current running state.
        
        Provides visual feedback for the current client state:
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

    def _on_period_changed(self) -> None:
        """
        Handle period field changes with real-time updates.
        
        This method processes period changes and applies them immediately
        to running clients. It validates the input and emits parameter
        change signals for live client update.
        
        Validation:
            - Applies standard validation through validation system
            - Converts to float for numeric validation
            - Ignores invalid values to prevent client disruption
        """
        on_edit_qedit(self.client, self.period_edit, 'period_sec')
        if self.is_running:
            try:
                period_sec = float(self.period_edit.text())
                self.params_changed.emit(self.client, {'period_sec': period_sec})
            except ValueError:
                pass  # Ignore invalid values during live editing

    def _on_route_changed(self) -> None:
        """
        Handle route field changes with real-time updates.
        
        This method processes route template changes and applies them
        immediately to running clients. The route supports Jinja2
        templating for dynamic URL generation.
        """
        on_edit_qedit(self.client, self.route_edit, 'route')
        if self.is_running:
            route = self.route_edit.text()
            self.params_changed.emit(self.client, {'route': route})

    def _on_method_changed(self, method: str, checked: bool) -> None:
        """
        Handle HTTP method selection changes.
        
        Args:
            method: The HTTP method that was selected
            checked: Whether the radio button is now checked
            
        This method updates the client model and applies changes
        immediately to running clients for real-time testing.
        """
        if checked:
            self.client.set_value('methode', method)
            if self.is_running:
                self.params_changed.emit(self.client, {'method': method})

    def _on_request_changed(self) -> None:
        """
        Handle request payload changes with real-time updates.
        
        This method processes request payload template changes and
        applies them immediately to running clients. The payload
        supports Jinja2 templating for dynamic content generation.
        """
        on_edit_qedit(self.client, self.request_edit, 'request')
        if self.is_running:
            request_data = self.request_edit.toPlainText()
            self.params_changed.emit(self.client, {'request_data': request_data})
    
    def set_running(self, running: bool) -> None:
        """
        Set the running state and update UI accordingly.
        
        Args:
            running: True if client is running, False if stopped
            
        This method calls the base class implementation and ensures
        proper UI state management across the widget hierarchy.
        """
        super().set_running(running)  # Call base class method
    
    def lock_fields(self) -> None:
        """
        Lock configuration fields when client is running.
        
        This method disables fields that cannot be changed during
        client execution, while keeping fields enabled that support
        real-time updates (route, method, request, period).
        
        Locked Fields:
            - Host configuration (requires restart)
            - Autostart flag (initialization parameter)
            - Loop flag (affects execution mode)
            - Initial delay (startup parameter)
            
        Unlocked Fields:
            - Route (supports real-time updates)
            - HTTP method (supports real-time updates)
            - Request payload (supports real-time updates)
            - Period timing (supports real-time updates)
        """
        self.host_edit.setEnabled(False)
        self.autostart_box.setEnabled(False)
        self.loop_box.setEnabled(False)
        self.initial_delay_edit.setEnabled(False)
        # Route, Method, Request and Period remain unlocked for dynamic updates
        
    def unlock_fields(self) -> None:
        """
        Unlock all configuration fields when client is stopped.
        
        This method re-enables all configuration fields when the client
        is not running, allowing full reconfiguration of the client
        instance before the next execution.
        """
        self.host_edit.setEnabled(True)
        self.autostart_box.setEnabled(True)
        self.loop_box.setEnabled(True)
        self.initial_delay_edit.setEnabled(True)
    
    def get_log_signal_handler(self):
        """
        Get the log signal handler for this client instance.
        
        Returns:
            The signal handler object for integrating with the logging system
            
        This method provides access to the logging signal handler for
        this specific client instance, enabling targeted log output
        and monitoring capabilities.
        """
        return self.log_widget.get_signal_handler()