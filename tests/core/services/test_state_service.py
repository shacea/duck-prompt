import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import pytest
import os
import json
import shutil
from zipfile import ZipFile, is_zipfile

# Module to test
from core.services.state_service import StateService
from core.pydantic_models.app_state import AppState

# Fixture for temporary status directory
@pytest.fixture
def temp_status_dir(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    return str(status_dir) # Return path as string

# Fixture for StateService instance with temp directory
@pytest.fixture
def state_service(temp_status_dir):
    service = StateService(status_dir=temp_status_dir)
    return service

# Fixture for a sample AppState object
@pytest.fixture
def sample_state():
    return AppState(
        mode="Test Mode",
        project_folder="/test/project",
        system_prompt="Test System",
        user_prompt="Test User",
        checked_files=["/test/project/file1.py", "/test/project/file2.txt"]
    )

def test_state_service_init_creates_dir(tmp_path):
    """Test that StateService creates the status directory if it doesn't exist."""
    new_status_dir = tmp_path / "new_status"
    assert not new_status_dir.exists()
    StateService(status_dir=str(new_status_dir))
    assert new_status_dir.exists()
    assert new_status_dir.is_dir()

def test_state_service_get_state_file_path(state_service, temp_status_dir):
    """Test the helper method for constructing file paths."""
    assert state_service._get_state_file_path("my_state") == os.path.join(temp_status_dir, "my_state.json")
    assert state_service._get_state_file_path("my_state.json") == os.path.join(temp_status_dir, "my_state.json")
    assert state_service._get_state_file_path("My_State.JSON") == os.path.join(temp_status_dir, "My_State.JSON.json") # Ensure lowercase check

def test_state_service_save_state(state_service, sample_state, temp_status_dir):
    """Test saving a valid AppState."""
    filename = "test_save"
    file_path = state_service._get_state_file_path(filename)

    assert not os.path.exists(file_path)
    success = state_service.save_state(sample_state, filename)
    assert success is True
    assert os.path.exists(file_path)

    # Verify content
    with open(file_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    # Compare loaded dict with model's dict representation
    assert saved_data == sample_state.model_dump()

def test_state_service_load_state_not_found(state_service):
    """Test loading a non-existent state returns default AppState."""
    loaded_state = state_service.load_state("non_existent_state")
    assert loaded_state is not None
    assert isinstance(loaded_state, AppState)
    assert loaded_state == AppState() # Should be default state

def test_state_service_load_state_success(state_service, sample_state, temp_status_dir):
    """Test loading a previously saved state."""
    filename = "test_load"
    state_service.save_state(sample_state, filename) # Save first

    loaded_state = state_service.load_state(filename)
    assert loaded_state is not None
    assert isinstance(loaded_state, AppState)
    assert loaded_state == sample_state # Compare loaded model with original

def test_state_service_load_state_invalid_json(state_service, temp_status_dir):
    """Test loading a file with invalid JSON returns default AppState."""
    filename = "invalid_json"
    file_path = state_service._get_state_file_path(filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{invalid json")

    loaded_state = state_service.load_state(filename)
    assert loaded_state is not None
    assert loaded_state == AppState()

def test_state_service_load_state_validation_error(state_service, temp_status_dir):
    """Test loading JSON that fails Pydantic validation returns default AppState."""
    filename = "validation_error"
    file_path = state_service._get_state_file_path(filename)
    invalid_data = {
        "mode": 123, # Invalid type
        "project_folder": "/test"
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(invalid_data, f)

    loaded_state = state_service.load_state(filename)
    assert loaded_state is not None
    assert loaded_state == AppState()

def test_state_service_list_states(state_service, temp_status_dir):
    """Test listing saved state files."""
    assert state_service.list_states() == [] # Initially empty
    state_service.save_state(AppState(mode="s1"), "state1")
    state_service.save_state(AppState(mode="s2"), "state2.json")
    # Create a non-json file
    with open(os.path.join(temp_status_dir, "not_a_state.txt"), 'w') as f:
        f.write("hello")

    states = state_service.list_states()
    assert len(states) == 2
    assert "state1.json" in states
    assert "state2.json" in states
    assert "not_a_state.txt" not in states

def test_state_service_delete_state(state_service, sample_state):
    """Test deleting a state file."""
    filename = "to_delete"
    file_path = state_service._get_state_file_path(filename)
    state_service.save_state(sample_state, filename)
    assert os.path.exists(file_path)

    success = state_service.delete_state(filename)
    assert success is True
    assert not os.path.exists(file_path)

    # Test deleting non-existent file
    success_non_existent = state_service.delete_state("non_existent")
    assert success_non_existent is False

def test_state_service_import_export(state_service, sample_state, tmp_path):
    """Test exporting and importing state to/from an external file."""
    export_path = tmp_path / "exported_state.json"
    import_path = export_path # Use the same file for import

    # Export
    assert not export_path.exists()
    export_success = state_service.export_state_to_file(sample_state, str(export_path))
    assert export_success is True
    assert export_path.exists()

    # Verify exported content
    with open(export_path, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    assert exported_data == sample_state.model_dump()

    # Import
    imported_state = state_service.import_state_from_file(str(import_path))
    assert imported_state is not None
    assert imported_state == sample_state

    # Test import non-existent file
    assert state_service.import_state_from_file(str(tmp_path / "no_such_file.json")) is None

def test_state_service_backup_restore(state_service, temp_status_dir, tmp_path):
    """Test backing up and restoring states."""
    backup_path = tmp_path / "state_backup.zip"

    # Create some state files
    state1 = AppState(mode="state1")
    state2 = AppState(mode="state2", checked_files=["f1"])
    state_service.save_state(state1, "state1")
    state_service.save_state(state2, "state2")
    state1_path = state_service._get_state_file_path("state1")
    state2_path = state_service._get_state_file_path("state2")

    assert os.path.exists(state1_path)
    assert os.path.exists(state2_path)

    # Backup
    backup_success = state_service.backup_all_states(str(backup_path))
    assert backup_success is True
    assert backup_path.exists()
    assert is_zipfile(backup_path)

    # Modify/delete original files before restore
    os.remove(state1_path)
    state_service.save_state(AppState(mode="modified"), "state2") # Modify state2

    # Restore
    restore_success = state_service.restore_states_from_backup(str(backup_path))
    assert restore_success is True

    # Verify restored files
    assert os.path.exists(state1_path) # state1 should be restored
    assert os.path.exists(state2_path) # state2 should be restored

    # Verify content of restored files
    restored_state1 = state_service.load_state("state1")
    restored_state2 = state_service.load_state("state2")
    assert restored_state1 == state1 # Check content matches original state1
    assert restored_state2 == state2 # Check content matches original state2

    # Test restore non-existent backup
    assert state_service.restore_states_from_backup(str(tmp_path / "no_backup.zip")) is False
