# Integrated Development Guide (XML Authoring + Python Coding Guidelines)

This document comprehensively outlines the guidelines that an LLM must follow to generate high-quality Python code and reflect this code within an XML structure. All guidelines must be strictly adhered to ensure consistent and efficient development.

---

## 1. Common Guidelines

- **Language and Output**: All responses and documentation must be written in **Korean**. Modified code must be output in its entirety without omissions. Files that are not modified should be explicitly stated as "No modifications" ("수정 없음").
- **Style**: Aim for a clear and concise technical style, prioritizing code readability above all else.
- **Programming Paradigm**: Prefer functional programming. Use classes only when absolutely necessary.
- **Modularity and Separation of Concerns**: Separate duplicate code into functions or modules. Adhere to the principle of separation of concerns to enhance maintainability.
- **Utility Structure**:
  - Utilities specific to a sub-project should be stored in the `src/<sub_project_name>/utils/` folder, separated into files based on functionality (e.g., `src/my_feature/utils/parser.py`, `src/my_feature/utils/formatter.py`). Do not create a single `utils.py` file in the root of individual sub-projects.
  - Utilities common to the entire project should be stored in the `src/utils/` folder, separated into files based on functionality (e.g., `src/utils/data_helper.py`, `src/utils/network.py`).
- **Variable Naming**:
  - Constants: Uppercase with underscores (e.g., `IS_LOADING`, `MAX_RETRIES`)
  - Variables, Functions: Snake case (e.g., `process_data()`, `user_input`)
- **Execution Method**: Use `main.py` in the project root as the execution entry point. This file should import and run the core logic from within `src`. Avoid direct execution of `__main__` blocks within `src/<sub-project_name>/main.py`. Discourage direct use of parsers or terminal inputs.
- **Configuration Management**:
  - API keys, secrets, environment-specific settings, etc., should be stored in the configuration file for each sub-project: `src/<sub_project_name>/config.yml`.
  - Loading configuration files should be done using the project-common utility `src/utils/config.py`. Do not use `.env` files.
- **Error Handling**:
  - Handle exceptions using `try-except` blocks and output informative error messages.
  - Use `termcolor` to inform the user about the progress of each step.
- **File Handling**: Always specify `encoding="utf-8"` when using `with open()`.
- **Key Variable Management**: Declare key variables (including constants) at the top of the script.
- **Model Specification**: If AI model names like `gpt-4o`, `gpt-4o-mini` are specified in the script, do not change them.
- **Python Version**: Use **Python 3.12 or higher**.
- **Dependency Management**:
  - **Python Virtual Environment**: Use `uv` to manage Python virtual environments.
  - **Dependency Specification**: Project dependencies must be specified and managed in the `pyproject.toml` file. Do not use `requirements.txt`.
- **Requirements Management (PRD)**:
  - **Storage Location**: Create and update documents as Markdown (`.md`) files per feature within the `docs/PRD(Product Requirement Document)/` folder.
  - **Update Method**: PRD documents are not updated every time. Modify the specific feature's file only when requirements for that feature change or are added.
- **Code Formatting**: Format code using `black` and `isort`.
- **Syntax**: Write simple conditional statements on a single line. Actively utilize list/dictionary comprehensions.
- **Web Development (FastAPI)**: Adhere to standard FastAPI patterns and REST API design principles. Establish appropriate caching strategies.
- **Logging**:
  - Actively use the `logging` module for tracing execution flow and diagnosing issues.
  - Log configuration and management are centralized through the project-common utility **`src/utils/log_manager.py`**.
  - Log files should be saved in the `logs/` folder. Filenames should include date and time information (e.g., `project_name_YYYYMMDD_HHMMSS.log`) to distinguish logs over time (configured in `log_manager.py`).
