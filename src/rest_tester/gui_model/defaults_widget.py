import json
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QCheckBox, QHBoxLayout, QTextEdit, QGroupBox, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal


class DefaultsWidget(QWidget):
    """Widget for editing default values for server or client instances."""
    
    defaults_changed = Signal()  # Signal when defaults are modified
    
    def __init__(self, config, is_server=True):
        super().__init__()
        self.config = config
        self.is_server = is_server
        self.defaults = config.raw['defaults']['server'] if is_server else config.raw['defaults']['client']
        
        # Create group box
        title = "Server Defaults" if is_server else "Client Defaults"
        self.group_box = QGroupBox(title)
        
        # Set minimum height for consistent layout
        self.setMinimumHeight(250)
        self.setMaximumHeight(300)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)
        
        # Form layout inside group box
        self.layout = QFormLayout(self.group_box)
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create form widgets based on server or client type."""
        if self.is_server:
            self._create_server_widgets()
        else:
            self._create_client_widgets()
            
    def _create_server_widgets(self):
        """Create widgets for server defaults."""
        # Host
        self.host_edit = QLineEdit(self.defaults.get('host', ''))
        self.host_edit.textChanged.connect(lambda val: self._on_edit('host', val))
        self.layout.addRow("Host", self.host_edit)
        
        # Autostart
        self.autostart_box = QCheckBox()
        self.autostart_box.setChecked(self.defaults.get('autostart', False))
        self.autostart_box.stateChanged.connect(lambda _: self._on_edit('autostart', self.autostart_box.isChecked()))
        self.layout.addRow("Autostart", self.autostart_box)
        
        # Initial Delay
        self.initial_delay_edit = QLineEdit(str(self.defaults.get('initial_delay_sec', 0.0)))
        self.initial_delay_edit.textChanged.connect(lambda val: self._on_edit('initial_delay_sec', val))
        self.layout.addRow("Initial Delay (s)", self.initial_delay_edit)
        
        # Response Delay
        self.response_delay_edit = QLineEdit(str(self.defaults.get('response_delay_sec', 0.0)))
        self.response_delay_edit.textChanged.connect(lambda val: self._on_edit('response_delay_sec', val))
        self.layout.addRow("Response Delay (s)", self.response_delay_edit)
        
        # Route
        self.route_edit = QLineEdit(self.defaults.get('route', ''))
        self.route_edit.textChanged.connect(lambda val: self._on_edit('route', val))
        self.layout.addRow("Route", self.route_edit)
        
        # Methods (horizontal checkboxes)
        self.methods_checks = []
        self.methods_layout = QHBoxLayout()
        available_methods = ["GET", "POST"]
        current_methods = self.defaults.get('methodes', [])
        
        for method in available_methods:
            cb = QCheckBox(method)
            cb.setChecked(method in current_methods)
            cb.stateChanged.connect(self._on_methods_changed)
            self.methods_checks.append(cb)
            self.methods_layout.addWidget(cb)
        self.layout.addRow("Methods", self.methods_layout)
        
        # Response (4 lines high)
        self.response_edit = QTextEdit(self.defaults.get('response', ''))
        self.response_edit.setFixedHeight(70)  # Fixed height for exactly 4 lines + 20%
        self.response_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.response_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.response_edit.textChanged.connect(lambda: self._on_edit('response', self.response_edit.toPlainText()))
        self.response_edit.focusOutEvent = self._response_focus_out_event
        self.layout.addRow("Response", self.response_edit)
        
        # Initial validation
        self._validate_and_pretty_response()
        
    def _create_client_widgets(self):
        """Create widgets for client defaults."""
        # Host
        self.host_edit = QLineEdit(self.defaults.get('host', ''))
        self.host_edit.textChanged.connect(lambda val: self._on_edit('host', val))
        self.layout.addRow("Host", self.host_edit)
        
        # Autostart
        self.autostart_box = QCheckBox()
        self.autostart_box.setChecked(self.defaults.get('autostart', False))
        self.autostart_box.stateChanged.connect(lambda _: self._on_edit('autostart', self.autostart_box.isChecked()))
        self.layout.addRow("Autostart", self.autostart_box)
        
        # Initial Delay
        self.initial_delay_edit = QLineEdit(str(self.defaults.get('initial_delay_sec', 0.0)))
        self.initial_delay_edit.textChanged.connect(lambda val: self._on_edit('initial_delay_sec', val))
        self.layout.addRow("Initial Delay (s)", self.initial_delay_edit)
        
        # Loop
        self.loop_box = QCheckBox()
        self.loop_box.setChecked(self.defaults.get('loop', False))
        self.loop_box.stateChanged.connect(lambda _: self._on_edit('loop', self.loop_box.isChecked()))
        self.layout.addRow("Loop", self.loop_box)
        
        # Period
        self.period_edit = QLineEdit(str(self.defaults.get('period_sec', 1.0)))
        self.period_edit.textChanged.connect(lambda val: self._on_edit('period_sec', val))
        self.layout.addRow("Period (s)", self.period_edit)
        
        # Route
        self.route_edit = QLineEdit(self.defaults.get('route', ''))
        self.route_edit.textChanged.connect(lambda val: self._on_edit('route', val))
        self.layout.addRow("Route", self.route_edit)
        
        # Method (exclusive checkboxes)
        self.method_checks = []
        self.method_layout = QHBoxLayout()
        server_methods = ["GET", "POST"]
        current_method = self.defaults.get('methode', server_methods[0] if server_methods else 'GET')
        
        for method in server_methods:
            cb = QCheckBox(method)
            cb.setChecked(method == current_method)
            cb.stateChanged.connect(self._on_method_changed)
            self.method_checks.append(cb)
            self.method_layout.addWidget(cb)
        self.layout.addRow("Method", self.method_layout)
        
        # Request (4 lines high)
        self.request_edit = QTextEdit(self.defaults.get('request', ''))
        self.request_edit.setFixedHeight(70)  # Fixed height for exactly 4 lines + 20%
        self.request_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.request_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.request_edit.textChanged.connect(lambda: self._on_edit('request', self.request_edit.toPlainText()))
        self.request_edit.focusOutEvent = self._request_focus_out_event
        self.layout.addRow("Request", self.request_edit)
        
        # Initial validation
        self._validate_and_pretty_request()
        
    def _on_edit(self, key, value):
        """Handle value changes."""
        # Convert numeric values
        if key in ['initial_delay_sec', 'response_delay_sec', 'period_sec']:
            try:
                value = float(value)
            except ValueError:
                return  # Invalid value, ignore
        
        # Update the defaults
        self.defaults[key] = value
        
        # Emit signal that defaults changed
        self.defaults_changed.emit()
        
    def _on_methods_changed(self):
        """Handle server methods selection (multiple allowed)."""
        selected = [cb.text() for cb in self.methods_checks if cb.isChecked()]
        if not selected:
            # At least one method must be selected
            self.methods_checks[0].setChecked(True)
            selected = [self.methods_checks[0].text()]
        
        self.defaults['methodes'] = selected
        self.defaults_changed.emit()
        
    def _on_method_changed(self):
        """Handle client method selection (exclusive)."""
        sender = self.sender()
        if sender.isChecked():
            # Uncheck all others
            for cb in self.method_checks:
                if cb is not sender:
                    cb.setChecked(False)
            self.defaults['methode'] = sender.text()
        else:
            # Must have at least one selected
            if not any(cb.isChecked() for cb in self.method_checks):
                sender.setChecked(True)
                
        self.defaults_changed.emit()
        
    def _validate_and_pretty_response(self):
        """Validate and format response JSON."""
        if not hasattr(self, 'response_edit'):
            return
            
        text = self.response_edit.toPlainText()
        try:
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.response_edit.setPlainText(pretty)
            self.response_edit.setStyleSheet("")
        except Exception:
            if text.strip():  # Only show error if there's content
                self.response_edit.setStyleSheet("background-color: #ffcccc;")
            else:
                self.response_edit.setStyleSheet("")
                
    def _validate_and_pretty_request(self):
        """Validate and format request JSON."""
        if not hasattr(self, 'request_edit'):
            return
            
        text = self.request_edit.toPlainText()
        try:
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.request_edit.setPlainText(pretty)
            self.request_edit.setStyleSheet("")
        except Exception:
            if text.strip():  # Only show error if there's content
                self.request_edit.setStyleSheet("background-color: #ffcccc;")
            else:
                self.request_edit.setStyleSheet("")
                
    def _response_focus_out_event(self, event):
        """Handle response field focus out."""
        self._validate_and_pretty_response()
        super(QTextEdit, self.response_edit).focusOutEvent(event)
        
    def _request_focus_out_event(self, event):
        """Handle request field focus out."""
        self._validate_and_pretty_request()
        super(QTextEdit, self.request_edit).focusOutEvent(event)
