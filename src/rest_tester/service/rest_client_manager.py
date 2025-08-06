"""
REST Client Management Module

This module provides comprehensive REST client management capabilities for automated
HTTP request generation and testing. It implements a multi-threaded client architecture
with template-based request generation, dynamic parameter updates, and comprehensive
response handling.

Key Features:
    - Multi-threaded client architecture for concurrent request generation
    - Jinja2 template-based request and URL rendering with extensive context
    - Dynamic parameter updates during runtime without client restart
    - Configurable request intervals and looping behavior
    - Comprehensive response handling with custom callbacks
    - Thread-safe operations with proper locking mechanisms
    - Instance-specific counters for request tracking and template context

Architecture:
    - ClientThread: Individual threaded HTTP client with template rendering
    - RestClientManager: Central coordinator for multiple client instances
    - Template-based request generation with mathematical and temporal context
    - Callback system for response processing and lifecycle management

Classes:
    - ClientThread: Individual threaded HTTP client with template capabilities
    - RestClientManager: Central management of multiple client instances

Dependencies:
    - requests: HTTP client library for request execution
    - Jinja2: Template engine for dynamic request generation
    - threading: Concurrent execution and synchronization
    - logging_config: Centralized logging configuration
"""

import threading
import time
import random
import json
import math
import os
import sys
import datetime
from typing import Dict, Optional, Callable, Any

import requests
from jinja2 import Environment
from .logging_config import get_logger