- **Type Hints**: Actively use type hints utilizing the `typing` module.
- **Data Structures**: **Use the `Pydantic` library to define data structures and perform validation.**
- **File Size**: **If the content of an individual file exceeds 15,000 tokens (LLM standard), split it by functionality. Keep related functionalities within the same folder.**
- **XML Reserved Characters**: When using XML reserved characters (`<`, `>`, `&`, `'`, `"`) as text data, they must be escaped (`&lt;`, `&gt;`, `&amp;`, `&apos;`, `&quot;`). Utilizing `CDATA` sections is convenient.
- **Unmodified Files**: Do not include files with no modifications in the XML response.
- **Response Structure and Summary**: **The response must have the XML section followed by the Summary section.** The Summary section must be concise, **under 1000 tokens**.

---

## 2. Detailed Python Coding Guidelines

## 2.1. Code Structure

- **File Structure Template (e.g., `src/sub_project_name/main.py`)**:

  ```python
  # Standard library imports
  import logging

  # Third-party imports
  from fastapi import FastAPI # Example: If using FastAPI
  from pydantic import BaseModel
  from termcolor import colored

  # Local application imports
  from .models import MyData # Example: Importing models from the same package
  from .utils.parser import parse_data # Example: Importing sub-project utility
  from src.utils.config import load_config # Importing project common config loader
  from src.utils.log_manager import get_logger # Importing project common logger

  # Logger setup (obtained via log_manager.py)
  logger = get_logger(__name__)

  # Load configuration (Recommended at root main.py or application initialization)
  # config = load_config('sub_project_name') # Pass sub-project name

  # Pydantic models
  class Item(BaseModel):
      name: str
      price: float

  # FastAPI app instance (for web applications)
  app = FastAPI()

  # main functions/classes
  @app.post("/items/", response_model=Item)
  async def create_item(item: Item):
      """Creates an item."""
      logger.info(f"Received item: {item.name}")
      # ... logic ...
      # config = load_config('sub_project_name') # Load if needed within the function
      # parsed = parse_data(...) # Use sub-project utility
      logger.info(colored(f"Item '{item.name}' created successfully.", "green"))
      return item

  def core_logic_function():
      """Core application logic function (if not web-based)."""
      logger.info("Starting core logic...")
      config = load_config('sub_project_name') # Load if needed within the function
      # ... perform logic ...
      logger.info("Core logic finished.")

  # helper functions (used only within this module)
  def _internal_helper():
      pass

  # __main__ block is unnecessary here as execution starts from root main.py
  # if __name__ == "__main__":
  #     pass
  ```

## 2.2. Naming Conventions

