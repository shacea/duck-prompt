import pytest
import os
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QApplication, QTreeView # QApplication needed for QFileSystemModel

# Modules to test
from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel

# --- Fixtures ---

# QApplication fixture (needed for Qt models)
@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

# FilteredFileSystemModel fixture
@pytest.fixture
def fs_model(qt_app):
    model = FilteredFileSystemModel()
    return model

# CheckableProxyModel fixture
@pytest.fixture
def proxy_model(qt_app, fs_model, tmp_path):
    # Mock project folder getter and tree view
    project_path = str(tmp_path / "project")
    os.makedirs(project_path, exist_ok=True)
    # Create dummy files/dirs
    (tmp_path / "project" / "file1.txt").touch()
    (tmp_path / "project" / "subdir").mkdir()
    (tmp_path / "project" / "subdir" / "file2.py").touch()
    (tmp_path / "project" / ".hidden").touch()
    (tmp_path / "project" / "ignored_dir").mkdir()
    (tmp_path / "project" / "ignored_dir" / "a.log").touch()
    # Create .gitignore
    with open(tmp_path / "project" / ".gitignore", "w") as f:
        f.write("*.log\n")
        f.write("ignored_dir/\n")
        f.write(".hidden\n")


    mock_tree_view = QTreeView() # Basic QTreeView instance
    # Getter function returns the mock project path
    getter = lambda: project_path
    proxy = CheckableProxyModel(fs_model, getter, mock_tree_view)
    proxy.setSourceModel(fs_model)

    # Set root path on the source model AFTER proxy is set up
    root_index = fs_model.setRootPathFiltered(project_path)
    proxy.set_ignore_patterns({"*.log", "ignored_dir/", ".hidden"}) # Set ignore patterns

    # Map the root index for the proxy
    proxy_root_index = proxy.mapFromSource(root_index)
    mock_tree_view.setRootIndex(proxy_root_index) # Set root on the view

    return proxy, fs_model, project_path # Return proxy, source model, and path

# --- FilteredFileSystemModel Tests ---

def test_filtered_model_set_root_path(fs_model, tmp_path):
    """Test setting the root path on the filtered model."""
    test_dir = tmp_path / "test_root"
    test_dir.mkdir()
    (test_dir / "file.txt").touch()
    (test_dir / "subdir").mkdir()

    root_index = fs_model.setRootPathFiltered(str(test_dir))
    assert root_index.isValid()
    assert fs_model.filePath(root_index) == str(test_dir)
    # Check if children were fetched (at least the direct ones)
    assert fs_model.rowCount(root_index) > 0 # Should have file.txt and subdir

# Add more tests for _fetch_all_recursively if possible (might be hard to test directly)

# --- CheckableProxyModel Tests ---

def test_proxy_model_initialization(proxy_model):
    """Test basic initialization of the proxy model."""
    proxy, _, _ = proxy_model
    assert proxy is not None
    assert proxy.sourceModel() is not None

def test_proxy_model_filtering(proxy_model):
    """Test if items are filtered based on ignore patterns."""
    proxy, fs_model, project_path = proxy_model
    root_src_index = fs_model.index(project_path)
    root_proxy_index = proxy.mapFromSource(root_src_index)

    # Wait for model population if necessary (usually happens synchronously here)
    # QTest.qWait(100) # If using QTest

    assert root_proxy_index.isValid()

    # Get children of the root in the proxy model
    children_names = set()
    for row in range(proxy.rowCount(root_proxy_index)):
        child_proxy_index = proxy.index(row, 0, root_proxy_index)
        child_src_index = proxy.mapToSource(child_proxy_index)
        if child_src_index.isValid():
             children_names.add(fs_model.fileName(child_src_index))

    print(f"Visible children: {children_names}")

    # Check visible items
    assert "file1.txt" in children_names
    assert "subdir" in children_names
    # Check filtered items
    assert ".hidden" not in children_names
    assert "ignored_dir" not in children_names
    assert ".gitignore" in children_names # .gitignore itself is not ignored by default patterns here

    # Check subdirectory filtering
    subdir_src_index = fs_model.index(os.path.join(project_path, "subdir"))
    subdir_proxy_index = proxy.mapFromSource(subdir_src_index)
    assert subdir_proxy_index.isValid()
    assert proxy.rowCount(subdir_proxy_index) == 1 # Should contain file2.py
    file2_proxy_index = proxy.index(0, 0, subdir_proxy_index)
    file2_src_index = proxy.mapToSource(file2_proxy_index)
    assert fs_model.fileName(file2_src_index) == "file2.py"


