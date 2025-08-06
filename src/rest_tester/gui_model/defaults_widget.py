"""
Default Values Configuration Widget Module

This module implements the graphical user interface for managing default configuration
values for REST server and client instances. It provides a unified interface for
editing global defaults that serve as templates for new instances, reducing
configuration redundancy and ensuring consistency across the application.

Key Features:
    - Unified interface for server and client default configuration
    - Adapter pattern for seamless integration with validation system
    - Factory-pattern widget creation for consistent UI elements
    - Real-time default value updates with signal notifications
    - Type validation and conversion for numeric fields
    - Change detection against initial default values
    - Transparent styling for seamless UI integration

Architecture:
    - DefaultsAdapter: Adapter pattern for validation system compatibility
    - DefaultsWidget: Main widget for default value editing
    - Uses FormFieldFactory for consistent widget creation
    - Implements signal-based change notifications
    - Integrates with ConfigModel for persistent storage

UI Components:
    - Server defaults: Host, route, methods, response template, timing
    - Client defaults: Host, route, method, request template, timing, flags
    - Validation and formatting for all input fields
    - Consistent styling with instance configuration widgets

Classes:
    - DefaultsAdapter: Validation system compatibility adapter
    - DefaultsWidget: Main default values configuration widget

Dependencies:
    - PySide6: Qt framework for GUI components
    - FormFieldFactory: Consistent widget creation patterns
    - validate: Input validation and formatting utilities
"""

from typing import Dict, List, Any, Union
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QCheckBox, QHBoxLayout, 
    QTextEdit, QGroupBox, QVBoxLayout, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from .validate import validate_and_format_qedit, on_edit_qedit, on_focus_qedit
from .form_field_factory import CommonFieldBuilder, FormFieldFactory


class DefaultsAdapter:
    """
    Adapter class for defaults configuration compatibility with validation system.
    
    This adapter implements the Adapter pattern to make the DefaultsWidget
    compatible with the existing validation functions that expect instance-like
    objects with get_value, set_value, and related methods.
    
    The adapter manages the relationship between UI changes and the underlying
    defaults dictionary, providing change detection and type conversion for
    numeric fields.
    
    Attributes:
        widget (DefaultsWidget): Reference to the parent widget
        defaults (Dict): Current default values being edited
        initial_defaults (Dict): Original default values for change detection
        
    Methods:
        - get_value: Retrieve current default value
        - set_value: Update default value with type conversion
        - get_default: Retrieve original default value
        - is_default: Check if value has been modified
    """
    
    def __init__(self, defaults_widget, defaults_dict: Dict[str, Any]) -> None:
        """
        Initialize adapter with widget reference and defaults dictionary.
        
        Args:
            defaults_widget: The parent DefaultsWidget instance
            defaults_dict: Dictionary of default values to manage
        """
        self.widget = defaults_widget
        self.defaults = defaults_dict
        self.initial_defaults = defaults_dict.copy()  # Store initial defaults for comparison
        
    def get_value(self, key: str) -> Any:
        """
        Get current default value for specified key.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Current default value, or empty string if not found
        """
        return self.defaults.get(key, "")
    
    def get_default(self, key: str) -> Any:
        """
        Get original default value for specified key.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Original default value from initial load
        """
        return self.initial_defaults.get(key, "")

    def set_value(self, key: str, value: Any) -> None:
        """
        Set default value with automatic type conversion and change notification.
        
        This method updates the defaults dictionary and applies appropriate
        type conversion for numeric fields. It emits change signals to
        notify the UI of modifications.
        
        Args:
            key: Configuration key to update
            value: New value to set
            
        Type Conversion:
            Numeric fields (delays, periods) are automatically converted
            to float values with validation.
        """
        # Convert numeric values appropriately
        if key in ['initial_delay_sec', 'response_delay_sec', 'period_sec']:
            try:
                value = float(value)
            except (ValueError, TypeError):
                return
        
        self.defaults[key] = value
        self.widget.defaults_changed.emit()
        
    def is_default(self, key: str) -> bool:
        """
        Check if current value matches original default.
        
        Args:
            key: Configuration key to check
            
        Returns:
            True if value unchanged, False if modified
        """
        return self.defaults.get(key) == self.initial_defaults.get(key)


