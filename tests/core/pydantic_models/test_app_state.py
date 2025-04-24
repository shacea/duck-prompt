import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import pytest
from pydantic import ValidationError

# Module to test
from core.pydantic_models.app_state import AppState

def test_app_state_defaults():
    """Test default values of AppState."""
    state = AppState()
    assert state.mode == "Code Enhancer Prompt Builder"
    assert state.project_folder is None
    assert state.system_prompt == ""
    assert state.user_prompt == ""
    assert state.checked_files == []

def test_app_state_initialization():
    """Test initializing AppState with specific values."""
    data = {
        "mode": "Meta Prompt Builder",
        "project_folder": "/path/to/project",
        "system_prompt": "System instructions",
        "user_prompt": "User query",
        "checked_files": ["/path/to/project/file1.py", "/path/to/project/file2.txt"]
    }
    state = AppState(**data)
    assert state.mode == data["mode"]
    assert state.project_folder == data["project_folder"]
    assert state.system_prompt == data["system_prompt"]
    assert state.user_prompt == data["user_prompt"]
    assert state.checked_files == data["checked_files"]

def test_app_state_type_validation():
    """Test type validation for AppState fields."""
    # mode must be a string
    with pytest.raises(ValidationError):
        AppState(mode=123)

    # project_folder must be a string or None
    with pytest.raises(ValidationError):
        AppState(project_folder=123)
    AppState(project_folder=None) # Should work
    AppState(project_folder="/valid/path") # Should work

    # checked_files must be a list of strings
    with pytest.raises(ValidationError):
        AppState(checked_files=["file1", 123]) # List contains non-string
    with pytest.raises(ValidationError):
        AppState(checked_files="not_a_list") # Not a list
    AppState(checked_files=["file1", "file2"]) # Should work

def test_app_state_assignment_validation():
    """Test validation on attribute assignment."""
    state = AppState()
    # Valid assignment
    state.project_folder = "/new/path"
    assert state.project_folder == "/new/path"

    # Invalid assignment
    with pytest.raises(ValidationError):
        state.checked_files = "not_a_list"

def test_app_state_json_serialization_deserialization():
    """Test JSON serialization and deserialization."""
    data = {
        "mode": "Meta Prompt Builder",
        "project_folder": "/path/to/project",
        "system_prompt": "System instructions",
        "user_prompt": "User query",
        "checked_files": ["/path/to/project/file1.py", "/path/to/project/file2.txt"]
    }
    state = AppState(**data)

    # Serialize to JSON
    state_json = state.model_dump_json()

    # Deserialize from JSON
    state_loaded = AppState.model_validate_json(state_json)

    # Check if loaded state matches original
    assert state_loaded == state
    assert state_loaded.mode == data["mode"]
    assert state_loaded.checked_files == data["checked_files"]

def test_app_state_missing_fields():
    """Test that missing non-optional fields raise ValidationError."""
    # mode is not optional, but has a default
    state = AppState()
    assert state.mode is not None

    # If a field without a default were added and made non-optional,
    # initializing without it would raise ValidationError.
    # Example (if 'new_required_field: str' was added):
    # with pytest.raises(ValidationError):
    #     AppState()
