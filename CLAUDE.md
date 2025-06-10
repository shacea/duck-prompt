# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application

```bash
# With uv (recommended)
uv run python main.py

# Direct Python
python main.py
```

### Building the Application

```bash
# Windows build (automatically detects AMD64/ARM64)
build.bat

# The executable will be created in dist/DuckPrompt/DuckPrompt.exe
```

### Testing and Code Quality

```bash
# Run tests (when available)
uv run pytest tests/

# Type checking
uv run mypy src/ tests/

# Linting
uv run ruff check .

# Code formatting
uv run black .
uv run ruff format .
```

### Installing Dependencies

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt
```

## High-Level Architecture

### Application Overview

DuckPrompt is a PyQt6-based GUI application that serves as an integrated prompt builder for Large Language Models (LLMs). It combines file content, attachments, and prompts to create comprehensive inputs for AI models, with direct Gemini API integration.

### Key Architectural Components

1. **Database-Driven Configuration**
   - PostgreSQL database (`duck_agent`) stores all configuration and API keys
   - Connection details hardcoded in `src/core/services/db_service.py`
   - Application will not start without database connection
   - Settings are read-only in GUI; database modifications required for changes

2. **Service Layer Architecture**
   - All core business logic is in `src/core/services/`:
     - `DbService`: Database operations and connection management
     - `ConfigService`: Configuration management from database
     - `GeminiService`: LangGraph-based Gemini API integration
     - `TokenService`: Multi-model token calculation (GPT, Claude, Gemini)
     - `FilesystemService`: File operations with watchdog monitoring
     - `DirectoryCacheService`: Efficient directory tree caching
     - `XmlService`: XML parsing for code changes
     - `PromptService`, `TemplateService`, `StateService`: Content management

3. **UI/Controller Pattern**
   - Controllers in `src/ui/controllers/` handle business logic
   - UI components in `src/ui/` handle presentation
   - Clean separation between UI and business logic
   - Main window setup split into modular components

4. **Two Operating Modes**
   - **Code Enhancement Mode**: Combines files, attachments, system/user prompts
   - **Meta Prompt Mode**: Wraps existing prompts with templates

5. **Asynchronous Processing**
   - Gemini API calls run in separate QThread workers
   - LangGraph workflow for structured API interactions
   - Non-blocking UI during API operations

### Critical Implementation Details

1. **File System Monitoring**
   - Uses `watchdog` library for real-time file system changes
   - Cached file system model for performance
   - Respects `.gitignore` and database filtering rules

2. **Token Calculation**
   - GPT: Local calculation using `tiktoken`
   - Claude: API-based calculation (requires active API key in DB)
   - Gemini: API-based with multimodal support (text + attachments)

3. **State Management**
   - Auto-saves to `resources/status/default.json`
   - Preserves project folder, prompts, attachments, and checked files
   - "Load Last Work" button for quick state restoration

4. **XML Processing**
   - Parses LLM-generated `<code_changes>` XML
   - Executes file operations without confirmation
   - Automatically strips markdown code blocks

### Database Schema Requirements

- Tables: `application_config`, `api_keys`, `gemini_logs`, `model_configs`
- API keys must have `is_active=TRUE` for functionality
- Default system prompt path stored in `application_config`

### Important File Locations

- Configuration: Database-driven, no local config files
- Templates: `resources/prompts/system/` and `resources/prompts/user/`
- States: `resources/status/`
- Icons/Resources: `resources/icons/`, `resources/fonts/`

## 디렉터리 트리 구조

File Tree:
 📁 duck-prompt/
   📁 ./
   📁 docs/
     📁 PRD(Product Requirement Document)/
       📄 PRD_db.md (267 bytes)
       📄 전체 PRD.md (8,262 bytes)
       📄 파일별 기능 상세.md (12,942 bytes)
     📁 PyQt6/
       📄 designer.md (19,049 bytes)
       📄 gotchas.md (14,084 bytes)
       📄 index.md (11,758 bytes)
       📄 introduction.md (7,488 bytes)
       📄 metaobjects.md (5,854 bytes)
       📄 multiinheritance.md (7,714 bytes)
       📄 pickle.md (4,137 bytes)
       📄 pyqt5_differences.md (5,701 bytes)
       📄 pyqt_qsettings.md (5,315 bytes)
       📄 pyqt_qvariant.md (4,135 bytes)
       📄 python_shell.md (3,690 bytes)
       📄 qml.md (22,132 bytes)
       📄 qt_interfaces.md (3,096 bytes)
       📄 qt_properties.md (7,917 bytes)
       📄 signals_slots.md (23,888 bytes)
     📁 ReferenceDocs/
       📄 Google Gen AI SDK.md (123,856 bytes)
       📄 gemini flash thinking model sample.py.txt (11,904 bytes)
       📄 py-silero-vad-lite docs.md (1,625 bytes)
       📄 개발전 PRD 작성가이드.md (8,778 bytes)
     📁 리팩토링/
       📄 Diff-match-patch(DMP) 코드 수정 방법.md (12,792 bytes)
       📄 Feature‑Atomic Hybrid(FAH) + Sub-Bus Structure.md (19,456 bytes)
       📄 unified-diff_en.md (7,265 bytes)
       📄 unified-diff_kr.md (9,307 bytes)
       📄 네트워크 드라이브 개선_캐싱 및 watchdog 사용.md (5,600 bytes)
       📄 프로그램 재개발.md (14,992 bytes)
     📄 Database Schema Definitions.md (11,229 bytes)
     📄 Diff-match-patch(DMP) 코드 수정 방법.md (12,792 bytes)
     📄 Feature‑Atomic Hybrid(FAH) + Sub-Bus Structure.md (19,456 bytes)
     📄 Gemini JSON schema docs.md (10,943 bytes)
     📄 ssh_docs.md (9,999 bytes)
   📁 resources/
     📁 fonts/
       📄 malgun.ttf (13,459,196 bytes)
     📁 icons/
       📄 rubber_duck.ico (108,585 bytes)
     📁 prompts/
       📁 system/
         📁 kr/
           📄 bug_fixer_kr.md (2,610 bytes)
           📄 unified-diff_kr.md (9,307 bytes)
           📄 xml_prompt_guide_python_kr.md (32,114 bytes)
         📄 META_Prompt.md (14,530 bytes)
         📄 bux_fixer.md (21,252 bytes)
         📄 code_generator.md (3,667 bytes)
         📄 python_prompt_guide.md (4,574 bytes)
         📄 unified-diff_en.md (7,265 bytes)
         📄 xml_prompt_guide.md (3,019 bytes)
         📄 xml_prompt_guide_python_en.md (30,011 bytes)
         📄 xml_prompt_guide_python_kr.md (32,114 bytes)
       📁 user/
         📄 mp_code_review.md (2,047 bytes)
         📄 mp_code_review_input.md (678 bytes)
         📄 mp_hn_perspective_input.md (559 bytes)
         📄 mp_script_to_blog_input.md (936 bytes)
         📄 mp_template.md (88 bytes)
     📁 status/
   📁 src/
     📁 core/
       📁 pydantic_models/
         📄 **init**.py (76 bytes)
         📄 app_state.py (1,267 bytes)
         📄 config_settings.py (3,409 bytes)
       📁 services/
         📄 **init**.py (990 bytes)
         📄 config_service.py (11,753 bytes)
         📄 db_service.py (32,083 bytes)
         📄 directory_cache_service.py (28,426 bytes)
         📄 filesystem_service.py (6,069 bytes)
         📄 gemini_service.py (30,577 bytes)
         📄 prompt_service.py (3,134 bytes)
         📄 state_service.py (7,779 bytes)
         📄 template_service.py (3,394 bytes)
         📄 token_service.py (12,573 bytes)
         📄 xml_service.py (12,145 bytes)
       📁 utils/
       📁 workers/
       📄 **init**.py (65 bytes)
       📄 langgraph_state.py (860 bytes)
     📁 ui/
       📁 controllers/
         📄 **init**.py (72 bytes)
         📄 file_tree_controller.py (15,891 bytes)
         📄 main_controller.py (23,703 bytes)
         📄 prompt_controller.py (7,072 bytes)
         📄 resource_controller.py (13,735 bytes)
         📄 system_prompt_controller.py (7,322 bytes)
         📄 xml_controller.py (2,671 bytes)
       📁 models/
         📄 **init**.py (67 bytes)
         📄 file_system_models.py (20,825 bytes)
       📁 widgets/
         📄 **init**.py (68 bytes)
         📄 check_box_delegate.py (3,714 bytes)
         📄 custom_tab_bar.py (4,364 bytes)
         📄 custom_text_edit.py (501 bytes)
         📄 file_tree_view.py (2,439 bytes)
         📄 tab_manager.py (434 bytes)
       📄 **init**.py (63 bytes)
       📄 main_window.py (51,497 bytes)
       📄 main_window_setup_signals.py (8,111 bytes)
       📄 main_window_setup_ui.py (19,302 bytes)
       📄 settings_dialog.py (54,953 bytes)
     📁 utils/
       📄 **init**.py (320 bytes)
       📄 db_migration_script.py (5,742 bytes)
       📄 helpers.py (2,152 bytes)
       📄 notifications.py (2,983 bytes)
       📄 postgres_db_initializer.py (20,529 bytes)
     📄 **init**.py (64 bytes)
     📄 app.py (5,276 bytes)
     📄 config.yml (1,155 bytes)
   📄 README.md (20,536 bytes)
   📄 app_amd64.spec (2,695 bytes)
   📄 app_arm64.spec (2,839 bytes)
   📄 build.bat (553 bytes)
   📄 main.py (422 bytes)
   📄 pyproject.toml (2,029 bytes)
   📄 qt.conf (47 bytes)
