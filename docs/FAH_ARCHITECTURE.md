# FAH (Feature-Atomic Hybrid) Architecture Implementation

## Overview

This document describes the Feature-Atomic Hybrid (FAH) architecture implementation for the Duck Prompt application. The FAH architecture combines feature-based organization with atomic design principles to create a scalable, maintainable codebase.

## Architecture Components

### 1. Gateway Layer (`src/gateway/`)

The gateway serves as the central hub for the FAH architecture:

- **Command Buses**: Feature-specific command routing
- **Event Bus**: Cross-feature communication via events
- **Service Locator**: Dependency injection and service registry

### 2. Feature Slices (`src/features/`)

Each feature is organized as an independent slice:

```
src/features/<feature_name>/
├── atoms/        # Basic, reusable components
├── molecules/    # Composite components
├── organisms/    # Complex business logic
├── commands.py   # Feature commands (Pydantic models)
├── handlers.py   # Command handlers
└── __init__.py
```

### 3. Shared Components (`src/shared/`)

Common utilities and helpers used across features:

- **atoms/**: Basic utilities (logger, file_utils, validators)

## Implemented Features

### Database Feature (`src/features/database/`)

- **Purpose**: Manages all database operations
- **Commands**: Connect, Disconnect, ExecuteQuery, API key management, Config management
- **Events**: DatabaseConnectedEvent, DatabaseDisconnectedEvent

### Config Feature (`src/features/config/`)

- **Purpose**: Application configuration management
- **Commands**: LoadConfiguration, UpdateConfiguration, API key selection
- **Events**: ConfigurationLoadedEvent, ConfigurationUpdatedEvent

## Usage Example

```python
import asyncio
from src import gateway as gw
from src.features.database.commands import ConnectDatabase
from src.features.config.commands import LoadConfiguration

async def main():
    # Connect to database
    await gw.database_command_bus.handle(ConnectDatabase())
    
    # Load configuration
    config = await gw.config_command_bus.handle(LoadConfiguration())
    print(f"Configuration loaded: {config}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Command Bus Pattern

Each feature has its own command bus:

```python
# Define command
class MyCommand(Command):
    param1: str
    param2: int

# Register handler
@MyFeatureCommandBus.register(MyCommand)
async def handle_my_command(cmd: MyCommand):
    # Handle command
    return result

# Use command
result = await gw.my_feature_command_bus.handle(MyCommand(param1="test", param2=42))
```

## Event Bus Pattern

Cross-feature communication via events:

```python
# Define event
class MyEvent(Event):
    data: str

# Subscribe to event
@EventBus.on(MyEvent)
def handle_my_event(event: MyEvent):
    print(f"Event received: {event.data}")

# Emit event
EventBus.emit(MyEvent(data="test"))
```

## Service Locator Pattern

Register and retrieve services:

```python
# Register service
ServiceLocator.provide("my_service", MyService())

# Get service
service = ServiceLocator.get("my_service")
```

## Migration Guide

To migrate existing services to FAH:

1. Create a new feature slice under `src/features/`
2. Define commands in `commands.py`
3. Move business logic to atoms/molecules/organisms
4. Create handlers in `handlers.py`
5. Register with appropriate command bus
6. Update imports in dependent code

## Benefits

1. **Modularity**: Each feature is self-contained
2. **Scalability**: Easy to add new features without affecting others
3. **Testability**: Clear boundaries make testing easier
4. **Maintainability**: Organized structure reduces complexity
5. **Performance**: Sub-bus pattern prevents handler dictionary bloat

## Next Steps

1. Complete migration of remaining features:
   - File Management
   - Prompt Builder
   - Attachments
   - Templates
   - State Management
   - Token Calculation
   - Gemini Integration
   - XML Processing

2. Implement UI layer integration with FAH
3. Add comprehensive tests for each feature
4. Update main application to use FAH architecture

## Testing

Run the FAH test script:

```bash
python test_fah.py
```

This will verify that the basic FAH architecture is working correctly.