class ClientThread(threading.Thread):
    """
    Individual threaded HTTP client with template-based request generation.
    
    This class implements a flexible HTTP client that can generate requests
    using Jinja2 templates, providing dynamic content generation with access
    to mathematical functions, time operations, and request-specific data.
    
    The client supports both single-shot and continuous looping operation
    with configurable intervals and comprehensive parameter update capabilities
    during runtime.
    
    Attributes:
        name (str): Unique identifier for this client instance
        host (str): Target server host address
        route (str): Request route template (supports Jinja2 templating)
        method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
        request_data (str): Request payload template (Jinja2 format)
        period_sec (float): Interval between requests in loop mode
        loop (bool): Whether to continuously send requests
        initial_delay_sec (float): Delay before first request
        counter (int): Request counter for template context
        logger: Configured logger instance for this client
        env (Environment): Jinja2 environment for template rendering
        
    Template Context Variables:
        All templates have access to:
        - time: Python time module for timestamp operations
        - random: Random number generation for dynamic values
        - json: JSON manipulation functions
        - math: Mathematical functions and constants
        - os: Operating system interface
        - sys: System parameters and functions
        - datetime: Date and time manipulation
        - counter: Instance-specific request counter
    """
    
    def __init__(self, name: str, host: str, route: str, method: str, 
                 request_data: str, period_sec: float = 1.0, loop: bool = False,
                 initial_delay_sec: float = 0.0, on_response: Optional[Callable] = None,
                 on_finished: Optional[Callable] = None, counter: int = 0,
                 signal_handler: Optional[Any] = None) -> None:
        """
        Initialize HTTP client thread with configuration and callbacks.
        
        Args:
            name: Unique identifier for this client instance
            host: Target server host (e.g., 'localhost:8080')
            route: Request route template with Jinja2 support
            method: HTTP method for requests
            request_data: Request payload template (JSON format recommended)
            period_sec: Interval between requests in loop mode
            loop: Whether to continuously send requests
            initial_delay_sec: Delay before first request execution
            on_response: Callback function for response processing
            on_finished: Callback function when client completes
            counter: Starting counter value for template context
            signal_handler: Optional signal handler for logging integration
            
        Template Support:
            Both route and request_data support Jinja2 templating with
            access to mathematical functions, time operations, and counters.
        """
        super().__init__()
        self.name = name
        self.host = host
        self.route = route
        self.method = method.upper()
        self.request_data = request_data
        self.period_sec = period_sec
        self.loop = loop
        self._stop_event = threading.Event()
        self.initial_delay_sec = initial_delay_sec
        self.on_response = on_response
        self.on_finished = on_finished  # Callback when thread completes
        self.counter = counter
        
        # Setup dedicated logger for this client instance
        self.logger = get_logger(name, signal_handler=signal_handler)

        # Thread-safe lock for parameter updates during runtime
        self._params_lock = threading.Lock()

        # Configure Jinja2 environment for template rendering
        self.env = Environment(autoescape=False)

    def update_params(self, **kwargs) -> None:
        """
        Update client parameters dynamically during runtime.
        
        This method allows modification of client behavior without restart,
        enabling dynamic testing scenarios and parameter adjustment based
        on runtime conditions or user interaction.
        
        Args:
            **kwargs: Parameter updates including:
                - route: New route template
                - method: HTTP method change
                - request_data: New request payload template
                - period_sec: Updated request interval
                
        Thread Safety:
            Uses parameter lock to ensure atomic updates without
            interfering with ongoing request generation.
        """
        with self._params_lock:
            if 'route' in kwargs:
                self.route = kwargs['route']
            if 'method' in kwargs:
                self.method = kwargs['method'].upper()
            if 'request_data' in kwargs:
                self.request_data = kwargs['request_data']
            if 'period_sec' in kwargs:
                self.period_sec = kwargs['period_sec']

    def run(self) -> None:
        """
        Main client execution loop with comprehensive request processing.
        
        This method implements the client's main execution lifecycle:
        1. Validates configuration parameters
        2. Applies initial delay if configured
        3. Executes request generation loop (single or continuous)
        4. Renders templates with comprehensive context
        5. Sends HTTP requests with proper error handling
        6. Processes responses via callbacks or logging
        7. Manages loop timing and termination
        
        Template Processing:
            - Request data: Rendered as Jinja2 template with full context
            - URL: Supports dynamic URL generation with templates
            - Context includes: time, random, math, datetime, counter, etc.
            
        Error Handling:
            - Configuration validation before execution
            - Template rendering error recovery
            - HTTP request exception handling
            - Graceful loop termination on errors
        """
        # Validate required configuration
        if not self.host or not self.route:
            self.logger.error("Host and route must be set before starting.")
            return
        
        # Apply initial delay before first request
        time.sleep(self.initial_delay_sec)
        
        while not self._stop_event.is_set():
            try:
                # Create thread-safe copy of parameters for this request
                with self._params_lock:
                    current_host = self.host
                    current_route = self.route
                    current_method = self.method
                    current_request_data = self.request_data
                    current_period_sec = self.period_sec
                
                # Construct base URL from host and route
                url = f"http://{current_host}{current_route}"
                
                # Process request payload with template rendering
                data = None
                json_data = None
                headers = {"Content-Type": "application/json"}
                
                if current_request_data:
                    try:
                        # Render request payload template with comprehensive context
                        json_template_request = self.env.from_string(current_request_data)
                        rendered_json_request = json_template_request.render(
                            time=time, 
                            random=random, 
                            json=json, 
                            math=math, 
                            os=os, 
                            sys=sys, 
                            datetime=datetime, 
                            counter=self.counter
                        )
                        json_data = json.loads(rendered_json_request)
                    except Exception:
                        # Fallback to raw data if JSON parsing fails
                        data = current_request_data

                # Render URL template for dynamic URL generation
                json_template_url = self.env.from_string(url)
                rendered_url = json_template_url.render(
                    time=time, 
                    random=random, 
                    json=json, 
                    math=math, 
                    os=os, 
                    sys=sys, 
                    datetime=datetime, 
                    counter=self.counter
                )

                # Execute HTTP request with rendered data
                resp = requests.request(current_method, rendered_url, 
                                      json=json_data, data=data, headers=headers)
                
                # Increment counter for next request
                self.counter += 1

                # Log outgoing request data for monitoring
                if json_data:
                    pretty_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                    log_output = f"----- Request JSON -----\n{pretty_json}\n------------------------"
                    self.logger.info(log_output)
                else:
                    self.logger.info("No JSON data")

                # Process response via callback or default logging
                if self.on_response:
                    self.on_response(self.name, resp)
                else:
                    self.logger.info(f"Response: {resp.status_code} {resp.text}")

            except Exception as e:
                self.logger.error(f"Error: {e}")

            # Exit loop if not in continuous mode
            if not self.loop:
                break
                
            # Wait for next iteration in loop mode
            time.sleep(current_period_sec)
        
        # Invoke completion callback if thread finishes naturally (not via stop())
        if self.on_finished and not self._stop_event.is_set():
            self.on_finished(self.name)

    def stop(self) -> None:
        """
        Stop client execution gracefully.
        
        Sets the stop event to terminate the request loop at the next
        iteration checkpoint, allowing current request to complete.
        """
        self._stop_event.set()