- **Functions**: `snake_case` (e.g., `process_data()`, `calculate_average()`)
- **Classes**: `PascalCase` (e.g., `DataProcessor`, `UserManager`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`, `API_KEY_NAME`)
- **Directories**: `lower_snake_case` (e.g., `data_processing`, `api_clients`, `utils`)

## 2.3. Type Hints and Pydantic

- Actively use the `typing` module to specify type hints for function arguments, return values, and variables.
- **Use `Pydantic` to define data models and perform data validation.** Use it where data structures need to be clear, such as API responses, configuration structures, and data processing pipelines. (Keep existing example code)

  ```python
  from typing import List, Optional
  from pydantic import BaseModel, Field, validator, EmailStr

  class UserProfile(BaseModel):
      username: str = Field(..., min_length=3, description="Unique username")
      email: EmailStr
      full_name: Optional[str] = None
      age: Optional[int] = Field(None, gt=0, le=120)

  class Order(BaseModel):
      order_id: int
      user: UserProfile
      items: List[str]

      @validator("items")
      def items_must_not_be_empty(cls, value):
          if not value:
              raise ValueError("Order must contain at least one item")
          return value
  ```

## 2.4. Syntax and Formatting

- Unify code style using `black` and `isort`. Settings can be included in `pyproject.toml`.
- Simple conditional statements can be written on a single line if it doesn't harm readability.
- Use list/dictionary comprehensions to write concise and efficient code.

## 2.5. Web Development (FastAPI)

- Adhere to FastAPI's standard patterns (path operation functions, Pydantic model integration, etc.). (Define `app` object in `src/sub_project_name/main.py`)
- Follow REST API design principles (resource-based URLs, appropriate HTTP methods, etc.).
- If necessary, utilize libraries like `FastAPI-Cache2` to implement suitable caching strategies.
- **Use Pydantic models to define request bodies and response models to leverage automatic data validation and documentation.**

## 2.6. Logging Details

- Centrally manage logging configuration via **`src/utils/log_manager.py`**. This module is responsible for creating logger instances and setting up necessary handlers (console, file, etc.).
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) to differentiate the importance of logs.
- **Log File Storage**: Configure `FileHandler` within `log_manager.py` to save logs to the `logs/` directory. Include date and time in filenames to make log file management easier.
- Record important execution steps, error occurrences, communication with external systems, etc. In each module, obtain a logger instance like so: `from src.utils.log_manager import get_logger; logger = get_logger(__name__)`.

## 2.7. Environment Configuration (config.yml)

- Store configuration information in YAML format within the **`src/<sub_project_name>/config.yml`** file inside each sub-project.
- Load configuration files using the function defined in the project-common utility **`src/utils/config.py`** (e.g., `load_config(sub_project_name: str)`). This function takes the sub-project name as an argument, parses the corresponding `config.yml` file, and returns it as a Python dictionary.
- Configuration files can include API keys, database connection info, external service URLs, application behavior parameters, etc. Consider managing sensitive information using placeholders or environment variable references instead of actual values.

  ```yaml
  # src/sub_project_name/config.yml Example
  api_settings:
    service_a:
      api_key: "your_api_key_here" # Actual key or environment variable reference
      base_url: "https://api.service_a.com/v1"
      timeout: 10
  database:
    type: "postgresql"
    host: "localhost"
    port: 5432
    username: "user"
    password: "password" # Actual password or environment variable reference
    db_name: "my_app_db"
  app_parameters:
    max_retries: 3
    feature_flags:
      new_dashboard: true
  ```

---

## 3. Virtual Environment and Dependency Management

- **Virtual Environment**: Use `uv` to create and manage isolated Python environments per project.
  - Creation: `uv venv`
  - Activation: `. .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
- **Dependency Management**: Use the `pyproject.toml` file to manage project metadata and dependencies.

  - Add dependency: `uv pip install <package_name>`
  - Install dependencies: `uv pip install -r requirements.lock` or `uv sync` (based on lock file)
  - `pyproject.toml` example:

    ```toml
    [project]
    name = "my_project"
    version = "0.1.0"
    description = "My project description."
    requires-python = ">=3.12" # Specify Python version
    dependencies = [
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "pydantic>=2.0",
        "PyYAML>=6.0",
        "termcolor>=2.0",
        "requests>=2.28.0",
        # Add other necessary libraries
    ]

    [tool.black]
    line-length = 88

    [tool.isort]
    profile = "black"

    [tool.uv.sources]
    # Optional: Specify custom package sources if needed
    ```

---

## 4. Project Structure

Below is the recommended project structure.

```tree
project-name/
├── src/                             # Source code root (Python package)
│   ├── sub_project_name/            # Main application or library module
│   │   ├── models/                  # Pydantic models or database models
│   │   │   ├── __init__.py
│   │   │   └── data_models.py
│   │   ├── tools/                   # Tool modules performing specific functions
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── specific_tool.py
│   │   ├── utils/                   # ★ Sub-project specific utility folder ★
│   │   │   ├── __init__.py
│   │   │   ├── parser.py            # Example: Parsing related utils
│   │   │   └── formatter.py         # Example: Formatting related utils
│   │   ├── __init__.py
│   │   ├── config.yml               # ★ Sub-project configuration file ★
│   │   └── main.py                  # Core application logic (e.g., FastAPI app definition)
│   └── utils/                       # ★ Project common utility folder ★
│       ├── __init__.py
│       ├── config.py                # ★ Common configuration loader ★
│       ├── log_manager.py           # ★ Common logging manager ★
│       └── common_helper.py         # Example: Other common utils
├── tests/                           # Test code root
│   ├── __init__.py
│   └── stage_{number}_{stage_description}/
│       ├── __init__.py
│       └── test_{feature_name}.py
├── docs/                            # Documentation root
│   ├── PRD(Product Requirement Document)/
│   │   ├── 00_overview.md
│   │   └── feature_a_spec.md
│   └── developer_guide.md
├── logs/                            # Log file storage directory (recommend auto-creation)
├── docker/                          # Docker related files directory
│   ├── Dockerfile
│   └── docker-compose.yml
├── data/                            # Input/Output data storage directory (recommend excluding from version control)
├── main.py                          # ★ Project root execution entry point ★
├── pyproject.toml                   # Project configuration and dependency management
├── README.md                        # Project introduction and usage guide
└── .gitignore                       # List of files excluded from Git tracking
```

**Key Directory and File Descriptions:**

- **`src/`**: The root package directory where all Python source code resides. This directory itself is recognized as a Python package.
- **`src/sub_project_name/`**: A package where the code for a specific feature or microservice unit resides. The core business logic of the project is organized under this directory. `sub_project_name` should be named according to the actual feature (e.g., `user_service`, `data_processor`).
- **`src/sub_project_name/models/`**: Directory containing Python files that define Pydantic models, database schemas (e.g., SQLAlchemy models), or other data structures. Defines the shape and validation rules for data.
- **`src/sub_project_name/tools/`**: Directory containing reusable tool modules that perform specific functions. Examples include external API clients, complex data transformation logic, specific file format handlers, etc.
- **`src/sub_project_name/utils/`**: Directory storing utility functions commonly used _only within_ the corresponding `sub_project_name` sub-project, separated into files by functionality (e.g., `parser.py`, `formatter.py`). Differentiated from project-global utilities.
- **`src/sub_project_name/config.yml`**: YAML configuration file storing settings specific to the sub-project (API keys, database paths, feature flags, etc.).
- **`src/sub_project_name/main.py`**: The main file containing the core logic of the sub-project. For FastAPI applications, the `FastAPI` app instance (`app`) and main path operations (API endpoints) might be defined here. This file is not executed directly but imported and used by the project root `main.py`.
- **`src/utils/`**: Directory containing utility modules that can be commonly used by multiple sub-projects across the entire project.
- **`src/utils/config.py`**: Common module providing a function (`load_config`) to safely load and parse `config.yml` files from each sub-project.
- **`src/utils/log_manager.py`**: Common module that initializes the project-wide logging settings (`setup_logging`) and provides standardized logger instances (`get_logger`). Manages log file creation, format settings, etc., centrally.
- **`tests/`**: Root directory for all types of test code, including unit tests, integration tests, and end-to-end tests. It's common to mirror the source code structure.
- **`tests/stage_{number}_{stage_description}/`**: Subdirectories organizing tests based on development stages. For example, `stage_01_data_ingestion`, `stage_02_api_endpoints` can be used to manage tests systematically.
- **`docs/`**: Directory for storing project-related documentation (this development guide, architecture diagrams, API docs, etc.).
- **`docs/PRD/`**: Directory for storing Product Requirement Documents as Markdown files, organized by feature or topic. Only the relevant file is updated when requirements change.
- **`logs/`**: Directory where log files generated during application execution are stored. Typically added to `.gitignore` to exclude from version control and implemented to be automatically created by `log_manager.py`.
- **`docker/`**: Directory for storing Docker-related files (`Dockerfile`, `docker-compose.yml`, related scripts, etc.). Used for containerizing the application.
- **`data/`**: Directory for storing input data required for program execution or output data generated as results. Often large, frequently changing, or containing sensitive information, so it's generally recommended to add it to `.gitignore`.
- **`main.py` (root)**: The **top-level execution entry point** for the project. Primarily responsible for setting up logging (e.g., calling `src.utils.log_manager.setup_logging()`), loading configuration if needed (e.g., `src.utils.config.load_config()`), and importing and running a specific sub-project application from the `src` directory (e.g., `src.sub_project_name.main.app`, often by starting a `uvicorn` server).
- **`pyproject.toml`**: The standard file for managing project metadata (name, version, description, etc.), Python version requirements, main dependency list, development dependencies, build system settings, and configurations for tools like `black` and `isort`. `uv` uses this file to configure the environment and manage packages.
- **`README.md`**: Located in the project's root directory, this Markdown document describes the project's overview, purpose, key features, installation instructions, execution methods, configuration details, contribution guidelines, etc. It's the crucial first file someone new to the project will read.
- **`.gitignore`**: Defines a list of file and directory patterns that the Git version control system should ignore. Examples include Python virtual environment directories (`.venv/`), bytecode files (`__pycache__/`, `*.pyc`), log files (`logs/`, `*.log`), data files (`data/`), IDE configuration files, and other files not directly related to the project code.

---

## 5. PRD (Product Requirement Document) Management

- PRD documents should be written and managed as Markdown files per feature or topic within the `docs/PRD/` directory.
- **There is no need to manage the entire PRD content in a single file or update it every time.** Only modify the requirements document for the specific feature where changes have occurred.
- Filename convention (example): Using a combination of numbers and descriptions like `01_user_authentication.md`, `02_data_processing_pipeline.md` is recommended.

---

## 6. XML Response Format

**Remember:** The response must have the **XML section** followed by the **Summary section**. The Summary must be concise, **under 1000 tokens**.

1.**Response Structure**: **XML Section + Summary Section** (Summary must come last)

- **XML Section**: Use the `<code_changes>` root tag. Describe changed file information within `<file>` elements inside `<changed_files>`.
- **Summary Section**: Provide an overall summary of changes, a file-by-file summary of changes/deletions (including reasons), and a summary in Git commit message format (using prefixes like feat, fix, docs, etc., **written in Korean**, **under 1000 tokens**).

  2.**XML Format Details**:

- Within the `<file>` element: Include `<file_summary>`, `<file_operation>` (CREATE, UPDATE, DELETE), `<file_path>`, and `<file_code>` (use CDATA section; omit for DELETE).
- **Do not include unmodified files in the XML.**
- **File paths must exactly follow the paths specified in the 'Project Structure' section above.** (e.g., `main.py`, `src/sub_project_name/main.py`, `src/sub_project_name/config.yml`, `src/utils/log_manager.py`, `docs/PRD/feature_x.md`, `docker/Dockerfile`)

  3.**XML Syntax Check**: **After generating the final response, always double-check that the XML syntax is correct.** (e.g., tag closure, CDATA section format, reserved character escaping, etc.)

**Example XML Snippet according to the changed guidelines:**
(Root `main.py` example updated: Reflects usage of `log_manager`, `config`)

```xml
<code_changes>
    <changed_files>
        <file>
            <file_summary>Project root execution script: Uses common logging and config loader, runs FastAPI app</file_summary>
            <file_operation>UPDATE</file_operation> {/* or CREATE */}
            <file_path>main.py</file_path>
            <file_code><![CDATA[
import uvicorn
import os
import logging
from termcolor import colored

# Import project common utilities
from src.utils.log_manager import setup_logging, get_logger
from src.utils.config import load_config

# Import sub-project app (change according to the app to run)
from src.sub_project_name.main import app

if __name__ == "__main__":
    # Setup logging (using log_manager)
    setup_logging()
    logger = get_logger(__name__)
    logger.info(colored("Starting application from root main.py...", "yellow"))

    # Load configuration (Example: loading sub_project_name config)
    sub_project_name = "sub_project_name" # Specify target sub-project
    try:
        app_config = load_config(sub_project_name)
        logger.info(f"Configuration for '{sub_project_name}' loaded.")
        # Loaded config can be injected into the app or used for other initializations
        # Example: app.state.config = app_config
    except FileNotFoundError:
        logger.warning(f"Configuration file for '{sub_project_name}' not found. Proceeding with defaults or environment variables if applicable.")
    except Exception as e:
        logger.critical(f"Failed to load configuration for '{sub_project_name}': {e}", exc_info=True)
        exit(1) # Exit if config loading fails

    # Run FastAPI (using Uvicorn)
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    reload = os.getenv("APP_RELOAD", "true").lower() == "true"

    logger.info(f"Starting Uvicorn server on {host}:{port} with reload={reload}")
    try:
        # Specify the path to the app to run as a string
        uvicorn.run(f"src.{sub_project_name}.main:app", host=host, port=port, reload=reload)
    except Exception as e:
        logger.critical(f"Failed to start Uvicorn: {e}", exc_info=True)

]]></file_code>
        </file>
        <file>
            <file_summary>Added common logging manager module</file_summary>
            <file_operation>CREATE</file_operation>
            <file_path>src/utils/log_manager.py</file_path>
            <file_code><![CDATA[
import logging
import logging.handlers
import os
import datetime

LOG_DIR = "logs"
LOG_LEVEL = logging.INFO # Default log level

def setup_logging():
    """Initializes project-wide logging configuration."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filename = os.path.join(LOG_DIR, f"app_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # Default formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove existing handlers (prevent duplication)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler configuration (specify UTF-8 encoding)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler configuration
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Adjust uvicorn log level (optional)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    root_logger.info("Logging setup complete.")

def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance with the specified name."""
    return logging.getLogger(name)

# Additional logging helper functions can be defined here if needed
]]></file_code>
        </file>
        <file>
            <file_summary>Added common configuration loader utility</file_summary>
            <file_operation>CREATE</file_operation>
            <file_path>src/utils/config.py</file_path>
            <file_code><![CDATA[
import yaml
import os
from typing import Dict, Any

CONFIG_DIR_TEMPLATE = "src/{sub_project_name}/config.yml"

def load_config(sub_project_name: str) -> Dict[str, Any]:
    """
    Loads the config.yml file for the specified sub-project.

    Args:
        sub_project_name: The name of the sub-project to load config for (e.g., 'my_feature').

    Returns:
        A dictionary containing the configuration content.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If an error occurs during YAML parsing.
        Exception: For other file reading errors.
    """
    config_path = CONFIG_DIR_TEMPLATE.format(sub_project_name=sub_project_name)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        if config is None: # Handle empty file
            return {}
        return config
    except yaml.YAMLError as e:
        # Log more specific info on YAML format error if needed
        raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}")
    except Exception as e:
        raise Exception(f"Error reading configuration file {config_path}: {e}")

# Logic for environment variable overrides or default value handling can be added here if needed
]]></file_code>
        </file>
         <file>
             <file_summary>Created sub-project configuration file</file_summary>
             <file_operation>CREATE</file_operation>
             <file_path>src/sub_project_name/config.yml</file_path>
             <file_code><![CDATA[
# src/sub_project_name/config.yml Example
api_settings:
  service_a:
    api_key: "your_api_key_here"
    base_url: "https://api.service_a.com/v1"
    timeout: 10
database:
  type: "sqlite"
  path: "data/sub_project.db"
app_parameters:
  max_items: 100
]]></file_code>
         </file>
        {/* Other file changes */}
    </changed_files>
</code_changes>

{/* --- Summary Section Start (Positioned after XML section) --- */}
<summary>
**Overall Change Summary:**
Updated the project structure and management practices according to the revised guidelines. Key changes include reorganizing the utility folder structure, introducing common logging and configuration management modules, and changing the location of sub-project-specific configuration files. The root `main.py` has been updated to use common modules for handling logging and configuration and to run the Uvicorn server.

**File-specific Change/Deletion Summary:**
- `main.py` (UPDATE): Modified to use common logging (`log_manager`) and config loader (`config`), updated FastAPI app execution logic.
- `src/utils/log_manager.py` (CREATE): Added a common module to manage project-wide logging. Includes file/console handlers and default format settings.
- `src/utils/config.py` (CREATE): Added a common utility function to load `config.yml` files for each sub-project.
- `src/sub_project_name/config.yml` (CREATE): Created an example configuration file for the sub-project.

**Git Commit Message:**
feat: 프로젝트 구조 및 공통 유틸리티 개편 (로깅, 설정)

(Token count: approx. 200)
</summary>
```
