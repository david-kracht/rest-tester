# REST Tester

**A comprehensive GUI application for testing and developing REST APIs with integrated server and client functionality**

## Abstract

REST Tester is a powerful, Qt-based desktop application designed to streamline REST API development and testing workflows. It provides a unified environment where developers can simultaneously run multiple REST servers, execute automated client requests, and monitor real-time interactions through an intuitive graphical interface. The application features template-based request/response generation, multi-threaded operations, and comprehensive logging capabilities, making it an essential tool for API development, testing, and debugging.


![REST Tester Main Window](./doc/window.jpg)
---

## Table of Contents

1. [Key Features](#key-features)
2. [Architecture Overview](#architecture-overview)
3. [Installation](#installation)
4. [Quick Start Guide](#quick-start-guide)
5. [User Guide](#user-guide)
   - [Server Management](#server-management)
   - [Client Management](#client-management)
   - [Configuration System](#configuration-system)
   - [Monitoring and Logging](#monitoring-and-logging)
6. [Use Cases](#use-cases)
7. [Development](#development)
   - [Development Setup](#development-setup)
   - [Project Structure](#project-structure)
   - [Contributing](#contributing)
8. [Deployment](#deployment)
9. [License](#license)
10. [Support](#support)

---

## Features

- **REST Client**: Multi-threaded HTTP client with Jinja2 template-based request generation
- **REST Server**: Flask-based mock server with dynamic endpoint registration and template responses
- **Jinja2 Templates**: Dynamic request/response generation with Python module access and request context
- **Configuration Management**: YAML-based configuration with default templates
- **Request Context**: Full access to HTTP request information in server templates
- **Logging**: Comprehensive logging for debugging and monitoring
- **GUI Interface**: PySide-based interface for test management

---

## Architecture Overview

REST Tester follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│                GUI Layer                    │
│  ┌─────────────────┐ ┌─────────────────────┐│
│  │ Instance Tabs   │ │ Configuration Panel ││
│  │ Log Viewers     │ │ Status Monitors     ││
│  └─────────────────┘ └─────────────────────┘│
├─────────────────────────────────────────────┤
│                Core Layer                   │
│  ┌─────────────────┐ ┌─────────────────────┐│
│  │ App Manager     │ │ Service Facade      ││
│  │ Config Locator  │ │ Validation Service  ││
│  └─────────────────┘ └─────────────────────┘│
├─────────────────────────────────────────────┤
│               Service Layer                 │
│  ┌─────────────────┐ ┌─────────────────────┐│
│  │ REST Server     │ │ REST Client         ││
│  │ Manager         │ │ Manager             ││
│  └─────────────────┘ └─────────────────────┘│
└─────────────────────────────────────────────┘
```

---

## Jinja2 Template System

REST Tester uses Jinja2 templates for dynamic request and response generation, providing powerful flexibility for testing scenarios.

### Available Template Variables

Both client and server templates have access to a rich context of Python modules and special variables:

| Variable | Type | Description | Example Usage |
|----------|------|-------------|---------------|
| `time` | Module | Python time module | `{{time.time()}}` |
| `random` | Module | Python random module | `{{random.randint(1, 100)}}` |
| `json` | Module | Python json module | `{{request.json}}` |
| `math` | Module | Python math module | `{{math.sin(counter)}}` |
| `os` | Module | Python os module | `{{os.environ.get('USER')}}` |
| `sys` | Module | Python sys module | `{{sys.platform}}` |
| `datetime` | Module | Python datetime module | `{{datetime.datetime.now()}}` |
| `counter` | Integer | Auto-incrementing counter | `{{counter}}` |

### Server-Specific Variables

Server response templates additionally have access to:

| Variable | Type | Description | Example Usage |
|----------|------|-------------|---------------|
| `request` | Object | Complete Flask request object | `{{request.method}}` |
| `request.method` | String | HTTP method | `{{request.method}}` |
| `request.path` | String | Request path | `{{request.path}}` |
| `request.headers` | Dict | HTTP headers | `{{request.headers}}` |
| `request.args` | Dict | Query parameters | `{{request.args}}` |
| `request.json` | Dict | JSON payload | `{{request.json}}` |
| `request.remote_addr` | String | Client IP address | `{{request.remote_addr}}` |

### Template Examples

**Client Request Template:**
```json
{
  "timestamp": {{time.time()}},
  "sequence": {{counter}},
  "value": {{ 3.5 * math.fmod(counter, 17)}},
  "random_id": {{random.randint(1000, 9999)}},
  "created_at": "{{datetime.datetime.now().isoformat()}}",
  "math_result": {{math.sqrt(counter + 1)}}
}
```

**Server Response Template:**
```json
{
  "received": {{request | tojson}},
  "processed_at": "{{datetime.datetime.now().isoformat()}}",
  "wave_value": {{ 5 * math.sin(math.pi/20.0 * counter)}},
  "counter": {{counter}},
  "method": "{{request.method}}",
  "path": "{{request.path}}",
  "client_ip": "{{request.remote_addr}}"
}
```

**Advanced Request Context Access:**
```json
{
  "request_info": {
    "method": "{{request.method}}",
    "url": "{{request.url}}",
    "headers": {{request.headers | tojson}},
    "query_params": {{request.args | tojson}},
    "json_data": {{request.json | tojson}}
  },
  "server_response": {
    "timestamp": {{time.time()}},
    "random_value": {{random.random()}},
    "counter": {{counter}}
  }
}
```

---

## Installation

### Prerequisites

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB available space

### Option 1: Production Release (Recommended)

Install the latest stable release from PyPI:

```bash
pip install rest-tester
```

### Option 2: Development Version

For the latest development features from Test PyPI:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rest-tester
```

### Option 3: Development Setup

For developers who want to contribute or customize:

```bash
# Clone the repository
git clone https://github.com/david-kracht/rest-tester.git
cd rest-tester

# Install with Poetry (recommended)
poetry install
poetry run rest-tester

# Or install with pip in development mode
pip install -e .
rest-tester
```

### Verification

Verify your installation by running:

```bash
rest-tester --version
```

---

## Quick Start Guide

### 1. Launch the Application

```bash
rest-tester
```

Or run directly with Python:

```bash
python -m rest_tester.main
```

### 2. Create Your First Server

1. Navigate to the **Server** tab
2. Click the **"+"** button to add a new server instance
3. Configure the server settings:
   - **Host**: `localhost:5000`
   - **Route**: `/api/hello`
   - **Methods**: Select `GET` and `POST`
   - **Response Template**:
     ```json
     {
       "message": "Hello from REST Tester!",
       "timestamp": "{{ time.time() }}",
       "method": "{{ request.method }}"
     }
     ```
4. Click **Start** to launch the server

### 3. Create a Client to Test Your Server

1. Navigate to the **Client** tab
2. Click the **"+"** button to add a new client instance
3. Configure the client settings:
   - **Host**: `localhost:5000`
   - **Route**: `/api/hello`
   - **Method**: `GET`
   - **Loop**: Enable for continuous testing
   - **Period**: `2.0` seconds
4. Click **Start** to begin sending requests

### 4. Monitor the Interaction

- Check the **Log** tabs for both server and client to see real-time communication
- Observe color-coded log entries indicating request/response flow
- Modify templates while running to see immediate effects

---

## User Guide

### Server Management

#### Creating and Configuring Servers

**Basic Server Setup:**
1. Click the **"+"** tab in the Server section
2. Configure the following parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Name** | Unique identifier for the server | `ProductAPI` |
| **Host** | Address and port binding | `localhost:8080` |
| **Route** | Endpoint path pattern | `/api/v1/products` |
| **Methods** | Supported HTTP methods | `GET`, `POST`, `PUT`, `DELETE` |
| **Autostart** | Start server automatically on app launch | ✓ |
| **Initial Delay** | Delay before server startup (seconds) | `0.5` |
| **Response Delay** | Artificial delay before sending responses | `0.1` |

**Advanced Response Templates:**

REST Tester uses Jinja2 templating for dynamic responses. Available variables include all Python standard modules and special context:

**Template Context Variables:**
- `time` - Python time module
- `random` - Python random module  
- `json` - Python json module
- `math` - Python math module
- `os` - Python os module
- `sys` - Python sys module
- `datetime` - Python datetime module
- `counter` - Auto-incrementing counter for sequential operations
- `request` - Complete Flask request object (servers only)

**Example: Dynamic Product API Response**
```json
{
  "status": "success",
  "timestamp": {{time.time()}},
  "method": "{{request.method}}",
  "data": {
    "products": [
      {
        "id": 1,
        "name": "Sample Product",
        "created_at": "{{datetime.datetime.now().isoformat()}}"
      }
    ]
  },
  "wave_value": {{ 5 * math.sin(math.pi/20.0 * counter)}},
  "request_info": {{request | tojson}},
  "counter": {{counter}}
}
```

#### Server Operations

- **Start/Stop**: Use the control buttons to manage server lifecycle
- **Real-time Updates**: Modify response templates while the server is running
- **Status Monitoring**: Green indicator shows active servers
- **Log Monitoring**: View incoming requests and outgoing responses

### Client Management

#### Creating and Configuring Clients

**Basic Client Setup:**
1. Click the **"+"** tab in the Client section
2. Configure the following parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Name** | Unique identifier for the client | `LoadTester` |
| **Host** | Target server address | `localhost:8080` |
| **Route** | Endpoint to request | `/api/v1/products` |
| **Method** | HTTP method to use | `POST` |
| **Autostart** | Start client automatically on app launch | ✓ |
| **Loop** | Send requests continuously | ✓ |
| **Initial Delay** | Delay before first request (seconds) | `1.0` |
| **Period** | Interval between requests (seconds) | `2.0` |

**Request Templates:**

Clients support Jinja2 templates for dynamic request generation with access to Python modules:

**Template Context Variables:**
- `time` - Python time module
- `random` - Python random module  
- `json` - Python json module
- `math` - Python math module
- `os` - Python os module
- `sys` - Python sys module
- `datetime` - Python datetime module
- `counter` - Auto-incrementing counter for sequential operations

**Example: Dynamic Request Body**
```json
{
  "timestamp": {{time.time()}},
  "sequence": {{counter}},
  "value": {{ 3.5 * math.fmod(counter, 17)}},
  "random_id": {{random.randint(1000, 9999)}},
  "data": {
    "action": "test_request",
    "created_at": "{{datetime.datetime.now().isoformat()}}",
    "math_result": {{math.sqrt(counter)}}
  }
}
```

#### Client Operations

- **Start/Stop**: Control client request generation
- **Loop Mode**: Enable for continuous testing scenarios
- **One-shot Mode**: Send single requests for debugging
- **Parameter Updates**: Modify settings while client is running
- **Response Monitoring**: View all responses in real-time

### Configuration System

#### Default Values

Set up default configurations to speed up instance creation:

**Server Defaults:**
```yaml
defaults:
  server:
    host: "localhost:5000"
    autostart: false
    initial_delay_sec: 0.5
    response_delay_sec: 0.0
    route: "/api/endpoint"
    methodes: ["GET", "POST"]
    response: |
      {
        "status": "ok",
        "timestamp": "{{ timestamp }}"
      }
```

**Client Defaults:**
```yaml
defaults:
  client:
    host: "localhost:5000"
    autostart: false
    loop: false
    initial_delay_sec: 1.0
    period_sec: 2.0
    route: "/api/endpoint"
    methode: "GET"
    request: |
      {
        "client": "{{ client_name }}",
        "time": "{{ timestamp }}"
      }
```

#### Configuration File Location

Configuration is automatically saved to:
- **Windows**: `%APPDATA%/rest-tester/config.yaml`
- **macOS**: `~/Library/Application Support/rest-tester/config.yaml`
- **Linux**: `~/.config/rest-tester/config.yaml`

### Monitoring and Logging

#### Log Viewer Features

- **Color-coded Levels**: 
  - 🔴 **ERROR**: Critical issues requiring attention
  - 🟠 **WARNING**: Important notices
  - ⚪ **INFO**: General information
  - 🔘 **DEBUG**: Detailed debugging information

- **Formatting Options**:
  - Adjustable font sizes (6pt - 18pt)
  - Monospace font for consistent alignment
  - JSON pretty-printing for structured data
  - Multi-line message support

- **Management Options**:
  - Clear logs for fresh start
  - Auto-scroll to latest entries
  - Search and filter capabilities
  - Export logs to file

---

## Use Cases

### 1. API Development and Testing

**Scenario**: Developing a REST API and need to test client interactions

**Setup**:
1. Create a server instance mimicking your API
2. Configure realistic response templates
3. Create multiple client instances with different request patterns
4. Monitor request/response cycles to identify issues

**Benefits**:
- Test API behavior before implementation
- Validate client error handling
- Performance testing with configurable delays
- Mock different API states and responses

### 2. Load Testing and Performance Analysis

**Scenario**: Evaluating API performance under various load conditions

**Setup**:
1. Deploy your API server
2. Create multiple client instances with loop mode enabled
3. Configure different request intervals and patterns
4. Monitor response times and error rates

**Example Configuration**:
```yaml
# Light load client
client_light:
  period_sec: 5.0
  loop: true

# Heavy load client  
client_heavy:
  period_sec: 0.1
  loop: true
```

### 3. Integration Testing

**Scenario**: Testing interactions between multiple microservices

**Setup**:
1. Create server instances for each microservice mock
2. Configure cross-service request templates
3. Set up client instances to simulate service-to-service communication
4. Monitor the complete request flow

### 4. API Mocking for Frontend Development

**Scenario**: Frontend development when backend APIs are not ready

**Setup**:
1. Create server instances matching API specifications
2. Configure realistic response data and timing
3. Implement various response scenarios (success, error, timeout)
4. Provide stable endpoints for frontend development

### 5. Debugging and Troubleshooting

**Scenario**: Investigating API communication issues

**Setup**:
1. Recreate problematic scenarios with server/client pairs
2. Add detailed logging and response delays
3. Monitor exact request/response payloads
4. Isolate and reproduce specific issues

### 6. Training and Education

**Scenario**: Teaching REST API concepts and debugging techniques

**Setup**:
1. Create examples demonstrating REST principles
2. Show real-time request/response interaction
3. Demonstrate error handling and retry logic
4. Provide hands-on experience with API testing tools

---

## Development

### Development Setup

#### Prerequisites for Development

```bash
# Required tools
git
python >= 3.9
poetry (recommended) or pip

# Optional but recommended
vscode or pycharm
git-flow
```

#### Setting Up Development Environment

1. **Clone and Setup**:
```bash
git clone https://github.com/david-kracht/rest-tester.git
cd rest-tester

# Install development dependencies
poetry install --with dev

# Activate virtual environment
poetry shell
```

2. **Run in Development Mode**:
```bash
# With Poetry
poetry run python -m rest_tester.main

# Or directly
python -m rest_tester.main
```

### Project Structure

```
rest-tester/
├── src/rest_tester/                   # Main application package
│   ├── core/                          # Core application logic
│   │   ├── application_manager.py
│   │   ├── service_facade.py
│   │   ├── config_locator.py
│   │   └── validation_service.py
│   ├── service/                       # Business logic layer
│   │   ├── rest_server_manager.py
│   │   ├── rest_client_manager.py
│   │   ├── endpoint_utils.py
│   │   └── logging_config.py
│   ├── gui_model/                     # GUI components and models
│   │   ├── instances_gui.py
│   │   ├── model.py
│   │   ├── log_widget.py
│   │   ├── client_instance_gui.py
│   │   ├── server_instance_gui.py
│   │   ├── defaults_widget.py
│   │   └── validate.py
│   ├── resources/                     # Static resources
│   │   └── config.yaml
│   └── main.py                        # Application entry point
├── scripts/                           # Build and deployment scripts
│   └── build-local.sh
├── pyproject.toml                     # Project configuration
├── poetry.lock                        # Dependencies lock file
├── DEPLOYMENT.md                      # Deployment instructions
├── README.md                          # This file
└── LICENSE                            # MIT License
```

#### Key Components

| Component | Responsibility | Key Files |
|-----------|---------------|-----------|
| **Core** | Application lifecycle, configuration management | `application_manager.py`, `service_facade.py` |
| **Service** | REST operations, threading, logging | `rest_server_manager.py`, `rest_client_manager.py` |
| **GUI** | User interface, models, widgets | `instances_gui.py`, `model.py`, `log_widget.py` |

### Contributing

#### Development Workflow

1. **Fork and Branch**:
```bash
git fork https://github.com/david-kracht/rest-tester.git
git checkout -b feature/amazing-feature
```

2. **Development Guidelines**:
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Update documentation as needed

3. **Code Quality** (Future Enhancement):
```bash
# Will be available in future releases:
# poetry run flake8 src/     # Linting
# poetry run mypy src/       # Type checking
# poetry run black src/      # Formatting
# poetry run isort src/      # Import sorting
```

4. **Commit and Pull Request**:
```bash
git add .
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

#### Coding Standards

- **Type Hints**: All public functions must include type hints
- **Docstrings**: Use Google-style docstrings for all modules, classes, and functions
- **Error Handling**: Implement comprehensive error handling with appropriate logging
- **Documentation**: Update relevant documentation for all changes

#### Architecture Guidelines

- **Separation of Concerns**: Keep GUI, business logic, and data layers separate
- **Dependency Injection**: Use dependency injection for testability
- **Signal/Slot Pattern**: Use Qt signals for loose coupling between components
- **Factory Pattern**: Use factories for consistent object creation
- **Configuration Driven**: Make behavior configurable rather than hard-coded

---

## Deployment

### Automated Deployment Pipeline

The project uses GitHub Actions for automated deployment to PyPI:

#### Release Process

1. **Development Builds**: 
   - Triggered on every push to any branch
   - Creates unique development versions: `{version}.dev{timestamp}+{commit_hash}`
   - Deployed to Test PyPI: https://test.pypi.org/project/rest-tester/

2. **Production Releases**:
   - Triggered when creating a GitHub release/tag
   - Uses semantic versioning (e.g., `v1.0.0` → `1.0.0`)
   - Deployed to Production PyPI: https://pypi.org/project/rest-tester/

#### Creating a Release

**Via GitHub UI**:
1. Go to Releases → Create a new release
2. Tag: `v1.0.0` (semantic versioning)
3. Title: `Version 1.0.0`
4. Description: Add release notes

**Via Command Line**:
```bash
git tag v1.0.0
git push origin v1.0.0
# Then create release from tag on GitHub
```

#### Manual Deployment

For manual deployment or testing:

```bash
# Build package
poetry build

# Upload to Test PyPI
poetry publish -r testpypi

# Upload to Production PyPI
poetry publish
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ **Commercial Use**: You can use this software commercially
- ✅ **Modification**: You can modify the source code
- ✅ **Distribution**: You can distribute the software
- ✅ **Private Use**: You can use the software privately
- ❌ **Liability**: Authors are not liable for damages
- ❌ **Warranty**: No warranty is provided

---

## Support

### Getting Help

- **Documentation**: This README and inline code documentation
- **Issues**: [GitHub Issues](https://github.com/david-kracht/rest-tester/issues)
- **Discussions**: [GitHub Discussions](https://github.com/david-kracht/rest-tester/discussions)

### Reporting Issues

When reporting issues, please include:

1. **Environment Information**:
   - Operating System and version
   - Python version
   - REST Tester version (`rest-tester --version`)

2. **Steps to Reproduce**:
   - Detailed steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots if applicable

3. **Configuration**:
   - Relevant configuration settings
   - Log output (with sensitive data removed)

### Feature Requests

We welcome feature requests! Please use GitHub Issues with the "enhancement" label and include:

- Clear description of the proposed feature
- Use case and benefits
- Possible implementation approach
- Willingness to contribute to implementation

---

## Future Work / Improvements

The following features and improvements are planned for future releases:

### Testing Infrastructure
- **Unit Test Suite**: Comprehensive test coverage with pytest
- **Integration Tests**: End-to-end testing of client-server interactions
- **GUI Testing**: Automated UI testing framework
- **Performance Tests**: Load testing and benchmarking tools

### Documentation
- **API Documentation**: Detailed API reference documentation
- **User Manual**: Step-by-step tutorials and guides
- **Developer Documentation**: Architecture and contribution guides
- **Video Tutorials**: Interactive learning materials

### Code Quality Tools
- **Linting**: Integration with flake8, mypy for code quality
- **Formatting**: Automated code formatting with black and isort
- **Pre-commit Hooks**: Automated quality checks before commits
- **Coverage Reports**: Test coverage tracking and reporting

### Enhanced Features
- **Plugin System**: Extensible architecture for custom functionality
- **Configuration Validation**: Schema-based YAML validation
- **Import/Export**: Configuration sharing and backup capabilities
- **Performance Monitoring**: Request timing and performance metrics
- **Visual Status Indicators**: Real-time status monitoring with color-coded indicators

---

**REST Tester** - *Making REST API development and testing effortless*

Copyright (c) 2025 David Kracht - Licensed under MIT License