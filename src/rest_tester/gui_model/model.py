"""
Configuration Model Module

This module provides the core data model classes for managing REST server and client
instances within the REST Tester application. It implements a comprehensive configuration
management system with YAML persistence, default value handling, and instance lifecycle
management.

Key Features:
    - Server and client instance modeling with configuration management
    - YAML-based persistence with block-style formatting for templates
    - Default value system with inheritance and override capabilities
    - Dynamic configuration updates with validation
    - Method validation for client instances based on server capabilities
    - Efficient storage by only persisting non-default values
    - YAML formatting preservation for human-readable configuration files

Architecture:
    - ServerInstance: Individual server configuration with template support
    - ClientInstance: Individual client configuration with method validation
    - ConfigModel: Central configuration manager with YAML persistence
    - Integration with ruamel.yaml for advanced YAML formatting control

Data Model:
    - Hierarchical configuration with defaults and instance overrides
    - Template content stored as literal scalar strings in YAML
    - Automatic cleanup of default values to minimize configuration size
    - Thread-safe configuration access and updates

Classes:
    - ServerInstance: Server configuration management with template support
    - ClientInstance: Client configuration management with method validation
    - ConfigModel: Central configuration persistence and management

Dependencies:
    - ruamel.yaml: Advanced YAML processing with formatting preservation
    - pathlib: Modern path handling for configuration files
    - LiteralScalarString: YAML block-style formatting for templates
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


class ServerInstance:
    """
    Server instance configuration model with template support and default management.
    
    This class manages individual server instance configurations including host settings,
    response templates, timing parameters, and HTTP method support. It provides a
    hierarchical configuration system where instance-specific values override defaults,
    and only non-default values are persisted to optimize configuration file size.
    
    The model supports Jinja2 response templates stored as YAML literal scalar strings
    for better readability and editing in configuration files.
    
    Attributes:
        name (str): Unique identifier for this server instance
        defaults (Dict): Default configuration values
        config (Dict): Instance-specific configuration overrides
        values (Dict): Merged configuration (defaults + overrides)
        
    Configuration Keys:
        - host: Server host address and port
        - route: Endpoint route pattern
        - response: Jinja2 response template
        - response_delay_sec: Delay before sending responses
        - initial_delay_sec: Delay before server starts
        - methodes: List of supported HTTP methods
        - autostart: Whether to start automatically
    """
    
    def __init__(self, name: str, defaults: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize server instance with name, defaults, and optional configuration.
        
        Args:
            name: Unique identifier for this server instance
            defaults: Default configuration values from global defaults
            config: Instance-specific configuration overrides
        """
        self.name = name
        self.defaults = defaults
        self.config = config or {}
        self.values = dict(defaults)
        self.values.update(config or {})

    def set_value(self, key: str, value: Any) -> None:
        """
        Set configuration value with automatic default management.
        
        This method updates both the instance configuration and merged values.
        If the new value matches the default, it removes the key from instance
        configuration to keep the configuration file minimal.
        
        Args:
            key: Configuration key to update
            value: New value to set
            
        Optimization:
            Values that match defaults are automatically removed from
            instance configuration to minimize file size and complexity.
        """
        if value == self.defaults.get(key):
            self.config.pop(key, None)
        else:
            self.config[key] = value
        self.values[key] = value

    def get_value(self, key: str) -> Any:
        """
        Get configuration value with default fallback.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Value from instance config, or default if not overridden
        """
        return self.values.get(key, self.defaults.get(key))

    def get_default(self, key: str) -> Any:
        """
        Get default value for specified key.
        
        Args:
            key: Configuration key to get default for
            
        Returns:
            Default value for the specified key
        """
        return self.defaults.get(key)

    def is_default(self, key: str) -> bool:
        """
        Check if current value matches default.
        
        Args:
            key: Configuration key to check
            
        Returns:
            True if current value is default, False if overridden
        """
        return key not in self.config or not self.config[key]

    def to_yaml(self) -> Dict[str, Any]:
        """
        Convert instance to YAML-serializable dictionary.
        
        This method creates a dictionary suitable for YAML serialization,
        including only non-default values and formatting response templates
        as literal scalar strings for better readability.
        
        Returns:
            Dictionary with instance name and non-default configuration values
            
        YAML Formatting:
            Response templates are stored as LiteralScalarString objects
            to ensure block-style formatting in the YAML file.
        """
        data = {k: v for k, v in self.config.items() if v != self.defaults.get(k)}
        if 'response' in data:
            data['response'] = LiteralScalarString(data['response'])
        data['name'] = self.name
        return data


