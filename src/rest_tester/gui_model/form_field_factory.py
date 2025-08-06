"""
Form Field Factory for GUI Widget Creation

This module implements the Factory Pattern for creating consistent GUI form
fields with integrated validation, reducing code duplication across the
application's GUI components.

Key Features:
    - Consistent widget creation with validation setup
    - Automatic data binding and signal connections
    - Reusable field types (text, textarea, checkbox, radio, etc.)
    - Builder pattern for complex form construction
    - Centralized styling and behavior management

Design Patterns:
    - Factory Pattern: For widget creation
    - Builder Pattern: For complex form assembly
    - Observer Pattern: For data binding and validation

Architecture Benefits:
    - Eliminates code duplication across GUI classes
    - Ensures consistent validation behavior
    - Simplifies widget lifecycle management
    - Enables easy styling and behavior changes
"""

from PySide6.QtWidgets import (
    QLineEdit, QCheckBox, QHBoxLayout, QTextEdit, 
    QRadioButton, QButtonGroup, QFormLayout
)
from PySide6.QtCore import Qt
from .validate import validate_and_format_qedit, on_edit_qedit, on_focus_qedit


class FormFieldFactory:
    """
    Factory class for creating GUI form fields with consistent validation.
    
    This factory encapsulates the common patterns for creating form widgets
    with proper validation setup and data binding. It ensures all widgets
    follow the same patterns for error handling and user interaction.
    
    Design Notes:
        - All created widgets include automatic validation setup
        - Data binding is established through adapter pattern
        - Signal connections are configured for real-time validation
        - Focus handling provides immediate feedback to users
    """
    
    @staticmethod
    def create_text_field(adapter, field_name: str, default_value: str = "", placeholder: str = "") -> QLineEdit:
        """
        Create a validated text input field.
        
        Creates a QLineEdit with comprehensive validation setup including
        real-time validation on text changes and focus events.
        
        Args:
            adapter: Data adapter for value management and validation
            field_name: Field identifier for validation and data binding
            default_value: Initial field value
            placeholder: Placeholder text for user guidance
            
        Returns:
            QLineEdit: Configured text input widget
            
        Features:
            - Real-time validation on text changes
            - Focus-out validation with error highlighting
            - Automatic formatting based on field type
            - Placeholder text for user guidance
        """
        field = QLineEdit(str(default_value))
        if placeholder:
            field.setPlaceholderText(placeholder)
            
        # Setup validation framework integration
        validate_and_format_qedit(adapter, field, field_name)
        field.textChanged.connect(lambda: on_edit_qedit(adapter, field, field_name))
        field.focusOutEvent = lambda event: on_focus_qedit(adapter, field, field_name, event)
        
        return field
    
    @staticmethod
    def create_text_area(adapter, field_name: str, default_value: str = "", min_height: int = 70) -> QTextEdit:
        """
        Create a validated multi-line text area.
        
        Creates a QTextEdit suitable for larger text content like JSON
        data or multi-line configuration values.
        
        Args:
            adapter: Data adapter for value management
            field_name: Field identifier for validation
            default_value: Initial content
            min_height: Minimum widget height in pixels
            
        Returns:
            QTextEdit: Configured text area widget
            
        Features:
            - Multi-line text support
            - Scrollbars for overflow content
            - Same validation framework as text fields
            - Configurable minimum height
        """
        field = QTextEdit(str(default_value))
        field.setMinimumHeight(min_height)
        field.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        field.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Apply same validation framework as text fields
        validate_and_format_qedit(adapter, field, field_name)
        field.textChanged.connect(lambda: on_edit_qedit(adapter, field, field_name))
        field.focusOutEvent = lambda event: on_focus_qedit(adapter, field, field_name, event)
        
        return field
    
    @staticmethod
    def create_checkbox(adapter, field_name: str, label: str, default_value: bool = False) -> QCheckBox:
        """
        Create a checkbox with automatic data binding.
        
        Creates a QCheckBox that automatically updates the underlying
        data model when the user changes its state.
        
        Args:
            adapter: Data adapter for value management
            field_name: Field identifier for data binding
            label: Display text for the checkbox
            default_value: Initial checked state
            
        Returns:
            QCheckBox: Configured checkbox widget
            
        Features:
            - Automatic data binding on state changes
            - Immediate model updates
            - Consistent styling with other form elements
        """
        checkbox = QCheckBox(label)
        checkbox.setChecked(bool(default_value))
        checkbox.stateChanged.connect(
            lambda checked: adapter.set_value(field_name, bool(checked))
        )
        return checkbox
    
    @staticmethod
    def create_flags_layout(adapter, flags_config: list) -> tuple:
        """
        Create horizontal layout with multiple flag checkboxes.
        
        Builds a horizontal layout containing multiple checkboxes for
        boolean flags, commonly used for feature toggles and options.
        
        Args:
            adapter: Data adapter for value management
            flags_config: List of tuples [(field_name, label, default_value), ...]
            
        Returns:
            tuple: (QHBoxLayout, dict) - layout and checkbox widgets by field name
            
        Example:
            flags = [('autostart', 'Autostart', False), ('loop', 'Loop', True)]
            layout, checkboxes = create_flags_layout(adapter, flags)
        """
        layout = QHBoxLayout()
        checkboxes = {}
        
        for field_name, label, default_value in flags_config:
            checkbox = FormFieldFactory.create_checkbox(adapter, field_name, label, default_value)
            layout.addWidget(checkbox)
            checkboxes[field_name] = checkbox
            
        return layout, checkboxes
    
    @staticmethod
    def create_radio_group(adapter, field_name: str, options: list, current_value: str, on_change_callback=None) -> tuple:
        """
        Create horizontal radio button group for exclusive selection.
        
        Builds a group of radio buttons where only one option can be
        selected at a time, commonly used for method selection or
        mutually exclusive options.
        
        Args:
            adapter: Data adapter for value management
            field_name: Field identifier for data binding
            options: List of available option values
            current_value: Currently selected value
            on_change_callback: Optional callback for selection changes
            
        Returns:
            tuple: (QHBoxLayout, list) - layout and radio button widgets
            
        Features:
            - Exclusive selection (only one can be checked)
            - Automatic data binding on selection changes
            - Optional custom change callbacks
            - Horizontal layout for compact display
        """
        layout = QHBoxLayout()
        radio_buttons = []
        
        for option in options:
            radio = QRadioButton(option)
            radio.setChecked(option == current_value)
            
            # Create closure to capture option value correctly
            def make_callback(opt):
                def callback(checked):
                    if checked:
                        adapter.set_value(field_name, opt)
                        if on_change_callback:
                            on_change_callback(opt, checked)
                return callback
            
            radio.toggled.connect(make_callback(option))
            layout.addWidget(radio)
            radio_buttons.append(radio)
            
        return layout, radio_buttons
    
    @staticmethod
    def create_checkbox_group(adapter, field_name: str, options: list, current_values: list, on_change_callback=None) -> tuple:
        """
        Create horizontal checkbox group for multiple selections.
        
        Builds a group of checkboxes where multiple options can be
        selected simultaneously, commonly used for HTTP methods or
        feature selections.
        
        Args:
            adapter: Data adapter for value management
            field_name: Field identifier for data binding
            options: List of available option values
            current_values: List of currently selected values
            on_change_callback: Optional callback for selection changes
            
        Returns:
            tuple: (QHBoxLayout, QButtonGroup, dict) - layout, button group, and checkboxes
            
        Features:
            - Multiple simultaneous selections
            - Automatic list management in data model
            - Custom change callbacks with selected values
            - Button group for coordinated management
        """
        layout = QHBoxLayout()
        button_group = QButtonGroup()
        button_group.setExclusive(False)  # Allow multiple selections
        checkboxes = {}
        
        for option in options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(option in current_values)
            button_group.addButton(checkbox)
            layout.addWidget(checkbox)
            checkboxes[option] = checkbox
        
        def on_button_toggled():
            """Handle checkbox state changes and update model."""
            selected = [opt for opt, cb in checkboxes.items() if cb.isChecked()]
            adapter.set_value(field_name, selected)
            if on_change_callback:
                on_change_callback(selected)
        
        button_group.buttonToggled.connect(on_button_toggled)
        return layout, button_group, checkboxes