class DefaultsWidget(QWidget):
    """
    Widget for editing default configuration values for server or client instances.
    
    This widget provides a comprehensive interface for managing global default
    values that serve as templates for new instances. It uses the factory pattern
    for consistent widget creation and integrates seamlessly with the validation
    system through the adapter pattern.
    
    The widget automatically adjusts its interface based on whether it's managing
    server or client defaults, providing appropriate fields and validation for
    each instance type.
    
    Key Features:
        - Dynamic interface based on server/client type
        - Real-time validation and formatting
        - Change notifications for configuration updates
        - Consistent styling with transparent group box
        - Factory-pattern widget creation
        - Type conversion for numeric fields
        
    Signals:
        defaults_changed: Emitted when any default value is modified
        
    Attributes:
        config: Configuration model reference
        is_server (bool): True for server defaults, False for client defaults
        defaults (Dict): Dictionary of default values being edited
        adapter (DefaultsAdapter): Validation system compatibility adapter
    """
    
    defaults_changed = Signal()  # Signal when defaults are modified
    
    def __init__(self, config, is_server: bool = True) -> None:
        """
        Initialize defaults widget for server or client configuration.
        
        Args:
            config: Configuration model containing default values
            is_server: True for server defaults, False for client defaults
            
        UI Setup:
            - Creates transparent group box for seamless integration
            - Sets fixed height for consistent layout
            - Initializes adapter for validation system compatibility
        """
        super().__init__()
        self.config = config
        self.is_server = is_server
        self.defaults = config.raw['defaults']['server'] if is_server else config.raw['defaults']['client']
        
        # Create adapter for validation functions
        self.adapter = DefaultsAdapter(self, self.defaults)
        
        # Create group box with appropriate title
        title = "Server Defaults" if is_server else "Client Defaults"
        self.group_box = QGroupBox(title)

        # Transparent styling for seamless UI integration
        self.group_box.setStyleSheet("""
            QGroupBox {
                background-color: transparent; 
                font-weight: normal;
                color: palette(text);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 0px 0 0px;
                background-color: transparent;
            }
        """)

        # Set minimum height for consistent layout
        self.setFixedHeight(300)
        
        # Main layout structure
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)
        
        # Form layout inside group box
        self.layout = QFormLayout(self.group_box)
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """
        Create form widgets based on server or client type.
        
        This method delegates to the appropriate widget creation method
        based on the instance type, ensuring the correct interface is
        presented for server or client default configuration.
        """
        if self.is_server:
            self._create_server_widgets()
        else:
            self._create_client_widgets()
            
    def _create_server_widgets(self) -> None:
        """
        Create widgets for server defaults using FormFieldFactory.
        
        This method creates all necessary UI elements for server default
        configuration including host, timing, methods, route, and response
        template fields. It uses the factory pattern for consistent creation.
        
        Server-Specific Fields:
            - Host: Server address and port configuration
            - Autostart: Whether servers start automatically
            - Initial delay: Delay before server startup
            - Response delay: Delay before sending responses
            - Route: Default endpoint route pattern
            - Methods: Supported HTTP methods (checkbox group)
            - Response: Default Jinja2 response template
        """
        builder = CommonFieldBuilder(self.adapter, self.layout)
        
        # Host field with validation
        builder.add_host_field(self.defaults.get('host', ''))
        
        # Flags configuration (only autostart for server)
        flags_config = [('autostart', 'Autostart', self.defaults.get('autostart', False))]
        layout, checkboxes = FormFieldFactory.create_flags_layout(self.adapter, flags_config)
        self.layout.addRow("Flags", layout)
        self.autostart_box = checkboxes['autostart']
        
        # Timing configuration fields
        builder.add_initial_delay_field(self.defaults.get('initial_delay_sec', 0.0))
        builder.add_response_delay_field(self.defaults.get('response_delay_sec', 0.0))
        
        # Route field for endpoint configuration
        builder.add_route_field(self.defaults.get('route', ''))
        
        # HTTP methods checkbox group
        available_methods = ["GET", "POST"]
        current_methods = self.defaults.get('methodes', [])
        layout, button_group, checkboxes = builder.add_methods_checkboxes(
            available_methods, current_methods, self._on_methods_changed
        )
        self.methods_group = button_group
        
        # Response template field
        builder.add_response_field(self.defaults.get('response', ''))
        
        # Store field references for compatibility
        self.host_edit = builder.fields['host']
        self.initial_delay_edit = builder.fields['initial_delay']
        self.response_delay_edit = builder.fields['response_delay']
        self.route_edit = builder.fields['route']
        self.response_edit = builder.fields['response']

    def _create_client_widgets(self) -> None:
        """
        Create widgets for client defaults using FormFieldFactory.
        
        This method creates all necessary UI elements for client default
        configuration including host, timing, method, route, and request
        template fields. It uses the factory pattern for consistent creation.
        
        Client-Specific Fields:
            - Host: Target server address and port
            - Autostart: Whether clients start automatically
            - Loop: Whether clients continuously send requests
            - Initial delay: Delay before first request
            - Period: Interval between requests in loop mode
            - Route: Default request route template
            - Method: Default HTTP method (radio group)
            - Request: Default Jinja2 request template
        """
        builder = CommonFieldBuilder(self.adapter, self.layout)
        
        # Host field with validation
        builder.add_host_field(self.defaults.get('host', ''))
        
        # Flags configuration (autostart and loop for client)
        flags_config = [
            ('autostart', 'Autostart', self.defaults.get('autostart', False)),
            ('loop', 'Loop', self.defaults.get('loop', False))
        ]
        layout, checkboxes = FormFieldFactory.create_flags_layout(self.adapter, flags_config)
        self.layout.addRow("Flags", layout)
        self.autostart_box = checkboxes['autostart']
        self.loop_box = checkboxes['loop']
        
        # Timing configuration fields
        builder.add_initial_delay_field(self.defaults.get('initial_delay_sec', 0.0))
        builder.add_period_field(self.defaults.get('period_sec', 1.0))
        
        # Route field for request configuration
        builder.add_route_field(self.defaults.get('route', ''))
        
        # HTTP method radio group for single method selection
        available_methods = ["GET", "POST"]
        current_method = self.defaults.get('methode', 'GET')
        layout, radio_buttons = FormFieldFactory.create_radio_group(
            self.adapter, 'methode', available_methods, current_method, self._on_method_changed
        )
        self.layout.addRow("Methode", layout)
        self.methode_checks = radio_buttons
        
        # Request template field
        builder.add_request_field(self.defaults.get('request', ''))
        
        # Store field references for compatibility
        self.host_edit = builder.fields['host']
        self.initial_delay_edit = builder.fields['initial_delay']
        self.period_edit = builder.fields['period']
        self.route_edit = builder.fields['route']
        self.request_edit = builder.fields['request']
        
    def _on_methods_changed(self, selected_methods: List[str]) -> None:
        """
        Handle changes to HTTP methods selection for server defaults.
        
        Args:
            selected_methods: List of currently selected HTTP methods
            
        This method ensures that at least one method is always selected
        for server defaults and updates the configuration accordingly.
        
        Validation:
            - Ensures at least one method is always selected
            - Automatically selects first available method if none selected
            - Updates defaults through adapter with change notification
        """
        # Ensure at least one method is selected for server functionality
        if not selected_methods:
            # Re-check first available method if none selected
            if hasattr(self, 'methods_group') and self.methods_group.buttons():
                first_button = self.methods_group.buttons()[0]
                first_button.setChecked(True)
                selected_methods = [first_button.text()]
        
        # Update defaults through adapter
        self.adapter.set_value('methodes', selected_methods)
    
    def _on_method_changed(self, method: str, checked: bool) -> None:
        """
        Handle changes to HTTP method selection for client defaults.
        
        Args:
            method: The HTTP method that was selected
            checked: Whether the radio button is now checked
            
        This method updates the default HTTP method for client instances
        when a radio button selection changes.
        """
        if checked:
            self.adapter.set_value('methode', method)

    def get_defaults(self) -> Dict[str, Any]:
        """
        Retrieve current default values dictionary.
        
        Returns:
            Dictionary containing current default values for the instance type
            
        This method provides access to the underlying defaults dictionary
        which is synchronized with the UI elements through the adapter pattern.
        It's typically used when saving configuration or validating complete
        default configurations.
        """
        return self.defaults
    
    def update_display(self) -> None:
        """
        Refresh all UI elements to reflect current defaults values.
        
        This method synchronizes the UI display with the underlying defaults
        dictionary, ensuring that any programmatic changes to the defaults
        are reflected in the user interface. It's particularly useful after
        loading new configuration data or resetting defaults.
        
        The method handles both server and client types, updating all relevant
        fields including timing, routing, methods, and template configurations.
        """
        # Update all fields through the adapter to maintain consistency
        if self.is_server:
            self._update_server_display()
        else:
            self._update_client_display()
    
    def _update_server_display(self) -> None:
        """
        Update server-specific UI elements from current defaults.
        
        This internal method refreshes all server-related UI elements
        with their corresponding values from the defaults dictionary.
        It ensures proper type conversion and validation during the update.
        """
        # Update text fields with validation
        self.host_edit.setText(self.defaults.get('host', ''))
        self.initial_delay_edit.setText(str(self.defaults.get('initial_delay_sec', 0.0)))
        self.response_delay_edit.setText(str(self.defaults.get('response_delay_sec', 0.0)))
        self.route_edit.setText(self.defaults.get('route', ''))
        self.response_edit.setPlainText(self.defaults.get('response', ''))
        
        # Update flags
        self.autostart_box.setChecked(self.defaults.get('autostart', False))
        
        # Update methods checkboxes
        current_methods = self.defaults.get('methodes', [])
        for button in self.methods_group.buttons():
            method_name = button.text()
            button.setChecked(method_name in current_methods)
    
    def _update_client_display(self) -> None:
        """
        Update client-specific UI elements from current defaults.
        
        This internal method refreshes all client-related UI elements
        with their corresponding values from the defaults dictionary.
        It ensures proper type conversion and validation during the update.
        """
        # Update text fields with validation
        self.host_edit.setText(self.defaults.get('host', ''))
        self.initial_delay_edit.setText(str(self.defaults.get('initial_delay_sec', 0.0)))
        self.period_edit.setText(str(self.defaults.get('period_sec', 1.0)))
        self.route_edit.setText(self.defaults.get('route', ''))
        self.request_edit.setPlainText(self.defaults.get('request', ''))
        
        # Update flags
        self.autostart_box.setChecked(self.defaults.get('autostart', False))
        self.loop_box.setChecked(self.defaults.get('loop', False))
        
        # Update method radio buttons
        current_method = self.defaults.get('methode', 'GET')
        for method_name, radio_button in self.methode_checks.items():
            radio_button.setChecked(method_name == current_method)

