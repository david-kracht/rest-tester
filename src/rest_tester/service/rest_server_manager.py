"""
REST Server Management Module

This module provides comprehensive REST server management capabilities using Flask
and threading for concurrent server operation. It implements a multi-server
architecture where each server runs in its own thread with dynamic endpoint
registration and management.

Key Features:
    - Multi-threaded server architecture for concurrent operation
    - Dynamic endpoint registration and handler updates at runtime
    - Thread-safe operations with proper locking mechanisms
    - Graceful server shutdown with resource cleanup
    - Socket reuse configuration for better port management
    - Comprehensive error handling and logging integration
    - Context management for Flask application lifecycle

Architecture:
    - ServerThread: Individual server instances with Flask applications
    - RestServerManager: Centralized management of multiple servers
    - Dynamic endpoint routing with method-specific handlers
    - Thread-safe endpoint registration and updates

Classes:
    - ServerThread: Individual threaded Flask server with endpoint management
    - RestServerManager: Central coordinator for multiple server instances

Dependencies:
    - Flask: Web framework for HTTP server implementation
    - threading: Concurrent execution and synchronization
    - werkzeug: WSGI utilities and server implementation
    - logging_config: Centralized logging configuration
"""

import threading
import logging
import time
import socket
from typing import Dict, Tuple, Callable, List, Optional, Any

from flask import Flask, request
from werkzeug.serving import make_server
from .logging_config import get_logger


