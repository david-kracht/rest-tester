"""
UI Validation Integration Layer

This module serves as the bridge between the centralized validation service
and GUI components, providing seamless integration of validation logic with
Qt widgets while maintaining proper separation of concerns.

Key Features:
    - Real-time validation feedback for form fields
    - Visual styling based on validation state
    - Integration with logging system for validation errors
    - Support for both QLineEdit and QTextEdit widgets
    - Automatic default value detection and styling

Architecture:
    Acts as an Adapter between the ValidationService and Qt widgets,
    translating validation results into appropriate UI feedback and
    maintaining consistency across all form components.

Design Pattern:
    Implements the Adapter pattern to bridge validation service
    with Qt widget system, using Singleton pattern for service access.
"""

from typing import Any
from PySide6.QtWidgets import QLineEdit, QTextEdit

from ..core.validation_service import ValidationService
from ..service.logging_config import get_logger


# Singleton validation service instance for consistent validation behavior
_validation_service = ValidationService()
_logger = get_logger("UIValidation")


def validate_and_format_qedit(instance: Any, widget, field_key: str) -> bool:
    """
    Validate widget content and apply appropriate visual formatting.
    
    This function performs comprehensive validation of GUI widget content
    using the centralized validation service and applies visual feedback
    to help users understand the validation state.
    
    Args:
        instance: Data model instance with get_default() and is_default() methods
        widget: Qt widget to validate (QLineEdit or QTextEdit)
        field_key: Field identifier for validation type determination
        
    Returns:
        bool: True if content is valid, False otherwise
        
    Features:
        - Automatic widget type detection
        - Centralized validation using ValidationService
        - Visual styling based on validation state
        - Error logging for debugging
        - Default value detection for appropriate styling
    """
    # Extract text content based on widget type
    if isinstance(widget, QLineEdit):
        text = widget.text()
    elif isinstance(widget, QTextEdit):
        text = widget.toPlainText()
    else:
        _logger.error(f"Unsupported widget type for validation: {type(widget)}")
        return False
    
    # Perform validation using centralized service
    is_valid, error_message = _validation_service.validate_field(field_key, text)
    
    # Apply visual feedback based on validation result
    _apply_widget_styling(widget, instance, field_key, is_valid)
    
    # Log validation failures for debugging and monitoring
    if not is_valid and error_message:
        _logger.warning(f"Validation failed for {field_key}: {error_message}")
    
    return is_valid


def on_edit_qedit(instance: Any, widget, field_key: str):
    """
    Handle text changes in form widgets.
    
    Args:
        instance: Instance to update
        widget: The widget that changed
        field_key: Field identifier
    """
    is_valid = validate_and_format_qedit(instance, widget, field_key)
    
    if is_valid:
        # Get and process the value
        value = _get_widget_value(widget, field_key)
        
        # Update the instance
        instance.set_value(field_key, value)
        
        # Reformat the widget to ensure consistency
        validate_and_format_qedit(instance, widget, field_key)


def on_focus_qedit(instance: Any, widget, field_key: str, event):
    """
    Handle focus out events for form widgets.
    
    Args:
        instance: Instance to update  
        widget: The widget losing focus
        field_key: Field identifier
        event: Focus event
    """
    # Get current value
    if isinstance(widget, QLineEdit):
        value = widget.text().strip()
    else:
        value = widget.toPlainText().strip()
    
    # Set default if empty
    if not value:
        default_value = instance.get_default(field_key)
        if isinstance(widget, QLineEdit):
            widget.setText(str(default_value))
        else:
            widget.setPlainText(str(default_value))
    
    # Process numeric fields
    if field_key in ['initial_delay_sec', 'period_sec', 'response_delay_sec']:
        try:
            numeric_value = float(value) if value else float(instance.get_default(field_key))
            if isinstance(widget, QLineEdit):
                widget.setText(str(numeric_value))
            else:
                widget.setPlainText(str(numeric_value))
        except ValueError:
            # Reset to default on invalid value
            default_value = instance.get_default(field_key)
            if isinstance(widget, QLineEdit):
                widget.setText(str(default_value))
            else:
                widget.setPlainText(str(default_value))
    
    # Call the original focus out event
    if isinstance(widget, QLineEdit):
        QLineEdit.focusOutEvent(widget, event)
    elif isinstance(widget, QTextEdit):
        QTextEdit.focusOutEvent(widget, event)


def _get_widget_value(widget, field_key: str) -> Any:
    """Extract and convert widget value based on field type."""
    if isinstance(widget, QLineEdit):
        text = widget.text().strip()
    else:
        text = widget.toPlainText().strip()
    
    # Convert numeric fields
    if field_key in ['initial_delay_sec', 'period_sec', 'response_delay_sec']:
        try:
            return float(text)
        except ValueError:
            return 1.0
    
    return text


def _apply_widget_styling(widget, instance: Any, field_key: str, is_valid: bool):
    """Apply appropriate styling to the widget based on validation and default state."""
    try:
        # Reset to base style
        if instance.is_default(field_key):
            widget.setStyleSheet("color: gray;")
        else:
            widget.setStyleSheet("")
        
        # Apply error styling if invalid
        if not is_valid:
            widget.setStyleSheet("background-color: #ffdddd;")
            
    except Exception as e:
        _logger.warning(f"Error applying widget styling: {e}")


# Legacy compatibility functions
def validate_host(host: str) -> bool:
    """Legacy compatibility function."""
    is_valid, _ = _validation_service.validate_host(host)
    return is_valid


def validate_seconds(value: str) -> bool:
    """Legacy compatibility function."""
    is_valid, _ = _validation_service.validate_seconds(value)
    return is_valid


def validate_route(route: str) -> bool:
    """Legacy compatibility function."""
    is_valid, _ = _validation_service.validate_route(route)
    return is_valid


def validate_json(value: str) -> bool:
    """Legacy compatibility function."""
    is_valid, _ = _validation_service.validate_json(value)
    return is_valid

    #if valid, set default style and client value, else set error style
    if is_valid:
        value = sender.text().strip() if isinstance(sender, QLineEdit) else sender.toPlainText().strip()
        if key in ['initial_delay_sec', 'period_sec', 'response_delay_sec']:
            try:
                value = float(value)
            except ValueError:
                value = 1.0
        instance.set_value(key, value)

        validate_and_format_qedit(instance, sender, key)
    else:
        #TODO: be more generic to use it as common functionality
        #print(f"The input is invalid: Client {self.client.name}, Parameter {key}.")
        pass


def on_focus_qedit(instance, sender, key , event):

    value = sender.text().strip() if isinstance(sender, QLineEdit) else sender.toPlainText()
    # set default if empty
    if value == "":
        value = instance.get_default(key)

    if key in ['initial_delay_sec', 'period_sec', 'response_delay_sec']:
        try:
            value = float(value)
        except ValueError:
            value = 1.0    

    if isinstance(sender, QLineEdit):
        sender.setText(f"{value}")
    elif isinstance(sender, QTextEdit):
        sender.setPlainText(f"{value}")

    if isinstance(sender, QLineEdit):
        QLineEdit.focusOutEvent(sender, event)
    elif isinstance(sender, QTextEdit):
        QTextEdit.focusOutEvent(sender, event)   