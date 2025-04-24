# Integrated Development Guide (JSON Response + Python Coding Guidelines)

This document comprehensively outlines the guidelines that an LLM must follow to generate high-quality Python code and reflect this code within a **JSON structure**. All guidelines must be strictly adhered to ensure consistent and efficient development.

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
- **JSON String Escaping**: Ensure special characters within strings in the JSON output (like newlines `\n`, quotes `"`, backslashes `\\`) are properly escaped according to JSON standards.
- **Unmodified Files**: Do not include files with no modifications in the **JSON response**.
- **Response Structure and Summary**: **The response must be a single JSON object containing a `code_changes` key and a `summary` key.** The `summary` object must be concise, **under 1000 tokens**.

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

**Key Directory and File Descriptions:** (Descriptions remain the same as the original guide)

- **`src/`**: The root package directory...
- **`src/sub_project_name/`**: A package where the code...
- **`src/sub_project_name/models/`**: Directory containing Python files...
- **`src/sub_project_name/tools/`**: Directory containing reusable tool modules...
- **`src/sub_project_name/utils/`**: Directory storing utility functions...
- **`src/sub_project_name/config.yml`**: YAML configuration file...
- **`src/sub_project_name/main.py`**: The main file containing...
- **`src/utils/`**: Directory containing utility modules...
- **`src/utils/config.py`**: Common module providing...
- **`src/utils/log_manager.py`**: Common module that initializes...
- **`tests/`**: Root directory for all types...
- **`tests/stage_{number}_{stage_description}/`**: Subdirectories organizing tests...
- **`docs/`**: Directory for storing project-related...
- **`docs/PRD/`**: Directory for storing Product Requirement Documents...
- **`logs/`**: Directory where log files...
- **`docker/`**: Directory for storing Docker-related...
- **`data/`**: Directory for storing input data...
- **`main.py` (root)**: The **top-level execution entry point**...
- **`pyproject.toml`**: The standard file for managing...
- **`README.md`**: Located in the project's root directory...
- **`.gitignore`**: Defines a list of file...

---

## 5. PRD (Product Requirement Document) Management

- PRD documents should be written and managed as Markdown files per feature or topic within the `docs/PRD/` directory.
- **There is no need to manage the entire PRD content in a single file or update it every time.** Only modify the requirements document for the specific feature where changes have occurred.
- Filename convention (example): Using a combination of numbers and descriptions like `01_user_authentication.md`, `02_data_processing_pipeline.md` is recommended.

---

## 6. JSON Response Format

**Remember:** The response must be a **single valid JSON object**. This object contains two main keys: `code_changes` and `summary`. The `summary` object must be concise, **under 1000 tokens**.

1.**Response Structure**: A single JSON object with keys `code_changes` and `summary`.

```json
{
  "code_changes": { ... },
  "summary": { ... }
}
```

2.**`code_changes` Object Details**:

- Contains a single key `changed_files`, which is an array of objects.
- Each object in the `changed_files` array represents a modified file and has the following keys:
  - `file_summary` (string): A brief description of the changes in the file.
  - `file_operation` (string): The operation performed ("CREATE", "UPDATE", "DELETE").
  - `file_path` (string): The exact path to the file, following the project structure.
  - `file_code` (string, optional): The complete code of the file as a string. Omit this key if `file_operation` is "DELETE". Ensure proper JSON string escaping for the code content (e.g., newlines as `\n`, quotes as `\"`).
- **Do not include unmodified files in the `changed_files` array.**
- **File paths must exactly follow the paths specified in the 'Project Structure' section.** (e.g., `main.py`, `src/sub_project_name/main.py`, `src/sub_project_name/config.yml`, `src/utils/log_manager.py`, `docs/PRD/feature_x.md`, `docker/Dockerfile`)

  3.**`summary` Object Details**:

- Contains the following keys:
  - `overall_summary` (string): An overall summary of the changes made.
  - `file_specific_summary` (array): An array of objects, each describing a specific file change/deletion. Each object should have:
    - `file` (string): The path of the changed/deleted file.
    - `operation` (string): "CREATE", "UPDATE", or "DELETE".
    - `reason` (string): A brief reason for the change/deletion.
  - `git_commit_message` (string): A summary in Git commit message format (using prefixes like feat, fix, docs, etc., **written in Korean**).
