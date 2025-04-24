import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import pytest
import os
import yaml
from unittest.mock import patch, mock_open

# Module to test
from core.services.config_service import ConfigService, DEFAULT_CONFIG_PATH
from core.pydantic_models.config_settings import ConfigSettings

# Fixture for temporary config file path
@pytest.fixture
def temp_config_path(tmp_path):
    return tmp_path / "test_config.yml"

# Fixture for ConfigService instance with temp path
@pytest.fixture
def config_service(temp_config_path):
    # Ensure the temp directory exists
    os.makedirs(os.path.dirname(temp_config_path), exist_ok=True)
    # Create an instance pointing to the temp path
    service = ConfigService(config_path=str(temp_config_path))
    # Clean up the file after test if it was created
    yield service
    if os.path.exists(temp_config_path):
        os.remove(temp_config_path)

def test_config_service_load_default_when_file_not_exist(config_service, temp_config_path):
    """Test that default settings are loaded and saved if config file doesn't exist."""
    assert not os.path.exists(temp_config_path)
    settings = config_service.get_settings()
    # Check if settings are default
    assert settings == ConfigSettings()
    # Check if the default config file was created
    assert os.path.exists(temp_config_path)
    # Verify content of the created file
    with open(temp_config_path, 'r', encoding='utf-8') as f:
        saved_data = yaml.safe_load(f)
    assert saved_data == ConfigSettings().model_dump(mode='python')


def test_config_service_load_from_existing_file(config_service, temp_config_path):
    """Test loading settings from an existing YAML file."""
    test_data = {
        "allowed_extensions": [".py", ".js"], # Use list for YAML compatibility
        "excluded_dirs": ["node_modules/", "dist/"],
        "default_ignore_list": ["__pycache__/"]
    }
    # Create the config file
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f)

    # Re-initialize service to load the file (or implement a reload method)
    service = ConfigService(config_path=str(temp_config_path))
    settings = service.get_settings()

    # Check if loaded settings match test data (Pydantic converts list to set)
    assert settings.allowed_extensions == {".py", ".js"}
    assert settings.excluded_dirs == {"node_modules/", "dist/"}
    assert settings.default_ignore_list == ["__pycache__/"]

def test_config_service_load_invalid_yaml(config_service, temp_config_path):
    """Test loading with invalid YAML returns default settings."""
    # Create invalid YAML file
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        f.write("allowed_extensions: [.py, .js\n") # Invalid syntax

    # Initialize service (should handle error and return defaults)
    service = ConfigService(config_path=str(temp_config_path))
    settings = service.get_settings()

    assert settings == ConfigSettings()

def test_config_service_load_validation_error(config_service, temp_config_path):
    """Test loading with data that fails Pydantic validation returns defaults."""
    test_data = {
        "allowed_extensions": ".py", # Invalid type (should be list/set)
        "excluded_dirs": ["node_modules/"]
    }
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f)

    # Initialize service (should handle validation error)
    service = ConfigService(config_path=str(temp_config_path))
    settings = service.get_settings()

    assert settings == ConfigSettings() # Should return defaults on validation error

def test_config_service_update_settings(config_service, temp_config_path):
    """Test updating settings and saving them."""
    # Initial load (creates default file)
    initial_settings = config_service.get_settings()
    assert initial_settings == ConfigSettings()
    assert os.path.exists(temp_config_path)

    # Update settings
    update_data = {"allowed_extensions": {".ts", ".tsx"}}
    config_service.update_settings(**update_data)

    # Get updated settings
    updated_settings = config_service.get_settings()
    assert updated_settings.allowed_extensions == {".ts", ".tsx"}
    # Other settings should remain default
    assert updated_settings.excluded_dirs == set()

    # Verify the file was updated
    with open(temp_config_path, 'r', encoding='utf-8') as f:
        saved_data = yaml.safe_load(f)

    # Pydantic converts set to list for YAML dump
    assert saved_data["allowed_extensions"] == [".ts", ".tsx"]
    assert saved_data["excluded_dirs"] == [] # Default empty set becomes empty list

def test_config_service_update_validation_error(config_service, temp_config_path):
    """Test that invalid updates do not change settings or save."""
    initial_settings = config_service.get_settings()

    # Attempt invalid update
    with patch('builtins.print') as mock_print: # Capture print output
        config_service.update_settings(allowed_extensions="not_a_set")

    # Settings should not have changed
    current_settings = config_service.get_settings()
    assert current_settings == initial_settings

    # Verify file content hasn't changed from the initial default save
    with open(temp_config_path, 'r', encoding='utf-8') as f:
        saved_data = yaml.safe_load(f)
    assert saved_data == ConfigSettings().model_dump(mode='python')

    # Check if validation error was printed
    mock_print.assert_any_call("Configuration update validation error: 1 validation error for ConfigSettings\nallowed_extensions\n  Input should be a valid set [type=set_type, input_value='not_a_set', input_type=str]")

# Test case for default config path (optional, might require mocking os.path.exists)
# def test_config_service_uses_default_path():
#     with patch('os.path.exists', return_value=False):
#         with patch('builtins.open', mock_open()) as mocked_file:
#             service = ConfigService() # Use default path
#             assert service.config_path == DEFAULT_CONFIG_PATH
#             # Check if it tried to save the default config
#             mocked_file.assert_called_once_with(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8')
