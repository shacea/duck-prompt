import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import pytest
from pydantic import ValidationError

# Module to test
from core.pydantic_models.config_settings import ConfigSettings

def test_config_settings_defaults():
    """Test default values of ConfigSettings."""
    settings = ConfigSettings()
    assert settings.allowed_extensions == set()
    assert settings.excluded_dirs == set()
    assert settings.default_ignore_list == [
        "__pycache__/",
        ".git/",
        ".gitignore",
        ".windsurfrules",
        ".cursorrules"
    ]

def test_config_settings_initialization():
    """Test initializing ConfigSettings with specific values."""
    data = {
        "allowed_extensions": {".py", ".md"},
        "excluded_dirs": {"node_modules/", "*.log"},
        "default_ignore_list": ["__pycache__/"] # Overriding default
    }
    settings = ConfigSettings(**data)
    assert settings.allowed_extensions == data["allowed_extensions"]
    assert settings.excluded_dirs == data["excluded_dirs"]
    assert settings.default_ignore_list == data["default_ignore_list"]

def test_config_settings_type_validation():
    """Test type validation for ConfigSettings fields."""
    # allowed_extensions must be a set of strings
    with pytest.raises(ValidationError):
        ConfigSettings(allowed_extensions=[".py", 123]) # List contains non-string
    with pytest.raises(ValidationError):
        ConfigSettings(allowed_extensions="not_a_set") # Not a set
    ConfigSettings(allowed_extensions={".py", ".txt"}) # Should work

    # excluded_dirs must be a set of strings
    with pytest.raises(ValidationError):
        ConfigSettings(excluded_dirs=[".git", 123])
    with pytest.raises(ValidationError):
        ConfigSettings(excluded_dirs="not_a_set")
    ConfigSettings(excluded_dirs={".git/", "*.tmp"}) # Should work

    # default_ignore_list must be a list of strings
    with pytest.raises(ValidationError):
        ConfigSettings(default_ignore_list=[".git", 123])
    with pytest.raises(ValidationError):
        ConfigSettings(default_ignore_list="not_a_list")
    ConfigSettings(default_ignore_list=[".git/", "*.pyc"]) # Should work

def test_config_settings_assignment_validation():
    """Test validation on attribute assignment."""
    settings = ConfigSettings()
    # Valid assignment
    settings.allowed_extensions = {".java", ".kt"}
    assert settings.allowed_extensions == {".java", ".kt"}

    # Invalid assignment
    with pytest.raises(ValidationError):
        settings.excluded_dirs = "not_a_set"

def test_config_settings_json_serialization_deserialization():
    """Test JSON serialization and deserialization."""
    data = {
        "allowed_extensions": {".py", ".md"},
        "excluded_dirs": {"node_modules/", "*.log"},
        "default_ignore_list": ["__pycache__/"]
    }
    settings = ConfigSettings(**data)

    # Serialize to JSON (Note: sets might serialize as lists in JSON)
    settings_json = settings.model_dump_json()

    # Deserialize from JSON
    settings_loaded = ConfigSettings.model_validate_json(settings_json)

    # Check if loaded settings match original (Pydantic handles set conversion)
    assert settings_loaded == settings
    assert settings_loaded.allowed_extensions == data["allowed_extensions"]
    assert settings_loaded.excluded_dirs == data["excluded_dirs"]
    assert settings_loaded.default_ignore_list == data["default_ignore_list"]

def test_config_settings_empty_initialization():
    """Test initializing with an empty dictionary uses defaults."""
    settings = ConfigSettings(**{})
    assert settings.allowed_extensions == set()
    assert settings.excluded_dirs == set()
    assert settings.default_ignore_list == [
        "__pycache__/",
        ".git/",
        ".gitignore",
        ".windsurfrules",
        ".cursorrules"
    ]