- The entire content of the `summary` object should be **under 1000 tokens**.

  4.**JSON Syntax Check**: **After generating the final response, always double-check that the JSON syntax is correct.** Ensure proper use of braces `{}`, brackets `[]`, commas `,`, colons `:`, quotes `""`, and correct escaping of special characters within strings.

**Example JSON Snippet according to the changed guidelines:**
(Root `main.py` example updated: Reflects usage of `log_manager`, `config`)

```json
{
  "code_changes": {
    "changed_files": [
      {
        "file_summary": "Project root execution script: Uses common logging and config loader, runs FastAPI app",
        "file_operation": "UPDATE",
        "file_path": "main.py",
        "file_code": "import uvicorn\nimport os\nimport logging\nfrom termcolor import colored\n\n# Import project common utilities\nfrom src.utils.log_manager import setup_logging, get_logger\nfrom src.utils.config import load_config\n\n# Import sub-project app (change according to the app to run)\nfrom src.sub_project_name.main import app\n\nif __name__ == \"__main__\":\n    # Setup logging (using log_manager)\n    setup_logging()\n    logger = get_logger(__name__)\n    logger.info(colored(\"Starting application from root main.py...\", \"yellow\"))\n\n    # Load configuration (Example: loading sub_project_name config)\n    sub_project_name = \"sub_project_name\" # Specify target sub-project\n    try:\n        app_config = load_config(sub_project_name)\n        logger.info(f\"Configuration for '{sub_project_name}' loaded.\")\n        # Loaded config can be injected into the app or used for other initializations\n        # Example: app.state.config = app_config\n    except FileNotFoundError:\n        logger.warning(f\"Configuration file for '{sub_project_name}' not found. Proceeding with defaults or environment variables if applicable.\")\n    except Exception as e:\n        logger.critical(f\"Failed to load configuration for '{sub_project_name}': {e}\", exc_info=True)\n        exit(1) # Exit if config loading fails\n\n    # Run FastAPI (using Uvicorn)\n    host = os.getenv(\"APP_HOST\", \"127.0.0.1\")\n    port = int(os.getenv(\"APP_PORT\", \"8000\"))\n    reload = os.getenv(\"APP_RELOAD\", \"true\").lower() == \"true\"\n\n    logger.info(f\"Starting Uvicorn server on {host}:{port} with reload={reload}\")\n    try:\n        # Specify the path to the app to run as a string\n        uvicorn.run(f\"src.{sub_project_name}.main:app\", host=host, port=port, reload=reload)\n    except Exception as e:\n        logger.critical(f\"Failed to start Uvicorn: {e}\", exc_info=True)\n\n"
      },
      {
        "file_summary": "Added common logging manager module",
        "file_operation": "CREATE",
        "file_path": "src/utils/log_manager.py",
        "file_code": "import logging\nimport logging.handlers\nimport os\nimport datetime\n\nLOG_DIR = \"logs\"\nLOG_LEVEL = logging.INFO # Default log level\n\ndef setup_logging():\n    \"\"\"Initializes project-wide logging configuration.\"\"\"\n    os.makedirs(LOG_DIR, exist_ok=True)\n    log_filename = os.path.join(LOG_DIR, f\"app_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log\")\n\n    # Default formatter\n    formatter = logging.Formatter(\n        \"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"\n    )\n\n    # Root logger configuration\n    root_logger = logging.getLogger()\n    root_logger.setLevel(LOG_LEVEL)\n\n    # Remove existing handlers (prevent duplication)\n    for handler in root_logger.handlers[:]:\n        root_logger.removeHandler(handler)\n\n    # File handler configuration (specify UTF-8 encoding)\n    file_handler = logging.FileHandler(log_filename, encoding='utf-8')\n    file_handler.setFormatter(formatter)\n    root_logger.addHandler(file_handler)\n\n    # Console handler configuration\n    stream_handler = logging.StreamHandler()\n    stream_handler.setFormatter(formatter)\n    root_logger.addHandler(stream_handler)\n\n    logging.getLogger(\"uvicorn.access\").setLevel(logging.WARNING) # Adjust uvicorn log level (optional)\n    logging.getLogger(\"uvicorn.error\").setLevel(logging.WARNING)\n\n    root_logger.info(\"Logging setup complete.\")\n\ndef get_logger(name: str) -> logging.Logger:\n    \"\"\"Returns a logger instance with the specified name.\"\"\"\n    return logging.getLogger(name)\n\n# Additional logging helper functions can be defined here if needed\n"
      },
      {
        "file_summary": "Added common configuration loader utility",
        "file_operation": "CREATE",
        "file_path": "src/utils/config.py",
        "file_code": "import yaml\nimport os\nfrom typing import Dict, Any\n\nCONFIG_DIR_TEMPLATE = \"src/{sub_project_name}/config.yml\"\n\ndef load_config(sub_project_name: str) -> Dict[str, Any]:\n    \"\"\"\n    Loads the config.yml file for the specified sub-project.\n\n    Args:\n        sub_project_name: The name of the sub-project to load config for (e.g., 'my_feature').\n\n    Returns:\n        A dictionary containing the configuration content.\n\n    Raises:\n        FileNotFoundError: If the configuration file does not exist.\n        yaml.YAMLError: If an error occurs during YAML parsing.\n        Exception: For other file reading errors.\n    \"\"\"\n    config_path = CONFIG_DIR_TEMPLATE.format(sub_project_name=sub_project_name)\n\n    if not os.path.exists(config_path):\n        raise FileNotFoundError(f\"Configuration file not found at: {config_path}\")\n\n    try:\n        with open(config_path, 'r', encoding='utf-8') as f:\n            config = yaml.safe_load(f)\n        if config is None: # Handle empty file\n            return {}\n        return config\n    except yaml.YAMLError as e:\n        # Log more specific info on YAML format error if needed\n        raise yaml.YAMLError(f\"Error parsing YAML file {config_path}: {e}\")\n    except Exception as e:\n        raise Exception(f\"Error reading configuration file {config_path}: {e}\")\n\n# Logic for environment variable overrides or default value handling can be added here if needed\n"
      },
      {
        "file_summary": "Created sub-project configuration file",
        "file_operation": "CREATE",
        "file_path": "src/sub_project_name/config.yml",
        "file_code": "# src/sub_project_name/config.yml Example\napi_settings:\n  service_a:\n    api_key: \"your_api_key_here\"\n    base_url: \"https://api.service_a.com/v1\"\n    timeout: 10\ndatabase:\n  type: \"sqlite\"\n  path: \"data/sub_project.db\"\napp_parameters:\n  max_items: 100\n"
      }
    ]
  },
  "summary": {
    "overall_summary": "Updated the project structure and management practices according to the revised guidelines. Key changes include reorganizing the utility folder structure, introducing common logging and configuration management modules, and changing the location of sub-project-specific configuration files. The root `main.py` has been updated to use common modules for handling logging and configuration and to run the Uvicorn server.",
    "file_specific_summary": [
      {
        "file": "main.py",
        "operation": "UPDATE",
        "reason": "Modified to use common logging (`log_manager`) and config loader (`config`), updated FastAPI app execution logic."
      },
      {
        "file": "src/utils/log_manager.py",
        "operation": "CREATE",
        "reason": "Added a common module to manage project-wide logging. Includes file/console handlers and default format settings."
      },
      {
        "file": "src/utils/config.py",
        "operation": "CREATE",
        "reason": "Added a common utility function to load `config.yml` files for each sub-project."
      },
      {
        "file": "src/sub_project_name/config.yml",
        "operation": "CREATE",
        "reason": "Created an example configuration file for the sub-project."
      }
    ],
    "git_commit_message": "feat: 프로젝트 구조 및 공통 유틸리티 개편 (로깅, 설정)"
  }
}
```

```

```