class ServerThread(threading.Thread):
    """
    Individual threaded Flask server with dynamic endpoint management.
    
    This class implements a Flask server that runs in its own thread, providing
    isolation and concurrent operation capabilities. It supports dynamic endpoint
    registration, handler updates, and graceful shutdown procedures.
    
    The server maintains thread-safe endpoint management using locks and provides
    comprehensive error handling for robust operation in multi-server environments.
    
    Attributes:
        host (str): Server host address
        port (int): Server port number
        logger: Configured logger for this server instance
        app (Flask): Flask application instance
        srv: Werkzeug server instance
        _shutdown (threading.Event): Shutdown coordination mechanism
        _endpoints (Dict): Endpoint registry with methods and handlers
        _endpoints_lock (threading.Lock): Thread safety for endpoint operations
        ctx: Flask application context for request handling
    """
    
    def __init__(self, host: str, port: int, logger) -> None:
        """
        Initialize server thread with host, port, and logger configuration.
        
        Args:
            host: Server host address (e.g., 'localhost', '0.0.0.0')
            port: Server port number
            logger: Configured logger instance for this server
            
        Note:
            - Creates unique Flask app name based on host:port
            - Suppresses Werkzeug request logs to avoid log pollution
            - Registers shutdown endpoint for graceful termination
            - Initializes thread-safe endpoint registry
        """
        super().__init__()
        self.host = host
        self.port = port
        self.logger = logger
        self.app = Flask(f"server_{host}_{port}")
        
        # Suppress Werkzeug request logs to prevent log pollution
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        
        self.srv = None
        self._shutdown = threading.Event()
        self._endpoints: Dict[str, Tuple[List[str], Callable]] = {}  # endpoint: (methods, handler)
        
        # Thread-safe lock for endpoint operations
        self._endpoints_lock = threading.Lock()
        
        # Register dummy shutdown endpoint for graceful termination
        self.app.add_url_rule("/__shutdown__", "__shutdown__", 
                             lambda: "shutting down", methods=["GET"])

    def _dispatch(self, **args) -> Tuple[str, int]:
        """
        Internal request dispatcher for dynamic endpoint routing.
        
        This method handles incoming requests by matching them against registered
        endpoints and delegating to appropriate handlers. It provides thread-safe
        access to the endpoint registry and proper error responses.
        
        Args:
            **args: URL route arguments from Flask routing
            
        Returns:
            Tuple[str, int]: Response content and HTTP status code
            
        Thread Safety:
            Uses endpoint lock to ensure consistent access to handler registry
            during concurrent operations.
        """
        with self._endpoints_lock:
            handler_info = self._endpoints.get(request.url_rule.rule)

        if handler_info and request.method in handler_info[0]:
            # Delegate request to registered handler
            return handler_info[1](request)
        
        return ("Not found", 404)

    def add_endpoint(self, endpoint: str, methods: List[str], 
                    initial_delay_sec: float, handler: Callable) -> None:
        """
        Register new endpoint with specified methods and handler.
        
        This method provides thread-safe endpoint registration with optional
        initialization delay. It supports both new endpoint creation and
        handler updates for existing endpoints.
        
        Args:
            endpoint: URL pattern for the endpoint (Flask route format)
            methods: List of HTTP methods supported by this endpoint
            initial_delay_sec: Delay before endpoint becomes active
            handler: Callable that processes requests for this endpoint
            
        Thread Safety:
            Uses endpoint lock to prevent race conditions during registration
            and ensure consistent state updates.
            
        Note:
            - Supports all HTTP methods: GET, POST, PUT, DELETE
            - Logs endpoint registration and updates for monitoring
            - Allows handler updates for existing endpoints
        """
        time.sleep(initial_delay_sec)
        
        with self._endpoints_lock:
            if endpoint not in self._endpoints:
                self.logger.info(f"Register endpoint {endpoint} on {self.host}:{self.port}")
                self.app.add_url_rule(endpoint, endpoint, view_func=self._dispatch, 
                                    methods=["GET", "POST", "PUT", "DELETE"])
            else:
                self.logger.info(f"Update handler for endpoint {endpoint} on {self.host}:{self.port}")
            
            self._endpoints[endpoint] = (methods, handler)

    def update_endpoint_handler(self, endpoint: str, handler: Callable) -> bool:
        """
        Update handler for existing endpoint during runtime.
        
        This method enables dynamic handler updates without server restart,
        maintaining the same HTTP methods while replacing the handler function.
        
        Args:
            endpoint: URL pattern of the endpoint to update
            handler: New handler function for processing requests
            
        Returns:
            bool: True if update successful, False if endpoint not found
            
        Thread Safety:
            Uses endpoint lock to ensure atomic handler updates without
            interrupting concurrent request processing.
        """
        with self._endpoints_lock:
            if endpoint in self._endpoints:
                methods = self._endpoints[endpoint][0]
                self._endpoints[endpoint] = (methods, handler)
                self.logger.info(f"Updated handler for endpoint {endpoint} on {self.host}:{self.port}")
                return True
        return False

    def remove_endpoint(self, endpoint: str) -> None:
        """
        Remove endpoint from server registry.
        
        Args:
            endpoint: URL pattern of the endpoint to remove
            
        Thread Safety:
            Uses endpoint lock for thread-safe removal operations.
        """
        with self._endpoints_lock:
            if endpoint in self._endpoints:
                self.logger.info(f"Unregister endpoint {endpoint} on {self.host}:{self.port}")
                self._endpoints.pop(endpoint)

    def run(self) -> None:
        """
        Main server execution loop with comprehensive error handling.
        
        This method implements the server's main execution lifecycle:
        1. Creates and configures Werkzeug server instance
        2. Sets socket options for better port reuse
        3. Establishes Flask application context
        4. Runs request handling loop until shutdown
        5. Performs cleanup and resource management
        
        Error Handling:
            - OSError: Handles port conflicts and network issues
            - General exceptions: Logs unexpected errors
            - Finally block: Ensures proper cleanup regardless of exit path
            
        Socket Configuration:
            - SO_REUSEADDR: Allows immediate port reuse after shutdown
            - SO_REUSEPORT: Enables port sharing (when available)
        """
        try:
            # Create Werkzeug server instance
            self.srv = make_server(self.host, self.port, self.app)
            
            # Configure socket options for better port management
            self.srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                # SO_REUSEPORT is not available on all systems
                self.srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                # Ignore if SO_REUSEPORT is not available
                pass
            
            # Establish Flask application context for request handling
            self.ctx = self.app.app_context()
            self.ctx.push()
            
            self.logger.info(f"Server started on {self.host}:{self.port}")
            
            # Main request handling loop
            while not self._shutdown.is_set():
                self.srv.handle_request()
                
        except OSError as e:
            if "Address already in use" in str(e):
                self.logger.error(f"Port {self.port} is already in use on {self.host}")
            else:
                self.logger.error(f"Server error on {self.host}:{self.port}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected server error on {self.host}:{self.port}: {e}")
        finally:
            self._cleanup()
            self.logger.info(f"Server stopped on {self.host}:{self.port}")

    def _cleanup(self) -> None:
        """
        Comprehensive resource cleanup for server shutdown.
        
        This method ensures proper cleanup of server resources including
        socket closure and Flask context management. It handles cleanup
        errors gracefully to prevent hanging during shutdown.
        
        Cleanup Steps:
            1. Close and cleanup Werkzeug server instance
            2. Manage Flask application context lifecycle
            3. Handle cleanup errors without propagating exceptions
            
        Error Handling:
            - Server cleanup errors are logged but not propagated
            - Context cleanup errors are silently handled (usually harmless)
            - Automatic context cleanup occurs when thread terminates
        """
        # Close server socket and cleanup server instance
        try:
            if hasattr(self, 'srv') and self.srv:
                self.srv.server_close()
                self.srv = None
        except Exception as e:
            self.logger.error(f"Error during server cleanup: {e}")
        
        # Cleanup Flask application context (only if still active)
        try:
            if hasattr(self, 'ctx') and self.ctx:
                # Check if context is still active before popping
                from flask import has_app_context
                if has_app_context():
                    self.ctx.pop()
                self.ctx = None
        except Exception:
            # Ignore context cleanup errors - they're usually harmless
            # Context will be automatically cleaned up when thread ends
            pass

    def shutdown(self) -> None:
        """
        Initiate graceful server shutdown procedure.
        
        This method implements a multi-step shutdown process:
        1. Set shutdown event to stop request loop
        2. Send graceful shutdown request to server
        3. Force close server socket as fallback
        
        The graceful shutdown attempts to complete current requests
        before terminating, while the socket closure ensures shutdown
        completion even if graceful termination fails.
        
        Error Handling:
            - Shutdown request failures are ignored (expected behavior)
            - Socket closure errors are silently handled
            - Multiple shutdown calls are safely ignored
        """
        if self._shutdown.is_set():
            return  # Already in shutdown process
            
        self._shutdown.set()
        
        # Attempt graceful shutdown via shutdown endpoint
        try:
            import requests
            requests.get(f"http://{self.host}:{self.port}/__shutdown__", timeout=1)
        except Exception:
            # Request failure is expected/acceptable - server will still shutdown
            pass
        
        # Ensure server socket closure (redundant with _cleanup(), but safer)
        try:
            if hasattr(self, 'srv') and self.srv:
                self.srv.server_close()
        except Exception:
            pass


