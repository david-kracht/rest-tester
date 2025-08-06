"""
REST Endpoint Utilities Module

This module provides utilities for handling REST API endpoints with template rendering,
request processing, and response generation capabilities. It implements the Template
Method pattern for consistent request handling across different endpoint types.

Key Features:
    - Jinja2 template-based response rendering with extensive context
    - Comprehensive request data extraction and logging
    - Configurable response delays for testing scenarios
    - Instance-specific state management with counters
    - Error handling and recovery for robust endpoint behavior
    - Structured logging integration for monitoring and debugging

Classes:
    - EndpointHandler: Core endpoint processing with template rendering
    
Functions:
    - make_generic_handler: Factory function for creating endpoint handlers

Dependencies:
    - Jinja2: Template engine for dynamic response generation
    - logging_config: Centralized logging configuration
    - Standard library modules for template context (time, random, json, etc.)
"""

import time
import random
import json
import math
import os
import sys
import datetime
from typing import Dict, Any, Callable

from jinja2 import Environment
from .logging_config import get_logger


class EndpointHandler:
    """
    Handles REST endpoint requests with template-based response generation.
    
    This class implements the Template Method pattern for endpoint processing,
    providing a consistent framework for request handling while allowing
    flexibility in response generation through Jinja2 templates.
    
    The handler maintains instance-specific state (counter) and provides
    comprehensive request logging and error handling capabilities.
    
    Attributes:
        response (str): Jinja2 template string for response generation
        response_delay_sec (float): Configurable delay before sending response
        server_name (str): Optional server identifier for logging context
        counter (int): Instance-specific request counter for template context
        env (Environment): Jinja2 environment for template rendering
        logger: Configured logger instance for this handler
        
    Template Context Variables:
        The following variables are available in response templates:
        - request: Complete request information dictionary
        - time: Python time module for timestamp operations
        - random: Python random module for dynamic value generation
        - json: JSON module for data manipulation
        - math: Mathematical functions and constants
        - os: Operating system interface functions
        - sys: System-specific parameters and functions
        - datetime: Date and time manipulation
        - counter: Instance-specific request counter
    """
    
    def __init__(self, response: str, response_delay_sec: float, server_name: str = None) -> None:
        """
        Initialize endpoint handler with response template and configuration.
        
        Args:
            response: Jinja2 template string for generating responses
            response_delay_sec: Delay in seconds before sending response
            server_name: Optional identifier for logging and identification
            
        Note:
            The Jinja2 environment is configured with autoescape=False to allow
            raw JSON generation in templates without HTML escaping.
        """
        self.response = response
        self.response_delay_sec = response_delay_sec
        self.server_name = server_name
        self.counter = 0  # Instance-specific counter for request tracking
        
        # Configure Jinja2 environment for JSON template rendering
        self.env = Environment(autoescape=False)
        
        # Create dedicated logger for this handler instance
        logger_name = f"{server_name}" if server_name else "EndpointHandler"
        self.logger = get_logger(logger_name)
    
    def handle_request(self, request) -> str:
        """
        Process incoming HTTP request and generate template-based response.
        
        This is the main entry point for request processing, implementing the
        Template Method pattern with the following steps:
        1. Convert request to structured dictionary format
        2. Render response template with comprehensive context
        3. Log request and response for monitoring
        4. Apply configured response delay
        5. Update instance state (counter)
        
        Args:
            request: Flask request object containing HTTP request data
            
        Returns:
            str: JSON-formatted response string ready for HTTP transmission
            
        Template Context:
            The response template has access to all request data plus:
            - Standard Python modules (time, random, json, math, os, sys, datetime)
            - Instance counter for request tracking
            - Complete request information in structured format
            
        Error Handling:
            Any exceptions during template rendering or processing are caught
            and converted to structured error responses for client consumption.
        """
        formatted_request = self._request_to_dict(request)
        
        try:
            # Render response template with comprehensive context
            json_template_response = self.env.from_string(self.response)
            rendered_json_response = json_template_response.render(
                request=formatted_request,
                time=time,
                random=random,
                json=json,
                math=math,
                os=os,
                sys=sys,
                datetime=datetime,
                counter=self.counter
            )
            
            # Log incoming request for monitoring and debugging
            self.logger.info(f"Request: {formatted_request}")
            
            # Parse and format response for pretty-printing
            formatted_response = json.loads(rendered_json_response)
            pretty_response = json.dumps(formatted_response, indent=2, ensure_ascii=False)
            
            # Log outgoing response with structured formatting
            log_output = f"----- Response JSON -----\n{pretty_response}\n-----------------------"
            self.logger.info(log_output)
            
            # Apply configured response delay for testing scenarios
            time.sleep(self.response_delay_sec)
            
            # Increment counter for next request tracking
            self.counter += 1
            
            return pretty_response
            
        except Exception as e:
            # Handle template rendering or processing errors gracefully
            self.logger.error(f"Error handling request: {e}")
            error_response = {"error": "Internal server error", "message": str(e)}
            return json.dumps(error_response)
    
    def _request_to_dict(self, request) -> Dict[str, Any]:
        """
        Convert Flask request object to comprehensive dictionary representation.
        
        Extracts all relevant information from the HTTP request including headers,
        query parameters, form data, JSON payload, and routing information.
        This structured format is used both for logging and as template context.
        
        Args:
            request: Flask request object to convert
            
        Returns:
            Dict[str, Any]: Comprehensive request information including:
                - method: HTTP method (GET, POST, etc.)
                - view_args: URL route parameters
                - url: Complete request URL
                - url_rule: Flask URL rule pattern
                - path: Request path component
                - remote_addr: Client IP address
                - headers: All HTTP headers as dictionary
                - query_params: URL query parameters
                - cookies: Request cookies
                - form_data: Form data for POST/PUT requests (if present)
                - json_data: JSON payload (if present)
                
        Error Handling:
            If request parsing fails, returns a minimal error dictionary
            to prevent template rendering failures.
        """
        try:
            # Extract comprehensive request information
            all_info = {
                'method': request.method,
                'view_args': request.view_args,
                'url': request.url,
                'url_rule': request.url_rule.rule,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'headers': dict(request.headers),
                'query_params': request.args.to_dict(),
                'cookies': request.cookies
            }
            
            # Add form data for POST/PUT requests when available
            if request.method in ['POST', 'PUT'] and request.form:
                all_info['form_data'] = request.form.to_dict()
            
            # Add JSON payload if request contains JSON data
            if request.is_json:
                all_info['json_data'] = request.json
                
            return all_info
            
        except Exception as e:
            # Provide fallback for parsing errors to prevent template failures
            self.logger.warning(f"Error parsing request: {e}")
            return {"error": "Failed to parse request"}


def make_generic_handler(response: str, response_delay_sec: float, server_name: str = None) -> Callable:
    """
    Factory function for creating endpoint handler functions.
    
    This factory creates a closure that encapsulates an EndpointHandler instance,
    providing a clean interface for Flask route registration while maintaining
    handler state and configuration.
    
    Args:
        response: Jinja2 template string for response generation
        response_delay_sec: Delay in seconds before sending responses
        server_name: Optional server identifier for logging context
        
    Returns:
        Callable: Function that can be used as Flask route handler
        
    Usage:
        handler = make_generic_handler(
            response='{"status": "ok", "counter": {{counter}}}',
            response_delay_sec=0.1,
            server_name="TestServer"
        )
        app.route('/api/test')(handler)
        
    Note:
        The returned function maintains state through the enclosed
        EndpointHandler instance, allowing per-endpoint counters
        and configuration while providing a simple interface.
    """
    handler_instance = EndpointHandler(response, response_delay_sec, server_name)
    return handler_instance.handle_request
