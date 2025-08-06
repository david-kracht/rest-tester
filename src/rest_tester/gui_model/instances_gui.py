"""
REST Tester Instance Management GUI Module

This module provides the main tabbed interface for managing server and client instances
in the REST Tester application. It implements a comprehensive management system for
both server endpoints and client request configurations with real-time status tracking,
lifecycle management, and integrated defaults configuration.

Key Components:
    InstanceTabWidget: Main tabbed interface for server/client management
    ClientFinishedSignal: Thread-safe communication for client completion events
    ServerErrorSignal: Thread-safe communication for server error events

Architecture Overview:
    This module follows the Model-View-Controller pattern where the InstanceTabWidget
    acts as both a view and controller, managing the UI representation and coordinating
    between the configuration model and the service layer (rest_server_manager and
    rest_client_manager).

Features:
    - Dynamic tab management with add/remove/rename functionality
    - Real-time server and client status tracking
    - Integrated defaults configuration for new instances
    - Thread-safe communication for background operations
    - Context menu support for advanced instance operations
    - Automatic startup support for configured instances
    - Live parameter updates and validation

Dependencies:
    - PySide6: Qt framework for GUI components
    - ConfigModel: Configuration management and persistence
    - ServerInstance/ClientInstance: Data models for instances
    - ServerInstanceWidget/ClientInstanceWidget: UI widgets for instances
    - DefaultsWidget: Global defaults configuration interface
    - REST managers: Service layer for actual server/client operations

Design Patterns:
    - Observer Pattern: Signal-slot communication for UI updates
    - Factory Pattern: Dynamic widget creation based on instance type
    - Command Pattern: Action-based instance management operations
    - Composite Pattern: Hierarchical tab organization with widgets

Thread Safety:
    The module implements thread-safe communication patterns using Qt signals
    to handle callbacks from background server and client operations, ensuring
    UI updates occur on the main thread.
"""

import importlib
import threading
from typing import Optional, Set, Tuple, Any, Dict
from PySide6.QtWidgets import (
    QApplication, QWidget, QSplitter, QTabWidget, QVBoxLayout, QPushButton, 
    QHBoxLayout, QMessageBox, QLineEdit, QGroupBox, QMenu, QTabBar
)
from PySide6.QtCore import Qt, QEvent, Signal, QObject
from . import (
    ConfigModel, ServerInstance, ClientInstance, ServerInstanceWidget, 
    ClientInstanceWidget, DefaultsWidget
)


class ClientFinishedSignal(QObject):
    """
    Thread-safe signal for communicating client completion events.
    
    This signal class enables safe communication between background client
    threads and the main UI thread when a client operation completes.
    It ensures that UI updates happen on the main thread, preventing
    potential race conditions and Qt-related crashes.
    
    Signals:
        finished: Emitted when a client operation completes
        
    Args:
        client_name (str): Name identifier of the completed client
    """
    finished = Signal(str)  # client_name


class ServerErrorSignal(QObject):
    """
    Thread-safe signal for communicating server error events.
    
    This signal class enables safe communication between background server
    threads and the main UI thread when server errors occur. It ensures
    that error handling and UI updates happen on the main thread.
    
    Signals:
        error_occurred: Emitted when a server operation encounters an error
        
    Args:
        server_name (str): Name identifier of the server with error
        error_message (str): Description of the error that occurred
    """
    error_occurred = Signal(str, str)  # server_name, error_message