class RestServerManager:
    """
    Central coordinator for multiple REST server instances.
    
    This class provides high-level server management capabilities including
    server lifecycle management, endpoint registration across servers, and
    coordinated shutdown procedures. It maintains a registry of active servers
    and provides thread-safe operations for multi-server environments.
    
    Key Features:
        - Multi-server lifecycle management
        - Dynamic endpoint registration and updates
        - Server health monitoring and cleanup
        - Coordinated shutdown across all servers
        - Thread-safe server registry operations
        
    Attributes:
        servers (Dict): Registry of active servers keyed by (host, port)
        logger: Configured logger for manager operations
    """
    
    def __init__(self) -> None:
        """
        Initialize server manager with empty server registry.
        
        Creates the central server registry and logging configuration
        for coordinated multi-server management.
        """
        self.servers: Dict[Tuple[str, int], ServerThread] = {}  # (host, port): ServerThread
        self.logger = get_logger("RestServerManager")

    def _get_server(self, host: str, port: int) -> Optional[ServerThread]:
        """
        Retrieve server instance for given host and port.
        
        Args:
            host: Server host address
            port: Server port number
            
        Returns:
            Optional[ServerThread]: Server instance if exists, None otherwise
        """
        return self.servers.get((host, port))

    def add_endpoint(self, host: str, port: int, endpoint: str, methods: List[str],
                    initial_delay_sec: float, handler: Callable, 
                    server_name: Optional[str] = None, 
                    signal_handler: Optional[Any] = None) -> None:
        """
        Add endpoint to server, creating server instance if necessary.
        
        This method provides comprehensive endpoint management including
        automatic server creation, health monitoring, and error recovery.
        It ensures robust operation in multi-server environments.
        
        Args:
            host: Server host address
            port: Server port number
            endpoint: URL pattern for the endpoint
            methods: List of supported HTTP methods
            initial_delay_sec: Delay before endpoint activation
            handler: Request handler function
            server_name: Optional server identifier for logging
            signal_handler: Optional signal handler for logging integration
            
        Raises:
            RuntimeError: If server cannot be started (e.g., port in use)
            
        Server Management:
            - Creates new server if none exists for host:port
            - Monitors server health and removes dead servers
            - Configures logging with custom names when provided
            - Validates server startup before proceeding
        """
        key = (host, port)
        
        # Check for and remove dead server instances
        if key in self.servers:
            existing_server = self.servers[key]
            if not existing_server.is_alive():
                self.logger.info(f"Removing dead server thread for {host}:{port}")
                del self.servers[key]
        
        # Create new server if needed
        if key not in self.servers:
            # Use custom server name if provided, otherwise default to host:port
            logger_name = server_name if server_name else f"{host}:{port}"
            logger = get_logger(logger_name, signal_handler=signal_handler)
            server = ServerThread(host, port, logger)
            self.servers[key] = server
            server.start()
            
            # Validate server startup with brief wait
            time.sleep(0.2)
            if not server.is_alive():
                # Server failed to start - cleanup and raise error
                del self.servers[key]
                raise RuntimeError(f"Failed to start server on {host}:{port} - port may be in use")
                
        try:
            # Add endpoint to running server
            self.servers[key].add_endpoint(endpoint, methods, initial_delay_sec, handler)
        except Exception as e:
            # Clean up server if endpoint addition fails
            if key in self.servers:
                server = self.servers[key]
                server.shutdown()
                server.join(timeout=2)
                del self.servers[key]
            raise e

    def update_endpoint_handler(self, host: str, port: int, endpoint: str, 
                               handler: Callable) -> bool:
        """
        Update handler for existing endpoint during runtime.
        
        Args:
            host: Server host address
            port: Server port number
            endpoint: URL pattern of endpoint to update
            handler: New handler function
            
        Returns:
            bool: True if update successful, False if server/endpoint not found
        """
        key = (host, port)
        server = self.servers.get(key)
        if server:
            return server.update_endpoint_handler(endpoint, handler)
        return False

    def remove_endpoint(self, host: str, port: int, endpoint: str) -> None:
        """
        Remove endpoint from server and shutdown server if no endpoints remain.
        
        This method provides intelligent server lifecycle management by
        automatically shutting down servers that no longer have active
        endpoints, optimizing resource usage.
        
        Args:
            host: Server host address
            port: Server port number
            endpoint: URL pattern of endpoint to remove
            
        Automatic Cleanup:
            - Removes endpoint from server registry
            - Monitors remaining endpoint count
            - Shuts down server if no endpoints remain
            - Cleans up server registry after shutdown
        """
        key = (host, port)
        server = self.servers.get(key)
        if server:
            server.remove_endpoint(endpoint)
            # Brief wait to ensure endpoint removal is processed
            time.sleep(0.1)
            
            # Shutdown server if no endpoints remain
            if not server._endpoints:
                self.logger.info(f"No more endpoints, shutting down server {host}:{port}")
                server.shutdown()
                server.join(timeout=3)  # Extended timeout for graceful shutdown
                if key in self.servers:
                    del self.servers[key]

    def shutdown_all(self) -> None:
        """
        Shutdown all managed servers with coordinated termination.
        
        This method ensures orderly shutdown of all server instances
        with proper resource cleanup and registry management.
        
        Shutdown Process:
            - Iterates through all active servers
            - Initiates shutdown for each server
            - Waits for graceful termination with timeout
            - Clears server registry after all shutdowns complete
        """
        for key, server in list(self.servers.items()):
            self.logger.info(f"Shutting down server {key[0]}:{key[1]}")
            server.shutdown()
            server.join(timeout=3)
        self.servers.clear()