class RestClientManager:
    """
    Central coordinator for multiple REST client instances.
    
    This class provides high-level client management capabilities including
    client lifecycle management, parameter updates, and coordinated shutdown
    procedures. It maintains a registry of active clients and provides
    global counter management for request tracking.
    
    Key Features:
        - Multi-client lifecycle management
        - Global counter coordination across clients
        - Dynamic parameter updates for running clients
        - Coordinated shutdown and cleanup
        - Thread-safe client registry operations
        
    Attributes:
        clients (Dict): Registry of active clients keyed by name
        counter (int): Global counter for client initialization
        logger: Configured logger for manager operations
    """
    
    def __init__(self) -> None:
        """
        Initialize client manager with empty client registry.
        
        Creates the central client registry and global counter
        for coordinated multi-client management.
        """
        self.clients: Dict[str, ClientThread] = {}  # name: ClientThread
        self.counter = 0  # Global counter for all clients
        self.logger = get_logger("RestClientManager")

    def start_client(self, name: str, host: str, route: str, method: str,
                    request_data: str, period_sec: float = 1.0, loop: bool = False,
                    initial_delay_sec: float = 0.0, on_response: Optional[Callable] = None,
                    on_finished: Optional[Callable] = None, 
                    signal_handler: Optional[Any] = None) -> None:
        """
        Start new client instance with specified configuration.
        
        This method creates and starts a new HTTP client thread with
        comprehensive configuration options. It automatically stops
        any existing client with the same name before creating the new one.
        
        Args:
            name: Unique identifier for the client
            host: Target server host address
            route: Request route template (supports Jinja2)
            method: HTTP method for requests
            request_data: Request payload template (JSON recommended)
            period_sec: Interval between requests in loop mode
            loop: Whether to continuously send requests
            initial_delay_sec: Delay before first request
            on_response: Callback for response processing
            on_finished: Callback when client completes
            signal_handler: Optional signal handler for logging
            
        Client Management:
            - Automatically stops existing client with same name
            - Assigns unique counter value for template context
            - Registers client in manager registry
            - Starts client thread immediately
        """
        # Stop any existing client with the same name
        self.stop_client(name)
        
        # Create new client thread with current counter value
        thread = ClientThread(
            name=name, 
            host=host, 
            route=route, 
            method=method, 
            request_data=request_data, 
            period_sec=period_sec, 
            loop=loop, 
            initial_delay_sec=initial_delay_sec, 
            on_response=on_response, 
            on_finished=on_finished, 
            counter=self.counter, 
            signal_handler=signal_handler
        )
        
        # Increment global counter for next client
        self.counter += 1 
        
        # Register and start client
        self.clients[name] = thread
        thread.start()

    def update_client_params(self, name: str, **kwargs) -> bool:
        """
        Update parameters for running client dynamically.
        
        This method enables real-time parameter modification for active
        clients without requiring restart, supporting dynamic testing
        scenarios and runtime configuration changes.
        
        Args:
            name: Identifier of client to update
            **kwargs: Parameters to update (route, method, request_data, period_sec)
            
        Returns:
            bool: True if update successful, False if client not found/active
        """
        thread = self.clients.get(name)
        if thread and thread.is_alive():
            thread.update_params(**kwargs)
            return True
        return False

    def stop_client(self, name: str) -> None:
        """
        Stop specific client and remove from registry.
        
        This method gracefully stops a client thread and performs
        cleanup including registry removal and thread termination.
        
        Args:
            name: Identifier of client to stop
            
        Cleanup Process:
            - Initiates graceful stop via stop event
            - Waits for thread termination with timeout
            - Removes client from registry
        """
        thread = self.clients.get(name)
        if thread:
            thread.stop()
            thread.join(timeout=1)
            del self.clients[name]
            
    def stop_all(self) -> None:
        """
        Stop all managed clients with coordinated shutdown.
        
        This method ensures orderly shutdown of all client instances
        by iterating through the registry and stopping each client.
        """
        for name in list(self.clients.keys()):
            self.stop_client(name)