class ClientInstance:
    """
    Client instance configuration model with method validation and template support.
    
    This class manages individual client instance configurations including target host,
    request templates, timing parameters, and HTTP method selection. It provides
    validation to ensure selected methods are compatible with available server methods.
    
    The model supports Jinja2 request templates stored as YAML literal scalar strings
    and automatically validates HTTP method selection against server capabilities.
    
    Attributes:
        name (str): Unique identifier for this client instance
        defaults (Dict): Default configuration values
        server_methods (List[str]): Available HTTP methods from server configuration
        config (Dict): Instance-specific configuration overrides
        values (Dict): Merged configuration (defaults + overrides)
        
    Configuration Keys:
        - host: Target server host address and port
        - route: Request route template
        - request: Jinja2 request payload template
        - methode: Selected HTTP method (validated against server_methods)
        - period_sec: Interval between requests in loop mode
        - initial_delay_sec: Delay before first request
        - loop: Whether to continuously send requests
        - autostart: Whether to start automatically
    """
    
    def __init__(self, name: str, defaults: Dict[str, Any], server_methods: List[str], 
                 config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize client instance with method validation.
        
        Args:
            name: Unique identifier for this client instance
            defaults: Default configuration values from global defaults
            server_methods: List of available HTTP methods from server configuration
            config: Instance-specific configuration overrides
            
        Method Validation:
            If the configured method is not in server_methods, it automatically
            selects the first available method to ensure compatibility.
        """
        self.name = name
        self.defaults = defaults
        self.server_methods = server_methods  # List of allowed methods
        self.config = config or {}
        self.values = dict(defaults)
        self.values.update(config or {})
        
        # Set method to first value from server_methods if not set or invalid
        if self.values.get('methode') not in self.server_methods:
            self.values['methode'] = self.server_methods[0] if self.server_methods else None

    def set_value(self, key: str, value: Any) -> None:
        """
        Set configuration value with method validation and default management.
        
        This method updates both the instance configuration and merged values.
        For HTTP method selection, it validates against available server methods.
        Values matching defaults are automatically removed from instance config.
        
        Args:
            key: Configuration key to update
            value: New value to set
            
        Method Validation:
            When setting 'methode', validates against server_methods and
            falls back to first available method if invalid.
            
        Optimization:
            Values that match defaults are automatically removed from
            instance configuration to minimize file size.
        """
        if key == 'methode' and value not in self.server_methods:
            value = self.server_methods[0] if self.server_methods else None
        if value == self.defaults.get(key):
            self.config.pop(key, None)
        else:
            self.config[key] = value
        self.values[key] = value

    def get_value(self, key: str) -> Any:
        """
        Get configuration value with default fallback.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Value from instance config, or default if not overridden
        """
        return self.values.get(key, self.defaults.get(key))

    def get_default(self, key: str) -> Any:
        """
        Get default value for specified key.
        
        Args:
            key: Configuration key to get default for
            
        Returns:
            Default value for the specified key
        """
        return self.defaults.get(key)

    def is_default(self, key: str) -> bool:
        """
        Check if current value matches default.
        
        Args:
            key: Configuration key to check
            
        Returns:
            True if current value is default, False if overridden
        """
        return key not in self.config or not self.config[key]

    def to_yaml(self) -> Dict[str, Any]:
        """
        Convert instance to YAML-serializable dictionary.
        
        This method creates a dictionary suitable for YAML serialization,
        including only non-default values and formatting request templates
        as literal scalar strings for better readability.
        
        Returns:
            Dictionary with instance name and non-default configuration values
            
        YAML Formatting:
            Request templates are stored as LiteralScalarString objects
            to ensure block-style formatting in the YAML file.
        """
        data = {k: v for k, v in self.config.items() if v != self.defaults.get(k)}
        if 'request' in data:
            data['request'] = LiteralScalarString(data['request'])
        data['name'] = self.name
        return data


class ConfigModel:
    """
    Central configuration model with YAML persistence and instance management.
    
    This class provides the main interface for managing REST Tester configuration
    including server and client instances, default values, and YAML file persistence.
    It handles loading, saving, and maintaining consistency between in-memory
    configuration and file storage.
    
    The model uses ruamel.yaml for advanced YAML processing including quote
    preservation, proper indentation, and block-style formatting for templates.
    It maintains separate collections for server and client instances with
    proper default value inheritance.
    
    Attributes:
        path (Path): Path to the YAML configuration file
        yaml (YAML): Configured YAML processor with formatting options
        raw (Dict): Raw YAML data structure
        defaults (Dict): Server default configuration values
        servers (List[ServerInstance]): Collection of server instances
        clients (List[ClientInstance]): Collection of client instances
        
    YAML Structure:
        - defaults: Global default values for servers and clients
        - servers: List of server instance configurations
        - clients: List of client instance configurations
    """
    
    def __init__(self, path: Union[str, Path]) -> None:
        """
        Initialize configuration model with YAML file path.
        
        Args:
            path: Path to the YAML configuration file
            
        YAML Configuration:
            - Preserves quotes and formatting from original file
            - Uses consistent indentation (2 spaces for mappings, 4 for sequences)
            - Applies 2-space offset for nested structures
        """
        self.path = Path(path)
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.load()

    def load(self) -> None:
        """
        Load configuration from YAML file and create instance objects.
        
        This method reads the YAML configuration file and creates appropriate
        ServerInstance and ClientInstance objects with proper default value
        inheritance and method validation.
        
        Instance Creation:
            - Servers: Created with server defaults
            - Clients: Created with client defaults and server method validation
            - Names are extracted and removed from instance configuration
            - Default values are inherited and can be overridden per instance
        """
        with open(self.path, 'r') as f:
            self.raw = self.yaml.load(f)
            
        # Extract server defaults
        self.defaults = self.raw['defaults']['server']
        
        # Create server instances
        self.servers = []
        for s in self.raw.get('servers', []):
            name = s['name']
            config = dict(s)
            config.pop('name')
            self.servers.append(ServerInstance(name, self.defaults, config))
            
        # Create client instances with method validation
        self.clients = []
        defaults = self.raw['defaults']['client']
        server_methods = self.raw['defaults']['server']['methodes']
        for c in self.raw.get('clients', []):
            name = c['name']
            config = dict(c)
            config.pop('name')
            self.clients.append(ClientInstance(name, defaults, server_methods, config))

    def save(self) -> None:
        """
        Save current configuration to YAML file with proper formatting.
        
        This method converts all instances back to YAML-serializable format
        and writes the configuration file with proper template formatting.
        
        Template Formatting:
            - Response templates: Converted to LiteralScalarString for block style
            - Request templates: Converted to LiteralScalarString for block style
            - Preserves YAML formatting and structure
            
        File Operations:
            - Updates raw YAML structure with current instance data
            - Writes file with preserved formatting and indentation
            - Ensures templates are human-readable in configuration file
        """
        # Format response templates for servers as block-style YAML
        for s in self.servers:
            if 'response' in s.values:
                val = s.values['response']
                if not isinstance(val, str):
                    val = str(val)
                s.values['response'] = LiteralScalarString(val)

        # Format request templates for clients as block-style YAML
        for c in self.clients:
            if 'request' in c.values:
                val = c.values['request']
                if not isinstance(val, str):
                    val = str(val)
                c.values['request'] = LiteralScalarString(val)

        # Convert instances to YAML format and update raw structure
        servers = [s.to_yaml() for s in self.servers]
        clients = [c.to_yaml() for c in self.clients]
        self.raw['servers'] = servers
        self.raw['clients'] = clients

        # Write formatted YAML to file
        with open(self.path, 'w') as f:
            self.yaml.dump(self.raw, f)