class CommonFieldBuilder:
    """
    Builder class for constructing common form field patterns.
    
    This builder provides high-level methods for creating frequently used
    form fields with appropriate validation and styling. It simplifies
    the creation of standard forms by encapsulating common patterns.
    
    Attributes:
        adapter: Data adapter for all created fields
        form_layout: Target form layout for field placement
        fields: Dictionary tracking created fields by name
        
    Usage:
        builder = CommonFieldBuilder(adapter, form_layout)
        builder.add_host_field(default_host)
        builder.add_route_field(default_route)
        # Access created fields via builder.fields['host']
    """
    
    def __init__(self, adapter, form_layout: QFormLayout):
        """
        Initialize builder with target adapter and layout.
        
        Args:
            adapter: Data adapter for field management
            form_layout: QFormLayout to add fields to
        """
        self.adapter = adapter
        self.form_layout = form_layout
        self.fields = {}  # Track created fields for later access
    
    def add_host_field(self, default_value: str = "", placeholder: str = "localhost:8080") -> QLineEdit:
        """Add host input field with network validation."""
        field = FormFieldFactory.create_text_field(
            self.adapter, 'host', default_value, placeholder
        )
        self.form_layout.addRow("Host", field)
        self.fields['host'] = field
        return field
    
    def add_route_field(self, default_value: str = "", placeholder: str = "/api/endpoint") -> QLineEdit:
        """Add route input field with URL validation."""
        field = FormFieldFactory.create_text_field(
            self.adapter, 'route', default_value, placeholder
        )
        self.form_layout.addRow("Route", field)
        self.fields['route'] = field
        return field
    
    def add_initial_delay_field(self, default_value: float = 0.0) -> QLineEdit:
        """Add initial delay field with numeric validation."""
        field = FormFieldFactory.create_text_field(
            self.adapter, 'initial_delay_sec', str(default_value), "0.0"
        )
        self.form_layout.addRow("Initial Delay (s)", field)
        self.fields['initial_delay'] = field
        return field
    
    def add_response_delay_field(self, default_value: float = 0.0) -> QLineEdit:
        """Add response delay field with numeric validation."""
        field = FormFieldFactory.create_text_field(
            self.adapter, 'response_delay_sec', str(default_value), "0.0"
        )
        self.form_layout.addRow("Response Delay (s)", field)
        self.fields['response_delay'] = field
        return field
    
    def add_period_field(self, default_value: float = 1.0) -> QLineEdit:
        """Add period field for client timing configuration."""
        field = FormFieldFactory.create_text_field(
            self.adapter, 'period_sec', str(default_value), "1.0"
        )
        self.form_layout.addRow("Period (s)", field)
        self.fields['period'] = field
        return field
    
    def add_common_flags(self, autostart_default: bool = False, loop_default: bool = False) -> tuple:
        """Add common boolean flags (autostart, loop if applicable)."""
        flags_config = [('autostart', 'Autostart', autostart_default)]
        
        # Conditionally add loop flag based on adapter capabilities
        if hasattr(self.adapter, 'get_value') and self._supports_loop():
            flags_config.append(('loop', 'Loop', loop_default))
        
        layout, checkboxes = FormFieldFactory.create_flags_layout(self.adapter, flags_config)
        self.form_layout.addRow("Flags", layout)
        self.fields.update(checkboxes)
        return layout, checkboxes
    
    def add_request_field(self, default_value: str = "", min_height: int = 120) -> QTextEdit:
        """Add request text area for client configuration."""
        field = FormFieldFactory.create_text_area(
            self.adapter, 'request', default_value, min_height
        )
        self.form_layout.addRow("Request", field)
        self.fields['request'] = field
        return field
    
    def add_response_field(self, default_value: str = "", min_height: int = 70) -> QTextEdit:
        """Add response text area for server configuration."""
        field = FormFieldFactory.create_text_area(
            self.adapter, 'response', default_value, min_height
        )
        self.form_layout.addRow("Response", field)
        self.fields['response'] = field
        return field
    
    def add_methods_checkboxes(self, available_methods: list, current_methods: list, on_change_callback=None) -> tuple:
        """Add HTTP methods checkbox group for server configuration."""
        layout, button_group, checkboxes = FormFieldFactory.create_checkbox_group(
            self.adapter, 'methodes', available_methods, current_methods, on_change_callback
        )
        self.form_layout.addRow("Methods", layout)
        self.fields['methods_group'] = button_group
        self.fields['methods_checkboxes'] = checkboxes
        return layout, button_group, checkboxes
    
    def add_method_radio(self, available_methods: list, current_method: str, on_change_callback=None) -> tuple:
        """Add HTTP method radio group for client configuration."""
        layout, radio_buttons = FormFieldFactory.create_radio_group(
            self.adapter, 'methode', available_methods, current_method, on_change_callback
        )
        self.form_layout.addRow("Method", layout)
        self.fields['method_radios'] = radio_buttons
        return layout, radio_buttons
    
    def _supports_loop(self) -> bool:
        """Check if adapter supports loop functionality."""
        # Simple heuristic to determine if loop is supported
        try:
            return hasattr(self.adapter, 'defaults') and 'loop' in str(self.adapter.defaults)
        except:
            return False
