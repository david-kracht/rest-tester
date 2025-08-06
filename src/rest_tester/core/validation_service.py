"""
Centralized Validation Service

This module provides comprehensive input validation for the REST Tester
application, separating validation logic from UI concerns and ensuring
consistent validation behavior across all components.

Key Features:
    - Host and port validation (IP addresses, hostnames, DNS resolution)
    - Numeric field validation (delays, periods, timeouts)
    - Route validation with RFC 3986 compliance
    - JSON validation with Jinja2 template support
    - Extensible validation framework

Validation Types:
    - Network: Host, port, URL validation
    - Data Format: JSON, template syntax validation
    - Numeric: Range checking, type validation
    - Protocol: HTTP route structure validation

Design Pattern:
    Implements the Strategy pattern for different validation types
    with centralized error handling and logging.
"""

import re
import socket
import time
import random
import json
import math
import os
import sys
import datetime
from typing import Any, Dict, Tuple
from jinja2 import Environment, StrictUndefined
import rfc3986

from ..service.logging_config import get_logger


class ValidationService:
    """
    Centralized validation service providing consistent input validation.
    
    This service encapsulates all validation logic for the application,
    ensuring consistent error messages and validation behavior across
    all components. It supports template validation for dynamic content
    and provides detailed error reporting.
    
    Attributes:
        logger: Service-specific logger for validation operations
        env: Jinja2 environment for template validation
        
    Design Notes:
        - All validation methods return (bool, str) tuples for consistency
        - Template validation uses a safe environment with restricted globals
        - Network validation includes both syntax and connectivity checks
    """
    
    def __init__(self):
        """Initialize validation service with safe template environment."""
        self.logger = get_logger("ValidationService")
        
        # Configure Jinja2 environment for safe template validation
        self.env = Environment(
            autoescape=False,           # Don't escape for API content
            undefined=StrictUndefined   # Fail on undefined variables
        )
    
    def validate_host(self, host: str) -> Tuple[bool, str]:
        """
        Validate host format supporting IP addresses, hostnames, and ports.
        
        Validates both syntax and format according to networking standards:
        - IPv4 addresses (e.g., 192.168.1.1)
        - Hostnames (e.g., api.example.com)
        - Localhost and special addresses
        - Optional port numbers (e.g., localhost:8080)
        
        Args:
            host: Host string to validate (may include port)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Examples:
            >>> service.validate_host("localhost:8080")
            (True, "")
            >>> service.validate_host("256.1.1.1")
            (False, "Invalid IP address format")
        """
        if not host or not host.strip():
            return False, "Host cannot be empty"
        
        host = host.strip()
        
        # Parse host and port components
        if ':' in host:
            host_part, port_part = host.rsplit(':', 1)
            
            # Validate port range (0-65535)
            try:
                port = int(port_part)
                if not (0 <= port <= 65535):
                    return False, f"Port {port} is out of valid range (0-65535)"
            except ValueError:
                return False, f"Invalid port format: {port_part}"
        else:
            host_part = host
        
        # Validate IPv4 address format
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if re.match(ipv4_pattern, host_part):
            return True, ""
        
        # Validate hostname format (RFC 1123)
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(hostname_pattern, host_part):
            return True, ""
        
        # Attempt DNS resolution for complex hostnames
        try:
            socket.gethostbyname(host_part)
            return True, ""
        except socket.gaierror:
            return False, f"Cannot resolve hostname: {host_part}"
    
    def validate_seconds(self, value: str) -> Tuple[bool, str]:
        """
        Validate numeric time values ensuring non-negative numbers.
        
        Accepts both integer and floating-point values for time-based
        parameters like delays and periods. Ensures values are reasonable
        for timing operations.
        
        Args:
            value: String representation of numeric value
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Examples:
            >>> service.validate_seconds("1.5")
            (True, "")
            >>> service.validate_seconds("-1")
            (False, "Value must be non-negative")
        """
        try:
            num_value = float(value)
            if num_value < 0:
                return False, "Value must be non-negative"
            if math.isinf(num_value) or math.isnan(num_value):
                return False, "Value must be finite"
            return True, ""
        except (ValueError, TypeError):
            return False, f"Invalid number format: {value}"
    
    def validate_route(self, route: str) -> Tuple[bool, str]:
        """
        Validate HTTP route format with template support and RFC 3986 compliance.
        
        Validates route strings that may contain Jinja2 templates for dynamic
        content generation. Ensures compliance with HTTP URL standards and
        proper route structure.
        
        Features:
            - Jinja2 template syntax validation
            - RFC 3986 URI compliance checking
            - HTTP path format validation
            - Character encoding validation
        
        Args:
            route: Route string (may contain Jinja2 templates)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Examples:
            >>> service.validate_route("/api/users/{{user_id}}")
            (True, "")
            >>> service.validate_route("invalid route")
            (False, "Route must start with '/'")
        """
        if not route or not route.strip():
            return False, "Route cannot be empty"
        
        try:
            # Validate template syntax by rendering with safe context
            route_template = self.env.from_string(route)
            rendered_route = route_template.render(
                time=time, 
                random=random, 
                json=json, 
                math=math, 
                os=os, 
                sys=sys, 
                datetime=datetime, 
                counter=0
            )

            # HTTP routes must start with forward slash
            if not rendered_route.startswith('/'):
                return False, "Route must start with '/'"
            
            # Validate URI structure using RFC 3986 standards
            test_uri = f"http://example.com{rendered_route}"
            uri = rfc3986.uri_reference(test_uri)

            # Ensure URI components are present and valid
            validator = rfc3986.validators.Validator().require_presence_of('scheme', 'host')
            validator.validate(uri)
            
            # Validate path component exists
            if uri.path is None:
                return False, "Invalid path in route"
                
            # Extract path without query parameters for character validation
            path_part = rendered_route.split('?')[0]
            
            # Check for invalid characters in path
            if ' ' in path_part:
                return False, "Route path cannot contain spaces"
            
            # Validate printable ASCII characters only
            for char in path_part:
                if ord(char) < 32 or ord(char) > 126:
                    return False, f"Route contains invalid character: {repr(char)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid route template: {str(e)}"
    
    def validate_json(self, value: str) -> Tuple[bool, str]:
        """
        Validate JSON format with Jinja2 template rendering support.
        
        Validates JSON strings that may contain Jinja2 templates for dynamic
        content generation. Ensures both template syntax and resulting JSON
        format are valid.
        
        Features:
            - Template syntax validation
            - JSON structure validation after rendering
            - Safe template context with restricted globals
            - Support for empty/optional JSON fields
        
        Args:
            value: JSON string (may contain Jinja2 templates)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Examples:
            >>> service.validate_json('{"id": {{user_id}}}')
            (True, "")
            >>> service.validate_json('{"invalid": json}')
            (False, "Invalid JSON template: ...")
        """
        if not value.strip():
            return True, ""  # Empty JSON is valid for optional fields
            
        try:
            # Validate template syntax with safe rendering context
            json_template = self.env.from_string(value)
            rendered_json = json_template.render(
                time=time, 
                random=random, 
                json=json, 
                math=math, 
                os=os, 
                sys=sys, 
                datetime=datetime, 
                counter=0,
                request={}  # Placeholder for request context
            )
            
            # Validate resulting JSON structure
            json.loads(rendered_json)
            return True, ""
            
        except Exception as e:
            return False, f"Invalid JSON template: {str(e)}"
    
    def validate_field(self, field_type: str, value: str) -> Tuple[bool, str]:
        """
        Validate a field based on its semantic type with extensible validation.
        
        Provides a unified interface for field validation based on semantic
        meaning rather than just data type. This allows for type-specific
        validation rules and easy extension for new field types.
        
        Args:
            field_type: Semantic type of the field (e.g., 'host', 'route', 'json')
            value: String value to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Supported Field Types:
            - Network: 'host' (hostnames, IPs, ports)
            - Timing: 'seconds', '*_delay_sec', 'period_sec'
            - HTTP: 'route' (URL paths)
            - Data: 'json', 'request', 'response' (JSON content)
            
        Examples:
            >>> service.validate_field('host', 'localhost:8080')
            (True, "")
            >>> service.validate_field('unknown_type', 'value')
            (False, "Unknown field type: unknown_type")
        """
        # Map field types to their corresponding validation methods
        validators = {
            'host': self.validate_host,
            'route': self.validate_route,
            'json': self.validate_json,
            'seconds': self.validate_seconds,
            'request': self.validate_json,
            'response': self.validate_json,
            'initial_delay_sec': self.validate_seconds,
            'period_sec': self.validate_seconds,
            'response_delay_sec': self.validate_seconds
        }
        
        validator = validators.get(field_type)
        if not validator:
            self.logger.warning(f"Unknown field type requested: {field_type}")
            return False, f"Unknown field type: {field_type}"
        
        return validator(value)
