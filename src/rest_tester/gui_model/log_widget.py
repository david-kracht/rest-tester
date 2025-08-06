"""
REST Tester Instance Log Widget Module

This module provides a specialized logging widget for displaying instance-specific
log messages in a console-style interface. It integrates with the application's
logging system to provide real-time log viewing for individual server and client
instances.

Key Components:
    InstanceLogWidget: Console-style log display widget with filtering and formatting

Architecture Overview:
    The widget connects to the centralized logging system through LogSignalHandler
    to receive log messages. It filters messages by instance name and provides
    a dark, console-like interface optimized for log viewing.

Features:
    - Instance-specific log filtering
    - Console-style dark theme interface
    - Monospace font for consistent formatting
    - Context menu for font size adjustment
    - Memory-efficient with document size limits
    - Real-time log message reception
    - Level-based message formatting

Dependencies:
    - PySide6: Qt framework for GUI components
    - LogSignalHandler: Application logging signal system

Design Patterns:
    - Observer Pattern: Log message reception through signals
    - Template Method: Consistent UI setup and formatting
    - Strategy Pattern: Configurable font and styling options

Thread Safety:
    The widget receives log messages through Qt's signal system, ensuring
    thread-safe communication from background logging operations.
"""

from typing import Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QAction
from ..service.logging_config import LogSignalHandler