def test_proxy_model_check_state_data(proxy_model):
    """Test getting and setting check state."""
    proxy, fs_model, project_path = proxy_model
    root_src_index = fs_model.index(project_path)
    root_proxy_index = proxy.mapFromSource(root_src_index)

    file1_proxy_index = proxy.index(0, 0, root_proxy_index) # Assuming file1.txt is first visible
    file1_path = proxy.get_file_path_from_index(file1_proxy_index)

    # Initial state should be Unchecked
    assert proxy.data(file1_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.checked_files_dict.get(file1_path) is None or proxy.checked_files_dict.get(file1_path) is False

    # Set state to Checked
    assert proxy.setData(file1_proxy_index, Qt.Checked, Qt.CheckStateRole) is True
    assert proxy.data(file1_proxy_index, Qt.CheckStateRole) == Qt.Checked
    assert proxy.checked_files_dict.get(file1_path) is True

    # Set state back to Unchecked
    assert proxy.setData(file1_proxy_index, Qt.Unchecked, Qt.CheckStateRole) is True
    assert proxy.data(file1_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.checked_files_dict.get(file1_path) is False

def test_proxy_model_check_folder_propagates(proxy_model):
    """Test that checking a folder checks its visible children."""
    proxy, fs_model, project_path = proxy_model
    root_src_index = fs_model.index(project_path)
    root_proxy_index = proxy.mapFromSource(root_src_index)

    # Find the 'subdir' proxy index
    subdir_proxy_index = QModelIndex()
    for row in range(proxy.rowCount(root_proxy_index)):
        idx = proxy.index(row, 0, root_proxy_index)
        if proxy.data(idx, Qt.DisplayRole) == "subdir":
            subdir_proxy_index = idx
            break
    assert subdir_proxy_index.isValid()

    # Find the 'file2.py' proxy index under 'subdir'
    file2_proxy_index = proxy.index(0, 0, subdir_proxy_index)
    assert file2_proxy_index.isValid()
    assert proxy.data(file2_proxy_index, Qt.DisplayRole) == "file2.py"

    file2_path = proxy.get_file_path_from_index(file2_proxy_index)
    subdir_path = proxy.get_file_path_from_index(subdir_proxy_index)

    # Initially unchecked
    assert proxy.data(subdir_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.data(file2_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.checked_files_dict.get(subdir_path) is False
    assert proxy.checked_files_dict.get(file2_path) is False

    # Check the folder
    proxy.setData(subdir_proxy_index, Qt.Checked, Qt.CheckStateRole)

    # Both folder and child file should be checked
    assert proxy.data(subdir_proxy_index, Qt.CheckStateRole) == Qt.Checked
    assert proxy.data(file2_proxy_index, Qt.CheckStateRole) == Qt.Checked
    assert proxy.checked_files_dict.get(subdir_path) is True
    assert proxy.checked_files_dict.get(file2_path) is True

    # Uncheck the folder
    proxy.setData(subdir_proxy_index, Qt.Unchecked, Qt.CheckStateRole)

    # Both should be unchecked
    assert proxy.data(subdir_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.data(file2_proxy_index, Qt.CheckStateRole) == Qt.Unchecked
    assert proxy.checked_files_dict.get(subdir_path) is False
    assert proxy.checked_files_dict.get(file2_path) is False


def test_proxy_model_get_checked_paths(proxy_model):
    """Test retrieving lists of checked paths."""
    proxy, _, _ = proxy_model
    root_proxy_index = proxy.index(0,0) # Assuming root is the first item mapped

    file1_proxy_index = proxy.index(0, 0, root_proxy_index) # file1.txt
    subdir_proxy_index = proxy.index(1, 0, root_proxy_index) # subdir
    file2_proxy_index = proxy.index(0, 0, subdir_proxy_index) # file2.py

    file1_path = proxy.get_file_path_from_index(file1_proxy_index)
    subdir_path = proxy.get_file_path_from_index(subdir_proxy_index)
    file2_path = proxy.get_file_path_from_index(file2_proxy_index)

    # Check file1 and subdir (which checks file2)
    proxy.setData(file1_proxy_index, Qt.Checked, Qt.CheckStateRole)
    proxy.setData(subdir_proxy_index, Qt.Checked, Qt.CheckStateRole)

    all_checked = proxy.get_all_checked_paths()
    checked_files_only = proxy.get_checked_files()

    assert len(all_checked) == 3
    assert file1_path in all_checked
    assert subdir_path in all_checked
    assert file2_path in all_checked

    assert len(checked_files_only) == 2
    assert file1_path in checked_files_only
    assert file2_path in checked_files_only
    assert subdir_path not in checked_files_only # It's a directory