class InstanceTabWidget(QWidget):
    """
    Main tabbed interface widget for managing server or client instances.
    
    This widget provides a comprehensive interface for managing multiple server
    or client instances through a tabbed layout. It includes integrated defaults
    configuration, real-time status tracking, and dynamic tab management with
    support for adding, removing, and renaming instances.
    
    The widget operates in two modes:
    - Server mode: Manages REST server endpoints with HTTP method support
    - Client mode: Manages REST client requests with timing and loop support
    
    Key Features:
        - Dynamic tab creation and management
        - Integrated defaults configuration widget
        - Real-time instance status tracking
        - Context menu support for advanced operations
        - Thread-safe communication with background operations
        - Automatic startup for configured instances
        - Live parameter validation and updates
        
    Architecture:
        The widget follows a composite pattern where each tab contains either
        a ServerInstanceWidget or ClientInstanceWidget. It coordinates between
        the configuration model and the service layer managers for actual
        server/client operations.
        
    Signals:
        The widget connects to various signals from child widgets and managers
        to provide real-time feedback and status updates to the user interface.
        
    Attributes:
        config: Configuration model containing instance definitions
        is_server (bool): True for server mode, False for client mode
        manager: Service layer manager (RestServerManager or RestClientManager)
        tabs (QTabWidget): Main tabbed interface container
        defaults_widget (DefaultsWidget): Integrated defaults configuration
        running_servers (Set): Track currently running server instances
        running_clients (Set): Track currently running client instances
        client_finished_signal: Thread-safe client completion communication
        server_error_signal: Thread-safe server error communication
    """
    def __init__(self, config: ConfigModel, is_server: bool = True, manager: Optional[Any] = None) -> None:
        """
        Initialize the instance tab widget for server or client management.
        
        Args:
            config: Configuration model containing instance definitions and defaults
            is_server: True for server mode, False for client mode
            manager: Service layer manager (RestServerManager or RestClientManager)
            
        Setup Process:
            1. Initialize base widget and store configuration references
            2. Create and configure the main tabbed interface
            3. Set up context menus and event handling
            4. Initialize status tracking collections
            5. Create thread-safe communication signals
            6. Build the layout with defaults and instances sections
            7. Initialize tabs and handle autostart instances
            
        UI Structure:
            - DefaultsWidget: Global configuration for new instances
            - InstancesGroup: Container for the tabbed instance interface
            - QTabWidget: Main tabs with closable and renameable tabs
            - Plus Tab: Special tab for adding new instances
            
        Event Handling:
            - Tab close requests for instance removal
            - Tab changes for focus management
            - Context menu requests for advanced operations
            - Double-click events for tab renaming
            
        Status Tracking:
            - running_servers: Set of (host, port, route) tuples for active servers
            - running_clients: Set of client names for active clients
            - Thread-safe signals for background operation communication
        """
        super().__init__()
        self.config = config
        self.is_server = is_server
        self.manager = manager
        
        # Create main tabbed interface with advanced features
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._on_close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.tabBar().installEventFilter(self)
        self.tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)
        
        # Setup tab renaming functionality if available
        self.tabs.tabBarDoubleClicked = getattr(self.tabs, 'tabBarDoubleClicked', None)
        if hasattr(self.tabs, 'tabBarDoubleClicked'):
            self.tabs.tabBarDoubleClicked.connect(self._on_tab_rename)

        # Flag to track special plus tab operations
        self._updating_plus_tab = False

        # Status tracking for active instances
        self.running_servers: Set[Tuple[str, int, str]] = set()  # (host, port, route) tuples
        self.running_clients: Set[str] = set()  # client names
        
        # Thread-safe communication signals
        self.client_finished_signal = ClientFinishedSignal()
        self.client_finished_signal.finished.connect(self._on_client_finished)
        
        self.server_error_signal = ServerErrorSignal()
        self.server_error_signal.error_occurred.connect(self._on_server_error)

        # Layout configuration with minimal spacing
        spacing = 0

        
        # Create integrated defaults configuration widget
        self.defaults_widget = DefaultsWidget(config, is_server)
        self.defaults_widget.defaults_changed.connect(self._on_defaults_changed)
        
        # Create transparent instances group container
        self.instances_group = QGroupBox("Instances")
        self.instances_group.setStyleSheet("""
            QGroupBox {
                border: none;
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
        
        # Configure instance group layout
        instances_layout = QVBoxLayout(self.instances_group)
        instances_layout.setSpacing(spacing)
        instances_layout.setContentsMargins(0, 0, 0, 0)
        instances_layout.addWidget(self.tabs)
        
        # Build main widget layout
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.defaults_widget)
        layout.addWidget(self.instances_group)
        self.setLayout(layout)
        
        # Initialize tabs and handle autostart instances
        self._init_tabs()
        self._handle_autostart_instances()
        
    def _handle_autostart_instances(self) -> None:
        """
        Initialize autostart instances based on configuration.
        
        This method processes all configured instances and automatically
        starts those marked with the autostart flag. It handles both
        server and client instances appropriately.
        
        For Server Instances:
            - Registers endpoints with the REST server manager
            - Updates UI status to reflect running state
            
        For Client Instances:
            - Starts client request threads
            - Updates widget running status
            - Adds to running clients tracking
        """
        if self.is_server and self.manager:
            for inst in self.config.servers:
                if inst.get_value('autostart'):
                    self._register_endpoint(inst)
        elif not self.is_server and self.manager:
            for i, inst in enumerate(getattr(self.config, 'clients', [])):
                if inst.get_value('autostart'):
                    self._start_client(inst)
                    # Update UI status for autostart clients
                    widget = self.tabs.widget(i)
                    if hasattr(widget, 'set_running'):
                        widget.set_running(True)
                    self.running_clients.add(inst.name)
    
    def _on_server_start_requested(self, server_instance: ServerInstance) -> None:
        """
        Handle server start requests from instance widgets.
        
        Args:
            server_instance: The server instance to start
            
        This method is called when a server instance widget requests
        to start its endpoint. It delegates to the endpoint registration
        system which handles the actual server startup process.
        """
        self._register_endpoint(server_instance)
    
    def _on_server_stop_requested(self, server_instance: ServerInstance) -> None:
        """
        Handle server stop requests from instance widgets.
        
        Args:
            server_instance: The server instance to stop
            
        This method is called when a server instance widget requests
        to stop its endpoint. It delegates to the endpoint removal
        system which handles the actual server shutdown process.
        """
        self._remove_endpoint(server_instance)
    
    def _on_client_start_requested(self, client_instance: ClientInstance) -> None:
        """
        Handle client start requests from instance widgets.
        
        Args:
            client_instance: The client instance to start
            
        This method processes client start requests by initializing
        the client thread and updating the UI status. It finds the
        corresponding widget and sets its running state.
        """
        self._start_client(client_instance)
        
        # Find and update the corresponding widget
        for i, inst in enumerate(getattr(self.config, 'clients', [])):
            if inst == client_instance:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'set_running'):
                    widget.set_running(True)
                self.running_clients.add(client_instance.name)
                break
    
    def _on_client_stop_requested(self, client_instance: ClientInstance) -> None:
        """
        Handle client stop requests from instance widgets.
        
        Args:
            client_instance: The client instance to stop
            
        This method processes client stop requests by stopping the
        client thread through the manager and updating the UI status.
        It finds the corresponding widget and sets its stopped state.
        """
        self.manager.stop_client(client_instance.name)
        
        # Find and update the corresponding widget
        for i, inst in enumerate(getattr(self.config, 'clients', [])):
            if inst == client_instance:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'set_running'):
                    widget.set_running(False)
                self.running_clients.discard(client_instance.name)
                break

    def _on_client_finished(self, client_name: str) -> None:
        """
        Handle client completion notifications from background threads.
        
        Args:
            client_name: Name of the client that finished
            
        This method is called through the thread-safe signal system
        when a client thread completes its operation. It updates the
        UI status and cleans up the client from the manager.
        
        Thread Safety:
            This method runs on the main thread via Qt signal system,
            ensuring safe UI updates from background operations.
        """
        # Find and update the corresponding widget
        for i, inst in enumerate(getattr(self.config, 'clients', [])):
            if inst.name == client_name:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'set_running'):
                    widget.set_running(False)
                self.running_clients.discard(client_name)
                # Clean up from manager as thread is finished
                if client_name in self.manager.clients:
                    del self.manager.clients[client_name]
                break

    def _on_client_params_changed(self, client_instance: ClientInstance, params: Dict[str, Any]) -> None:
        """
        Handle parameter changes for running client instances.
        
        Args:
            client_instance: The client instance that changed
            params: Dictionary of updated parameters
            
        This method processes real-time parameter updates for active client
        instances. It communicates with the REST client manager to apply
        changes without requiring a restart of the client operation.
        
        Error Handling:
            If parameter updates fail, an error is logged to help with
            debugging and troubleshooting client operation issues.
        """
        if not self.manager:
            return
            
        success = self.manager.update_client_params(client_instance.name, **params)
        if not success:
            # Avoid import errors by delaying logger import
            from ..service.logging_config import get_logger
            logger = get_logger("InstanceTabWidget")
            logger.error(f"Failed to update params for client {client_instance.name}")

    def _on_server_params_changed(self, server_instance: ServerInstance, params: Dict[str, Any]) -> None:
        """
        Handle parameter changes for running server instances.
        
        Args:
            server_instance: The server instance that changed
            params: Dictionary of updated parameters
            
        This method processes real-time parameter updates for active server
        instances. It focuses on parameters that can be updated without
        restarting the server, such as response templates and delay settings.
        
        Update Process:
            1. Extract current endpoint parameters
            2. Create new handler with updated response/delay parameters
            3. Update the endpoint handler in the REST server manager
            
        Supported Updates:
            - Response template changes
            - Response delay modifications
            - Dynamic handler reconfiguration
            
        Error Handling:
            If handler updates fail, an error is logged to assist with
            debugging server configuration issues.
        """
        if not self.manager:
            return
        
        host, port, route, methods, response, response_delay_sec, initial_delay_sec = self._get_endpoint_params(server_instance)
        
        # Create new handler with updated parameters
        if 'response' in params or 'response_delay_sec' in params:
            from ..service.endpoint_utils import make_generic_handler
            new_response = params.get('response', response)
            new_delay = params.get('response_delay_sec', response_delay_sec)
            handler = make_generic_handler(new_response, new_delay, server_name=server_instance.name)
            
            success = self.manager.update_endpoint_handler(host, port, route, handler)
            if not success:
                # Avoid import errors by delaying logger import
                from ..service.logging_config import get_logger
                logger = get_logger("InstanceTabWidget")
                logger.error(f"Failed to update handler for server {server_instance.name}")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Handle mouse events for tab bar interactions.
        
        Args:
            obj: The object that generated the event
            event: The Qt event to process
            
        Returns:
            True if event was handled, False otherwise
            
        This event filter specifically handles double-click events on
        the tab bar to trigger tab renaming functionality. It uses the
        modern Qt API for event position handling.
        """
        if obj == self.tabs.tabBar() and event.type() == QEvent.MouseButtonDblClick:
            # Use modern Qt API for position handling
            index = self.tabs.tabBar().tabAt(event.position().toPoint())
            if index >= 0:
                self._on_tab_rename(index)
            return True
        return super().eventFilter(obj, event)

    def _show_tab_context_menu(self, position: Any) -> None:
        """
        Display context menu for tab bar interactions.
        
        Args:
            position: Position where the context menu was requested
            
        This method creates and displays a context menu for tab operations
        such as renaming, duplicating, or performing advanced actions on
        instance tabs. It excludes the special plus tab from context menus.
        """
        index = self.tabs.tabBar().tabAt(position)
        if index < 0 or self._is_plus_tab(index):
            return
            
        menu = QMenu(self)
        
        # Clone-Aktion
        clone_action = menu.addAction("Clone")
        clone_action.triggered.connect(lambda: self._clone_instance(index))
        
        # Reset-Aktion
        reset_action = menu.addAction("Reset")
        reset_action.triggered.connect(lambda: self._reset_instance_by_index(index))
        
        # Zeige Menü an der Mausposition
        menu.exec_(self.tabs.tabBar().mapToGlobal(position))

    def _on_tab_rename(self, index):
        tab_bar = self.tabs.tabBar()
        old_name = self.tabs.tabText(index)
        editor = QLineEdit(old_name, tab_bar)
        editor.setGeometry(tab_bar.tabRect(index))
        editor.setFocus()
        editor.selectAll()
        editor.editingFinished.connect(lambda: self._finish_tab_rename(index, editor))
        editor.show()

    def _finish_tab_rename(self, index, editor):
        new_name = editor.text().strip()
        if not new_name:
            editor.deleteLater()
            return
        # Eindeutigkeit prüfen
        all_names = [self.tabs.tabText(i) for i in range(self.tabs.count())]
        if new_name in all_names and new_name != self.tabs.tabText(index):
            QMessageBox.warning(self, "Name existiert", "Der Name muss eindeutig sein!")
            editor.deleteLater()
            return
        
        # Alten Namen für Thread-Referenz merken
        old_name = self.tabs.tabText(index)
        
        self.tabs.setTabText(index, new_name)
        # Instanzname im Model aktualisieren
        if self.is_server:
            server_inst = self.config.servers[index]
            old_server_name = server_inst.name
            server_inst.name = new_name
            
            # Bei Server-Threads: Prüfe ob ein Endpoint mit diesem Namen läuft
            if self.manager and hasattr(self.manager, 'rename_endpoint_reference'):
                # Hole die aktuellen Server-Parameter
                host, port, route, _, _, _, _ = self._get_endpoint_params(server_inst)
                # Da sich nur der Name ändert, nicht die Endpoint-Parameter,
                # müssen wir den Endpoint nicht umbenennen - der Name ist nur für die GUI
                # Der Server läuft weiter mit den gleichen Host/Port/Route Parametern
                pass
        else:
            self.config.clients[index].name = new_name
            # Bei Client-Threads: Referenz im Manager aktualisieren
            if self.manager and old_name in self.manager.clients:
                # Hole den laufenden Thread mit dem alten Namen
                thread = self.manager.clients[old_name]
                # Aktualisiere den Namen im Thread selbst
                thread.name = new_name
                # Verschiebe die Referenz im Manager Dictionary
                self.manager.clients[new_name] = thread
                del self.manager.clients[old_name]
        
        editor.deleteLater()
        # Config speichern, damit Änderung persistent ist
        if hasattr(self.config, 'save'):
            self.config.save()

    def _get_client_params(self, inst):
        host_port = inst.get_value('host')
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            host = host.strip()
            port = int(port)
            host = f"{host}:{port}"
        else:
            host = host_port
        route = inst.get_value('route')
        method = inst.get_value('methode')
        request_data = inst.get_value('request')
        period_sec = float(inst.get_value('period_sec') or 1.0)
        loop = bool(inst.get_value('loop'))
        initial_delay_sec = float(inst.get_value('initial_delay_sec') or 0.0)
        return inst.name, host, route, method, request_data, period_sec, loop, initial_delay_sec

    def _start_client(self, inst):
        if not self.manager:
            return
        name, host, route, method, request_data, period_sec, loop, initial_delay_sec = self._get_client_params(inst)
        
        # Get signal handler from the widget
        signal_handler = None
        for i, client_inst in enumerate(getattr(self.config, 'clients', [])):
            if client_inst == inst:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'get_log_signal_handler'):
                    signal_handler = widget.get_log_signal_handler()
                break
        
        # Übergebe Callback für automatische Thread-Beendigung (thread-safe über Signal)
        def signal_finished(client_name):
            self.client_finished_signal.finished.emit(client_name)
        
        self.manager.start_client(name, host, route, method, request_data, period_sec, loop, 
                                initial_delay_sec=initial_delay_sec, on_finished=signal_finished, signal_handler=signal_handler)

    def _start_client_request(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or self.is_server or not self.manager:
            return
        inst = getattr(self.config, 'clients', [])[idx]
        self._start_client(inst)

    def _stop_client_request(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or self.is_server or not self.manager:
            return
        inst = getattr(self.config, 'clients', [])[idx]
        self.manager.stop_client(inst.name)

    def _stop_endpoint(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or not self.is_server or not self.manager:
            return
        inst = self.config.servers[idx]
        self._remove_endpoint(inst)
        # Button-Status wird in _remove_endpoint aktualisiert

    def _get_endpoint_params(self, inst):
        # Host: host:port
        host_port = inst.get_value('host')
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host = host_port
            port = 5000
        route = inst.get_value('route')
        methods = inst.get_value('methodes')
        response = inst.get_value('response')
        response_delay_sec = float(inst.get_value('response_delay_sec') or 0.0)
        initial_delay_sec = float(inst.get_value('initial_delay_sec') or 0.0)
        return host, port, route, methods, response, response_delay_sec, initial_delay_sec

    def _register_endpoint(self, inst):
        from ..service.endpoint_utils import make_generic_handler
        host, port, route, methods, response, response_delay_sec, initial_delay_sec = self._get_endpoint_params(inst)
        
        #TODO: fix to early validation
        '''
        try:
            import json
            response_json = json.loads(response) if response else {}
        except Exception:
            response_json = {"error": "invalid response json"}
        '''
        handler = make_generic_handler(response, response_delay_sec, server_name=inst.name)

        # Setze Widget zunächst auf "läuft"
        widget = None
        signal_handler = None
        for i, server_inst in enumerate(self.config.servers):
            if server_inst == inst:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'set_running'):
                    widget.set_running(True)
                # Get the log signal handler from the widget
                if hasattr(widget, 'get_log_signal_handler'):
                    signal_handler = widget.get_log_signal_handler()
                break

        # Versuche Server zu starten (in Background Thread)
        def start_server():
            try:
                self.manager.add_endpoint(host, port, route, methods, initial_delay_sec, handler, server_name=inst.name, signal_handler=signal_handler)
                # Erfolg: Merke dass dieser Server läuft
                server_key = (host, port, route)
                self.running_servers.add(server_key)
            except Exception as e:
                # Fehler: Setze Widget zurück auf "gestoppt" und zeige Fehler
                if widget and hasattr(widget, 'set_running'):
                    widget.set_running(False)
                
                # Log den Fehler
                # Mögliche import Fehler beim ersten mal verhindern
                from ..service.logging_config import get_logger
                logger = get_logger("InstanceTabWidget")
                logger.error(f"Error starting server on {host}:{port}: {e}")
                
                # Thread-sicheres Error-Signal
                self.server_error_signal.error_occurred.emit(f"{host}:{port}", str(e))

        # Starte Server in Background Thread
        thread = threading.Thread(target=start_server)
        thread.start()

    def _on_server_error(self, server_info, error_message):
        """Thread-sichere Behandlung von Server-Fehlern"""
        from PySide6.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Server Start Error")
        msg.setText(f"Failed to start server on {server_info}")
        msg.setDetailedText(error_message)
        
        if "Address already in use" in error_message:
            msg.setInformativeText("The port is already in use. Please try a different port or stop the conflicting service.")
        
        msg.exec()

    def _remove_endpoint(self, inst):
        host, port, route, _, _, _, _ = self._get_endpoint_params(inst)
        self.manager.remove_endpoint(host, port, route)
        
        # Finde das entsprechende Widget für diese Instanz und setze es auf "gestoppt"
        for i, server_inst in enumerate(self.config.servers):
            if server_inst == inst:
                widget = self.tabs.widget(i)
                if hasattr(widget, 'set_running'):
                    widget.set_running(False)
                # Entferne Server aus der Laufzeit-Liste
                server_key = (host, port, route)
                self.running_servers.discard(server_key)
                break

    def _init_tabs(self):
        self.tabs.clear()
        # Korrigiere Zugriff auf Clients
        instances = self.config.servers if self.is_server else getattr(self.config, 'clients', [])
        for inst in instances:
            widget = ServerInstanceWidget(inst) if self.is_server else ClientInstanceWidget(inst)
            
            # Verbinde die Signale des Widgets
            if self.is_server:
                widget.start_requested.connect(self._on_server_start_requested)
                widget.stop_requested.connect(self._on_server_stop_requested)
                widget.params_changed.connect(self._on_server_params_changed)
            else:
                widget.start_requested.connect(self._on_client_start_requested)
                widget.stop_requested.connect(self._on_client_stop_requested)
                widget.params_changed.connect(self._on_client_params_changed)
            
            self.tabs.addTab(widget, inst.name)
            
            # Connect log signal handler to existing logger
            if hasattr(widget, 'get_log_signal_handler'):
                signal_handler = widget.get_log_signal_handler()
                if signal_handler:
                    from ..service.logging_config import add_signal_handler_to_existing_logger
                    logger_name = inst.name
                    add_signal_handler_to_existing_logger(logger_name, signal_handler)
        
        # Füge den + Tab hinzu
        self._add_plus_tab()

    def _add_plus_tab(self):
        """Fügt einen kleinen + Tab am Ende hinzu"""
        if not self._updating_plus_tab:
            self._updating_plus_tab = True
            # Erstelle einen leeren Widget für den + Tab
            plus_widget = QWidget()
            plus_index = self.tabs.addTab(plus_widget, "+")
            # Mache den + Tab nicht schließbar
            self.tabs.tabBar().setTabButton(plus_index, QTabBar.ButtonPosition.RightSide, None)
            self._updating_plus_tab = False

    def _is_plus_tab(self, index):
        """Prüft ob der gegebene Index der + Tab ist"""
        return index >= 0 and self.tabs.tabText(index) == "+"

    def _remove_plus_tab(self):
        """Entfernt den + Tab temporär"""
        if not self._updating_plus_tab:
            self._updating_plus_tab = True
            for i in range(self.tabs.count()):
                if self._is_plus_tab(i):
                    self.tabs.removeTab(i)
                    break
            self._updating_plus_tab = False

    def _add_instance(self):
        # Entferne + Tab temporär
        self._remove_plus_tab()
        
        base = "Server" if self.is_server else "Client"
        if self.is_server:
            existing = [inst.name for inst in self.config.servers]
            defaults = self.config.defaults
        else:
            existing = [inst.name for inst in getattr(self.config, 'clients', [])]
            defaults = self.config.raw['defaults']['client']
            server_methods = self.config.raw['defaults']['server']['methodes']
        idx = 1
        while f"{base}{idx}" in existing:
            idx += 1
        name = f"{base}{idx}"
        if self.is_server:
            inst = ServerInstance(name, defaults)
            self.config.servers.append(inst)
            widget = ServerInstanceWidget(inst)
            # Verbinde die Signale
            widget.start_requested.connect(self._on_server_start_requested)
            widget.stop_requested.connect(self._on_server_stop_requested)
        else:
            inst = ClientInstance(name, defaults, server_methods)
            self.config.clients.append(inst)
            widget = ClientInstanceWidget(inst)
            # Verbinde die Signale
            widget.start_requested.connect(self._on_client_start_requested)
            widget.stop_requested.connect(self._on_client_stop_requested)
        self.tabs.addTab(widget, name)
        
        # Füge + Tab wieder hinzu
        self._add_plus_tab()
        
        # Wechsle zum neuen Tab (nicht zum + Tab)
        self.tabs.setCurrentIndex(self.tabs.count()-2)

    def _clone_instance(self, source_index):
        """Klont eine Instanz basierend auf dem gegebenen Index"""
        if source_index < 0 or source_index >= self.tabs.count() or self._is_plus_tab(source_index):
            return
            
        # Entferne + Tab temporär
        self._remove_plus_tab()
            
        # Hole die Quell-Instanz
        if self.is_server:
            source_inst = self.config.servers[source_index]
            existing = [inst.name for inst in self.config.servers]
            base = source_inst.name
        else:
            source_inst = getattr(self.config, 'clients', [])[source_index]
            existing = [inst.name for inst in getattr(self.config, 'clients', [])]
            base = source_inst.name
            
        # Finde einen eindeutigen Namen für den Klon
        clone_name = f"{base}_copy"
        idx = 1
        while clone_name in existing:
            clone_name = f"{base}_copy{idx}"
            idx += 1
            
        # Erstelle neue Instanz mit kopierten Werten
        if self.is_server:
            # Kopiere alle Werte aus der Quell-Instanz
            clone_inst = ServerInstance(clone_name, source_inst.defaults)
            for key, value in source_inst.values.items():
                clone_inst.set_value(key, value)
            # Füge in die Liste an der richtigen Position ein (nach source_index)
            self.config.servers.insert(source_index + 1, clone_inst)
            widget = ServerInstanceWidget(clone_inst)
            # Verbinde die Signale
            widget.start_requested.connect(self._on_server_start_requested)
            widget.stop_requested.connect(self._on_server_stop_requested)
        else:
            # Kopiere alle Werte aus der Quell-Instanz
            clone_inst = ClientInstance(clone_name, source_inst.defaults, source_inst.server_methods)
            for key, value in source_inst.values.items():
                clone_inst.set_value(key, value)
            # Füge in die Liste an der richtigen Position ein (nach source_index)
            self.config.clients.insert(source_index + 1, clone_inst)
            widget = ClientInstanceWidget(clone_inst)
            # Verbinde die Signale
            widget.start_requested.connect(self._on_client_start_requested)
            widget.stop_requested.connect(self._on_client_stop_requested)
            
        # Füge Tab an der richtigen Position hinzu (nach source_index)
        self.tabs.insertTab(source_index + 1, widget, clone_name)
        
        # Füge + Tab wieder hinzu
        self._add_plus_tab()
        
        # Wechsle zum neuen Tab
        self.tabs.setCurrentIndex(source_index + 1)

    def _reset_instance(self):
        idx = self.tabs.currentIndex()
        if idx < 0:
            return
        self._reset_instance_by_index(idx)

    def _reset_instance_by_index(self, idx):
        """Reset eine Instanz basierend auf dem gegebenen Index"""
        if idx < 0 or idx >= self.tabs.count():
            return
            
        widget = self.tabs.widget(idx)
        # Unterscheide zwischen Server und Client
        if self.is_server:
            for key in widget.server.defaults:
                widget.server.set_value(key, widget.server.defaults[key])
            widget.host_edit.setText(widget.server.get_value('host'))
            widget.autostart_box.setChecked(widget.server.get_value('autostart'))
            widget.initial_delay_edit.setText(str(widget.server.get_value('initial_delay_sec')))
            widget.delay_edit.setText(str(widget.server.get_value('response_delay_sec')))
            widget.route_edit.setText(widget.server.get_value('route'))
            default_methods = widget.server.defaults.get('methodes', [])
            for i, cb in enumerate(widget.methods_checks):
                cb.setChecked(cb.text() in default_methods)
            widget.response_edit.setPlainText(widget.server.get_value('response') if widget.server.get_value('response') else "")
        else:
            for key in widget.client.defaults:
                widget.client.set_value(key, widget.client.defaults[key])
            widget.host_edit.setText(widget.client.get_value('host'))
            widget.autostart_box.setChecked(widget.client.get_value('autostart'))
            widget.initial_delay_edit.setText(str(widget.client.get_value('initial_delay_sec')))
            widget.loop_box.setChecked(widget.client.get_value('loop'))
            widget.period_edit.setText(str(widget.client.get_value('period_sec')))
            widget.route_edit.setText(widget.client.get_value('route'))
            for i, cb in enumerate(widget.methode_checks):
                cb.setChecked(cb.text() == widget.client.get_value('methode'))
            widget.request_edit.setPlainText(widget.client.get_value('request') if widget.client.get_value('request') else "")

    def _delete_instance(self):
        # Verhindere das Löschen des letzten Tabs (+ Plus-Tab)
        actual_tabs = self.tabs.count() - 1  # -1 für den + Tab
        if actual_tabs <= 1:
            return
            
        idx = self.tabs.currentIndex()
        if idx < 0 or self._is_plus_tab(idx):
            return
            
        # Entferne + Tab temporär
        self._remove_plus_tab()
        
        if self.is_server and self.manager:
            inst = self.config.servers[idx]
            self._remove_endpoint(inst)
        elif not self.is_server and self.manager:
            inst = getattr(self.config, 'clients', [])[idx]
            # Stoppe ggf. laufenden Client-Thread vor dem Löschen
            self.manager.stop_client(inst.name)
            # Entferne auch aus der Laufzeit-Liste
            self.running_clients.discard(inst.name)
        # Zugriff auf Clients robust machen
        if self.is_server:
            instances = self.config.servers
        else:
            instances = getattr(self.config, 'clients', [])
        del instances[idx]
        self.tabs.removeTab(idx)
        
        # Füge + Tab wieder hinzu
        self._add_plus_tab()

    def _on_close_tab(self, idx):
        # Verhindere das Schließen des + Tabs
        if self._is_plus_tab(idx):
            return
        self.tabs.setCurrentIndex(idx)
        self._delete_instance()

    def _on_tab_changed(self, idx):
        # Wenn der + Tab ausgewählt wird, erstelle eine neue Instanz
        if idx >= 0 and self._is_plus_tab(idx):
            self._add_instance()
            return

    def _on_defaults_changed(self):
        """Called when default values are changed."""
        # Update all instance widgets to reflect new defaults
        for i in range(self.tabs.count()):
            # Skip the + tab
            if self._is_plus_tab(i):
                continue
                
            widget = self.tabs.widget(i)
            if self.is_server:
                # Update server instance defaults reference
                widget.server.defaults = self.config.raw['defaults']['server']
                # Refresh widgets that display default values
                self._refresh_instance_widget(widget)
            else:
                # Update client instance defaults reference
                widget.client.defaults = self.config.raw['defaults']['client']
                # Update server_methods reference for client instances
                widget.client.server_methods = self.config.raw['defaults']['server']['methodes']
                # Refresh widgets that display default values
                self._refresh_instance_widget(widget)

    def _refresh_instance_widget(self, widget):
        """Refresh an instance widget to show updated default values."""
        if self.is_server:
            # Überspringe die Aktualisierung wenn der Server läuft
            if hasattr(widget, 'is_running') and widget.is_running:
                return
                
            # Update the values dictionary with new defaults for unchanged fields
            for key, default_value in widget.server.defaults.items():
                if widget.server.is_default(key):
                    widget.server.values[key] = default_value
 
            # Update text for fields that are at default values
            if widget.server.is_default('host'):
                widget.host_edit.setText(widget.server.get_value('host'))
            if widget.server.is_default('autostart'):
                widget.autostart_box.setChecked(widget.server.get_value('autostart'))
            if widget.server.is_default('initial_delay_sec'):
                widget.initial_delay_edit.setText(str(widget.server.get_value('initial_delay_sec')))
            if widget.server.is_default('response_delay_sec'):
                widget.delay_edit.setText(str(widget.server.get_value('response_delay_sec')))
            if widget.server.is_default('route'):
                widget.route_edit.setText(widget.server.get_value('route'))
            if widget.server.is_default('response'):
                widget.response_edit.setPlainText(widget.server.get_value('response') or "")
                
            # Update methods checkboxes if at default
            if widget.server.is_default('methodes'):
                current_methods = widget.server.get_value('methodes') or []
                for cb in widget.methods_checks:
                    cb.setChecked(cb.text() in current_methods)
        else:
            # Überspringe die Aktualisierung wenn der Client läuft
            if hasattr(widget, 'is_running') and widget.is_running:
                return
                
            # Update the values dictionary with new defaults for unchanged fields
            for key, default_value in widget.client.defaults.items():
                if widget.client.is_default(key):
                    widget.client.values[key] = default_value
            
            # Update text for fields that are at default values
            if widget.client.is_default('host'):
                widget.host_edit.setText(widget.client.get_value('host'))
            if widget.client.is_default('autostart'):
                widget.autostart_box.setChecked(widget.client.get_value('autostart'))
            if widget.client.is_default('initial_delay_sec'):
                widget.initial_delay_edit.setText(str(widget.client.get_value('initial_delay_sec')))
            if widget.client.is_default('loop'):
                widget.loop_box.setChecked(widget.client.get_value('loop'))
            if widget.client.is_default('period_sec'):
                widget.period_edit.setText(str(widget.client.get_value('period_sec')))
            if widget.client.is_default('route'):
                widget.route_edit.setText(widget.client.get_value('route'))
            if widget.client.is_default('request'):
                widget.request_edit.setPlainText(widget.client.get_value('request') or "")
                
            # Update method checkboxes if at default
            if widget.client.is_default('methode'):
                current_method = widget.client.get_value('methode')
                for cb in widget.methode_checks:
                    cb.setChecked(cb.text() == current_method)

class MainWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        from ..service.rest_server_manager import RestServerManager
        from ..service.rest_client_manager import RestClientManager
        from .. import __version__
        self.manager = RestServerManager() #TODO: renaming to avoid confusion
        self.client_manager = RestClientManager()
        self.setWindowTitle(f"REST Tester (rest-tester {__version__})")
        splitter = QSplitter(Qt.Horizontal)
        self.server_tabs = InstanceTabWidget(config, is_server=True, manager=self.manager)
        self.client_tabs = InstanceTabWidget(config, is_server=False, manager=self.client_manager)
        splitter.addWidget(self.server_tabs)
        splitter.addWidget(self.client_tabs)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def closeEvent(self, event):
        self.config.save()
        if hasattr(self, 'manager') and self.manager:
            self.manager.shutdown_all()
        if hasattr(self, 'client_manager') and self.client_manager:
            self.client_manager.stop_all()
        event.accept()
