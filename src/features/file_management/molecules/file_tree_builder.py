"""File tree builder molecule - builds hierarchical file structures"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class FileTreeNode:
    """Represents a node in the file tree"""
    
    def __init__(self, path: Path, is_dir: bool = False):
        self.path = path
        self.name = path.name
        self.is_dir = is_dir
        self.children: List[FileTreeNode] = []
        self.checked = False
        self.parent: Optional[FileTreeNode] = None
    
    def add_child(self, child: 'FileTreeNode'):
        """Add a child node"""
        child.parent = self
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'path': str(self.path),
            'name': self.name,
            'is_dir': self.is_dir,
            'checked': self.checked,
            'children': [child.to_dict() for child in self.children]
        }


class FileTreeBuilder:
    """Builds hierarchical file tree structures"""
    
    def __init__(self):
        self.root_node: Optional[FileTreeNode] = None
        self.path_to_node: Dict[str, FileTreeNode] = {}
        self.checked_paths: Set[str] = set()
    
    def build_tree(self, root_path: Path, file_paths: List[Path]) -> FileTreeNode:
        """Build a file tree from a list of file paths"""
        self.root_node = FileTreeNode(root_path, is_dir=True)
        self.path_to_node = {str(root_path): self.root_node}
        
        # Sort paths to ensure parents come before children
        sorted_paths = sorted(file_paths)
        
        for file_path in sorted_paths:
            self._add_path_to_tree(file_path, root_path)
        
        # Apply checked states
        self._apply_checked_states()
        
        return self.root_node
    
    def _add_path_to_tree(self, file_path: Path, root_path: Path):
        """Add a file path to the tree"""
        try:
            relative_path = file_path.relative_to(root_path)
        except ValueError:
            logger.warning(f"Path {file_path} is not relative to root {root_path}")
            return
        
        # Build the path components
        parts = relative_path.parts
        current_path = root_path
        current_node = self.root_node
        
        # Process each part of the path
        for i, part in enumerate(parts):
            current_path = current_path / part
            path_str = str(current_path)
            
            if path_str not in self.path_to_node:
                # Create new node
                is_dir = i < len(parts) - 1 or current_path.is_dir()
                new_node = FileTreeNode(current_path, is_dir=is_dir)
                current_node.add_child(new_node)
                self.path_to_node[path_str] = new_node
                current_node = new_node
            else:
                current_node = self.path_to_node[path_str]
    
    def check_file(self, file_path: str, checked: bool):
        """Check or uncheck a file"""
        if checked:
            self.checked_paths.add(file_path)
        else:
            self.checked_paths.discard(file_path)
        
        # Update node if tree is built
        if file_path in self.path_to_node:
            self.path_to_node[file_path].checked = checked
    
    def check_all(self, checked: bool):
        """Check or uncheck all files"""
        if checked:
            # Add all file paths to checked set
            for path_str, node in self.path_to_node.items():
                if not node.is_dir:
                    self.checked_paths.add(path_str)
                    node.checked = True
        else:
            # Clear all checked paths
            self.checked_paths.clear()
            for node in self.path_to_node.values():
                node.checked = False
    
    def get_checked_paths(self) -> List[str]:
        """Get list of all checked paths (files and directories)."""
        return sorted(list(self.checked_paths))
    
    def _apply_checked_states(self):
        """Apply checked states to nodes"""
        for path_str in self.checked_paths:
            if path_str in self.path_to_node:
                self.path_to_node[path_str].checked = True
    
    def generate_tree_text(self, node: Optional[FileTreeNode] = None, prefix: str = "", is_last: bool = True) -> str:
        """Generate text representation of the tree"""
        if node is None:
            node = self.root_node
            if node is None:
                return ""
        
        # Build the current line
        connector = "└── " if is_last else "├── "
        line = prefix + connector + node.name
        
        if node.is_dir:
            line += "/"
        if node.checked:
            line += " ✓"
        
        lines = [line]
        
        # Process children
        if node.children:
            extension = "    " if is_last else "│   "
            for i, child in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                child_lines = self.generate_tree_text(
                    child, 
                    prefix + extension, 
                    is_last_child
                )
                lines.append(child_lines)
        
        return "\n".join(lines)
