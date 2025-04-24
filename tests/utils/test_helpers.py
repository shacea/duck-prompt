import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Module to test
# Ensure src is in sys.path (usually handled by tests/__init__.py or pytest config)
from utils import helpers

# --- Fixtures ---
@pytest.fixture(autouse=True)
def ensure_utils_initialized():
    """Ensure helpers.init_utils() is called before tests needing encoding."""
    # Reset ENC before each test potentially using it
    helpers.ENC = None
    helpers.init_utils()
    # Wait for the preloading thread to likely finish (adjust time if needed)
    # This is not ideal, proper synchronization or mocking might be better.
    import time
    time.sleep(0.2) # Give thread time to load encoding

# --- Tests for get_project_root ---

@patch('sys.frozen', True, create=True)
@patch('sys._MEIPASS', '/mock/meipass/path', create=True)
def test_get_project_root_frozen():
    """Test get_project_root in PyInstaller bundle environment."""
    root = helpers.get_project_root()
    assert str(root) == '/mock/meipass/path'

@patch('sys.frozen', False, create=True)
def test_get_project_root_dev():
    """Test get_project_root in development environment."""
    # Assumes test file is in tests/utils/test_helpers.py
    # Project root should be two levels above src (which is one level above utils)
    expected_root = helpers.Path(__file__).parent.parent.parent.resolve()
    root = helpers.get_project_root()
    assert root == expected_root

# --- Tests for get_resource_path ---

@patch('utils.helpers.get_project_root')
def test_get_resource_path(mock_get_root):
    """Test get_resource_path constructs path correctly."""
    mock_root_path = helpers.Path('/fake/project/root')
    mock_get_root.return_value = mock_root_path

    relative = "icons/my_icon.png"
    expected = str(mock_root_path / "resources" / relative)
    assert helpers.get_resource_path(relative) == expected

    relative_dir = "prompts/system"
    expected_dir = str(mock_root_path / "resources" / relative_dir)
    assert helpers.get_resource_path(relative_dir) == expected_dir


# --- Tests for calculate_char_count ---

def test_calculate_char_count():
    """Test character count calculation."""
    assert helpers.calculate_char_count("") == 0
    assert helpers.calculate_char_count("hello") == 5
    assert helpers.calculate_char_count("你好世界") == 4 # Unicode characters
    assert helpers.calculate_char_count(" line\n ") == 7

# --- Tests for calculate_token_count ---

# Mock tiktoken if network access is restricted or for speed
# @patch('tiktoken.get_encoding')
# def test_calculate_token_count_mocked(mock_get_encoding):
#     # Setup mock encoder
#     mock_encoder = MagicMock()
#     mock_encoder.encode.return_value = [1, 2, 3, 4, 5] # Example token IDs
#     mock_get_encoding.return_value = mock_encoder
#     helpers.ENC = mock_encoder # Force use of mock

#     assert helpers.calculate_token_count("some text") == 5
#     mock_encoder.encode.assert_called_once_with("some text")

# Test with actual tiktoken (requires library installed)
def test_calculate_token_count_actual(ensure_utils_initialized):
    """Test token count calculation using actual tiktoken."""
    # Ensure encoding is loaded
    assert helpers.get_encoding() is not None, "Tiktoken encoding failed to load"

    assert helpers.calculate_token_count("") == 0
    # Example counts (may vary slightly based on tiktoken version)
    assert helpers.calculate_token_count("hello world") == 2
    assert helpers.calculate_token_count("tiktoken is great!") == 5
    # Test with potentially problematic input
    assert helpers.calculate_token_count("   ") == 1 # Whitespace counts as tokens

@patch('utils.helpers.get_encoding', return_value=None)
def test_calculate_token_count_no_encoding(mock_get_enc):
    """Test token count returns None if encoding is unavailable."""
    assert helpers.calculate_token_count("some text") is None

@patch('utils.helpers.get_encoding')
def test_calculate_token_count_encoding_error(mock_get_enc):
    """Test token count returns None if encoding raises an error."""
    mock_encoder = MagicMock()
    mock_encoder.encode.side_effect = Exception("Encoding error")
    mock_get_enc.return_value = mock_encoder

    assert helpers.calculate_token_count("some text") is None

# --- Tests for init_utils and get_encoding ---

def test_init_utils_loads_encoding(ensure_utils_initialized):
    """Test that init_utils (called by fixture) loads the encoding."""
    assert helpers.ENC is not None
    assert helpers.get_encoding() is helpers.ENC

# Add test for thread safety if complex interactions are expected