class InstanceLogWidget(QWidget):
    """
    Console-style log display widget for instance-specific log messages.
    
    This widget provides a dark, console-like interface for viewing log messages
    from specific server or client instances. It filters messages by instance
    name and presents them in a format optimized for debugging and monitoring.
    
    The widget automatically receives log messages through the application's
    signal-based logging system and displays them with appropriate formatting
    and styling for easy reading.
    
    Key Features:
        - Instance-specific message filtering
        - Dark console-style appearance
        - Monospace font for consistent alignment
        - Configurable font size through context menu
        - Memory-efficient document size limiting
        - Real-time message reception
        - Thread-safe operation through Qt signals
        
    UI Design:
        The widget uses a single QTextEdit with custom styling to create
        a professional console appearance. Messages are automatically
        scrolled and formatted for optimal readability.
        
    Attributes:
        instance_name (str): Name of the instance for message filtering
        log_display (QTextEdit): Main text area for log message display
        log_handler (LogSignalHandler): Connection to logging signal system
        
    Signals:
        The widget connects to logging signals to receive messages but
        does not emit its own signals.
    """
    
    def __init__(self, instance_name: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the instance log widget.
        
        Args:
            instance_name: Name of the instance to filter log messages for
            parent: Optional parent widget for Qt hierarchy
            
        Setup Process:
            1. Store instance name for message filtering
            2. Initialize UI components with console styling
            3. Configure logging system connection
            4. Set up event handlers and context menus
        """
        super().__init__(parent)
        self.instance_name = instance_name
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self) -> None:
        """
        Initialize and configure the user interface components.
        
        This method creates the main text display area with console-style
        formatting and configures fonts, colors, and layout for optimal
        log viewing. It includes memory management settings to prevent
        performance issues with large log outputs.
        
        UI Configuration:
            - Dark background with light text for console feel
            - Monospace font for consistent character alignment
            - Document size limits for memory efficiency
            - Context menu for font size adjustment
            - Professional border styling
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main log display text area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        # Configure memory management to prevent issues with large logs
        self.log_display.document().setMaximumBlockCount(10000)
        
        # Configure monospace font with fallback options
        font = QFont("Consolas", 7)  # Preferred console font
        if not font.exactMatch():
            font = QFont("Courier New", 7)  # Windows fallback
        if not font.exactMatch():
            font = QFont("monospace", 7)  # Generic fallback
        self.log_display.setFont(font)
        
        # Apply dark console-style appearance
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                font-family: monospace;
            }
        """)
        
        # Configure context menu for font size adjustment
        self.log_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_display.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.log_display)
    
    def setup_logging(self) -> None:
        """
        Configure logging system connection for this instance.
        
        This method creates and configures a LogSignalHandler specifically
        for this instance's log messages. The handler filters messages by
        instance name and connects to the widget's display method.
        
        Signal Connection:
            The handler's log_message signal is connected to add_log_message
            to enable real-time log display updates from background operations.
        """
        self.signal_handler = LogSignalHandler(self.instance_name)
        self.signal_handler.log_message.connect(self.add_log_message)
    
    def get_signal_handler(self) -> LogSignalHandler:
        """
        Retrieve the signal handler for logger configuration.
        
        Returns:
            LogSignalHandler: The instance-specific signal handler
            
        This method provides access to the signal handler for integration
        with the application's logging system. The handler can be added
        to loggers to enable message routing to this widget.
        """
        return self.signal_handler
    
    @Slot(str, str, str)
    def add_log_message(self, timestamp: str, level: str, message: str) -> None:
        """
        Add a formatted log message to the display.
        
        Args:
            timestamp: Formatted timestamp string for the message
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: The actual log message content
            
        This method handles the formatting and display of log messages with
        appropriate color coding and structure preservation. It handles both
        single-line messages and complex multi-line content like JSON blocks.
        
        Message Processing:
            1. Apply level-based color coding
            2. Detect and preserve multi-line formatting
            3. Handle JSON blocks with special formatting
            4. Maintain indentation and whitespace
            5. Auto-scroll to show latest messages
            
        Special Handling:
            - JSON blocks are formatted as cohesive units
            - Indentation and spacing are preserved
            - Empty lines are maintained for readability
            - HTML encoding prevents formatting issues
        """
        # Apply color coding based on log level
        color = self.get_level_color(level)
        
        # Handle pre-formatted messages (multi-line with headers)
        if message.startswith('[') and '][' in message and level in message:
            # Message already formatted by LogSignalHandler
            lines = message.split('\n')
            
            # Detect JSON blocks for special formatting
            is_json_block = any('-----' in line or '{' in line or '}' in line for line in lines)
            
            if is_json_block and len(lines) > 3:
                # Format JSON blocks with unified header
                first_line = lines[0]
                import re
                header_match = re.match(r'^\[([^\]]+)\]\[([^\]]+)\]', first_line)
                if header_match:
                    block_timestamp = header_match.group(1)
                    block_level = header_match.group(2)
                    
                    # Create unified block header
                    block_header = f'<span style="color: {color};">[{block_timestamp}][{block_level}]</span>'
                    self.log_display.append(block_header)
                    
                    # Add content lines with preserved formatting
                    for line in lines:
                        content_match = re.match(r'^\[[^\]]+\]\[[^\]]+\] (.*)', line)
                        if content_match:
                            content = content_match.group(1)
                            # Preserve whitespace using HTML entities
                            html_content = content.replace(' ', '&nbsp;') if content else ''
                            formatted_line = f'<span style="color: {color};">{html_content}</span>'
                            self.log_display.append(formatted_line)
                        elif line.strip():  # Handle non-matching lines
                            html_line = line.replace(' ', '&nbsp;')
                            formatted_line = f'<span style="color: {color};">{html_line}</span>'
                            self.log_display.append(formatted_line)
                else:
                    # Fallback for unparseable headers
                    for line in lines:
                        if line.strip():
                            formatted_line = f'<span style="color: {color};">{line}</span>'
                            self.log_display.append(formatted_line)
            else:
                # Handle regular multi-line messages
                for line in lines:
                    if line.strip():
                        formatted_line = f'<span style="color: {color};">{line}</span>'
                        self.log_display.append(formatted_line)
        else:
            # Handle simple messages with custom formatting
            lines = message.split('\n')
            for line in lines:
                if line.strip():
                    formatted_line = f'<span style="color: {color};">[{timestamp}][{level}] {line}</span>'
                    self.log_display.append(formatted_line)
        
        # Auto-scroll to show latest messages
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_level_color(self, level: str) -> str:
        """
        Determine display color for log level.
        
        Args:
            level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Hex color code for the specified level
            
        This method provides consistent color coding for different log levels
        to improve readability and quick identification of message importance.
        
        Color Scheme:
            - DEBUG: Gray (#888888) - Less prominent for debug info
            - INFO: White (#ffffff) - Standard visibility for information
            - WARNING: Orange (#ffaa00) - Attention-grabbing for warnings
            - ERROR: Red (#ff4444) - Clear indication of errors
            - CRITICAL: Bright Red (#ff0000) - Maximum visibility for critical issues
        """
        colors = {
            'DEBUG': '#888888',
            'INFO': '#ffffff',
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }
        return colors.get(level, '#ffffff')  # Default to white for unknown levels
    
    def show_context_menu(self, position: Any) -> None:
        """
        Display context menu for log widget operations.
        
        Args:
            position: Position where context menu was requested
            
        This method creates and displays a context menu with options for
        font size adjustment and log clearing. It provides user-friendly
        controls for customizing the log viewing experience.
        
        Menu Options:
            - Font Size submenu: Multiple size options (6-18pt)
            - Custom Font Size: User input for specific sizes
            - Clear Logs: Remove all current log content
            
        The menu shows the current font size with a checkmark for easy
        identification of the active setting.
        """
        menu = QMenu(self)
        
        # Create font size submenu with common sizes
        font_menu = menu.addMenu("Font Size")
        
        sizes = [6, 7, 8, 9, 10, 11, 12, 14, 16, 18]
        current_size = self.log_display.font().pointSize()
        
        # Add size options with current size marked
        for size in sizes:
            action = QAction(f"{size}pt", self)
            if size == current_size:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
            font_menu.addAction(action)
        
        font_menu.addSeparator()
        
        # Custom font size option
        custom_action = QAction("Custom...", self)
        custom_action.triggered.connect(self.set_custom_font_size)
        font_menu.addAction(custom_action)
        
        # Log management actions
        menu.addSeparator()
        clear_action = QAction("Clear Logs", self)
        clear_action.triggered.connect(self.clear_logs)
        menu.addAction(clear_action)
        
        # Display menu at requested position
        menu.exec(self.log_display.mapToGlobal(position))
    
    def set_font_size(self, size: int) -> None:
        """
        Set the font size for the log display.
        
        Args:
            size: Font size in points
            
        This method updates the font size while preserving the monospace
        font family for consistent character alignment in log output.
        """
        font = self.log_display.font()
        font.setPointSize(size)
        self.log_display.setFont(font)
    
    def set_custom_font_size(self) -> None:
        """
        Prompt user for custom font size input.
        
        This method displays an input dialog for users to specify a custom
        font size outside the predefined options. It includes validation
        to ensure the entered value is within reasonable bounds.
        """
        current_size = self.log_display.font().pointSize()
        size, ok = QInputDialog.getInt(
            self, 
            "Custom Font Size", 
            "Enter font size (4-72):",
            current_size,
            4,  # minimum
            72  # maximum
        )
        if ok:
            self.set_font_size(size)
    
    def clear_logs(self) -> None:
        """
        Clear all log content from the display.
        
        This method prompts for confirmation before clearing the log content
        to prevent accidental data loss. It provides a clean slate for new
        log messages while maintaining all widget settings.
        """
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            f"Clear all log messages for {self.instance_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log_display.clear()
    
    def show_context_menu(self, position):
        """Show context menu for font size adjustment and clearing."""
        menu = QMenu(self)
        
        # Font size actions
        font_menu = menu.addMenu("Font Size")
        
        sizes = [6, 7, 8, 9, 10, 11, 12, 14, 16, 18]
        current_size = self.log_display.font().pointSize()
        
        for size in sizes:
            action = QAction(f"{size}pt", self)
            if size == current_size:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
            font_menu.addAction(action)
        
        font_menu.addSeparator()
        custom_action = QAction("Custom Size...", self)
        custom_action.triggered.connect(self.set_custom_font_size)
        font_menu.addAction(custom_action)
        
        # Clear action
        menu.addSeparator()
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.clear_log)
        menu.addAction(clear_action)
        
        # Copy all action
        copy_action = QAction("Copy All", self)
        copy_action.triggered.connect(self.copy_all_logs)
        menu.addAction(copy_action)
        
        menu.exec(self.log_display.mapToGlobal(position))
    
    def set_font_size(self, size: int):
        """Set font size."""
        font = self.log_display.font()
        font.setPointSize(size)
        self.log_display.setFont(font)
    
    def set_custom_font_size(self):
        """Set custom font size via input dialog."""
        current_size = self.log_display.font().pointSize()
        size, ok = QInputDialog.getInt(
            self, 
            "Font Size", 
            "Enter font size (pt):", 
            current_size, 
            4, 
            72
        )
        if ok:
            self.set_font_size(size)
    
    def clear_log(self):
        """Clear all log messages."""
        reply = QMessageBox.question(
            self,
            "Clear Log",
            f"Clear all log messages for {self.instance_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log_display.clear()
    
    def copy_all_logs(self):
        """Copy all logs to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_display.toPlainText())
