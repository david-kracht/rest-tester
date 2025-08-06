"""
REST Tester Service Facade Module

This module implements the Facade design pattern to provide a unified, simplified
interface for coordinating and managing the REST Tester service layer components.
It acts as a single entry point for all service operations, abstracting the
complexity of managing multiple service managers.

Key Components:
    ServiceFacade: Main facade class that coordinates service layer operations

Architecture Overview:
    The ServiceFacade follows the Facade pattern by providing a simplified interface
    to a complex subsystem. It coordinates between RestServerManager and 
    RestClientManager, providing unified operations like shutdown, status reporting,
    and service lifecycle management.

Design Benefits:
    - Simplified client interface to complex service layer
    - Centralized service coordination and lifecycle management
    - Consistent error handling and logging across services
    - Single point of control for application shutdown
    - Abstraction of service layer implementation details

Usage Pattern:
    The facade is typically instantiated once per application and used by
    higher-level components (like GUI controllers) to perform service operations
    without needing to understand the underlying service manager implementations.

Dependencies:
    - RestServerManager: HTTP server lifecycle management
    - RestClientManager: HTTP client request management  
    - Logging system: Centralized logging for service operations

Design Patterns:
    - Facade Pattern: Simplified interface to complex service subsystem
    - Singleton-like Usage: Typically one instance per application
    - Delegation Pattern: Forwards operations to appropriate service managers
"""

from typing import Optional, Callable, Dict, Any
from ..service.rest_server_manager import RestServerManager
from ..service.rest_client_manager import RestClientManager
from ..service.logging_config import get_logger


class ServiceFacade:
    """
    Facade for coordinating REST server and client service managers.
    
    This class implements the Facade design pattern to provide a unified,
    simplified interface for managing both REST server and client operations.
    It abstracts the complexity of coordinating multiple service managers
    and provides centralized lifecycle management.
    
    Key Responsibilities:
        - Coordinate server and client manager operations
        - Provide unified shutdown and cleanup procedures
        - Centralize service status reporting
        - Abstract service layer complexity from higher-level components
        - Ensure consistent error handling and logging
        
    Architecture:
        The facade maintains references to both RestServerManager and
        RestClientManager instances, delegating appropriate operations
        to each while coordinating cross-service operations like shutdown.
        
    Thread Safety:
        The facade delegates thread safety to the underlying service managers.
        Individual operations are thread-safe, but complex multi-step operations
        should be coordinated by the caller if needed.
        
    Lifecycle:
        1. Initialization: Creates and configures service managers
        2. Operation: Provides access to individual managers
        3. Shutdown: Coordinates graceful shutdown of all services
        
    Attributes:
        logger: Logger instance for facade operations
        _server_manager: Internal REST server manager instance
        _client_manager: Internal REST client manager instance
    """
    
    def __init__(self) -> None:
        """
        Initialize the service facade with server and client managers.
        
        This constructor creates instances of both RestServerManager and
        RestClientManager, configures logging, and prepares the facade
        for coordinating service operations.
        
        Setup Process:
            1. Initialize logger for facade operations
            2. Create RestServerManager instance
            3. Create RestClientManager instance
            4. Prepare for service coordination
            
        The managers are created in a ready state but no services are
        started automatically. Service startup is handled through the
        individual manager interfaces accessed via properties.
        """
        self.logger = get_logger("ServiceFacade")
        self._server_manager = RestServerManager()
        self._client_manager = RestClientManager()
    
    @property
    def server_manager(self) -> RestServerManager:
        """
        Access the REST server manager instance.
        
        Returns:
            RestServerManager: The managed server instance
            
        This property provides access to the underlying server manager
        for operations specific to REST server management like endpoint
        registration, handler updates, and server lifecycle control.
        
        Usage:
            Use this property when you need direct access to server-specific
            operations that aren't provided through the facade interface.
        """
        return self._server_manager
    
    @property
    def client_manager(self) -> RestClientManager:
        """
        Access the REST client manager instance.
        
        Returns:
            RestClientManager: The managed client instance
            
        This property provides access to the underlying client manager
        for operations specific to REST client management like request
        configuration, client lifecycle control, and parameter updates.
        
        Usage:
            Use this property when you need direct access to client-specific
            operations that aren't provided through the facade interface.
        """
        return self._client_manager
    
    def shutdown_all(self) -> None:
        """
        Gracefully shutdown all running servers and clients.
        
        This method provides coordinated shutdown of all services managed
        by the facade. It ensures proper cleanup order and handles errors
        gracefully to prevent incomplete shutdown states.
        
        Shutdown Process:
            1. Log shutdown initiation
            2. Stop all client operations first (to avoid connection errors)
            3. Shutdown all server operations
            4. Log successful completion
            5. Handle and log any errors that occur
            
        Error Handling:
            If errors occur during shutdown, they are logged but don't prevent
            the shutdown process from continuing. This ensures maximum cleanup
            even in error conditions.
            
        Thread Safety:
            This method coordinates shutdown across multiple managers and
            should be called from a single thread to ensure proper ordering.
        """
        try:
            self.logger.info("Shutting down all services...")
            
            # Stop clients first to avoid connection errors
            self._client_manager.stop_all()
            
            # Then shutdown servers to free resources
            self._server_manager.shutdown_all()
            
            self.logger.info("All services shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during service shutdown: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive status information for all managed services.
        
        Returns:
            Dict containing current status of servers and clients
            
        This method provides a unified view of the current state of all
        services managed by the facade. It's useful for monitoring,
        debugging, and providing status information to users.
        
        Status Information:
            - servers: Number of currently running server instances
            - clients: Number of currently active client instances
            
        Usage:
            This method is typically used by monitoring systems, GUI status
            displays, or administrative interfaces to show current service
            state without needing to query individual managers.
            
        Thread Safety:
            This method is read-only and thread-safe. It provides a snapshot
            of the current state at the time of the call.
        """
        return {
            'servers': len(self._server_manager.servers),
            'clients': len(self._client_manager.clients)
        }