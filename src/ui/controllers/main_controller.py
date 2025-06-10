"""FAH-based main controller - manages main window operations using FAH architecture"""
import logging
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from ..bridges.fah_bridge import FAHBridge

logger = logging.getLogger(__name__)


class MainController(QObject):
    """Main controller using FAH architecture"""
    
    # Signals
    project_folder_changed = pyqtSignal(str)
    prompt_built = pyqtSignal(str)
    tokens_calculated = pyqtSignal(dict)
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.bridge = FAHBridge()
        
        # Connect bridge signals
        self.bridge.command_completed.connect(self._handle_command_completion)
        self.bridge.command_failed.connect(self._handle_command_failure)
        
        # Initialize application
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the application"""
        # Load configuration
        self.bridge.load_configuration()
        
        # Set up initial state
        self.status_message.emit("Application initialized")
    
    @pyqtSlot(str, object)
    def _handle_command_completion(self, command_name: str, result: Any):
        """Handle successful command completion"""
        logger.debug(f"Command {command_name} completed: {result}")
        
        # Handle specific command results
        if command_name == "SetProjectFolder":
            if result.get("success"):
                self.project_folder_changed.emit(result.get("path", ""))
                self.status_message.emit(f"Project folder set: {result.get('path', '')}")
        
        elif command_name == "BuildPrompt":
            if result.get("success"):
                prompt = result.get("prompt", "")
                self.prompt_built.emit(prompt)
                self.status_message.emit(f"Prompt built: {result.get('length', 0)} characters")
            else:
                errors = result.get("errors", [])
                self.error_occurred.emit(f"Failed to build prompt: {', '.join(errors)}")
        
        elif command_name == "CalculateTokens":
            self.tokens_calculated.emit(result)
            self.status_message.emit(f"Tokens calculated: {result.get('tokens', 0)}")
        
        elif command_name == "LoadConfiguration":
            self.status_message.emit("Configuration loaded successfully")
    
    @pyqtSlot(str, str)
    def _handle_command_failure(self, command_name: str, error: str):
        """Handle command failure"""
        logger.error(f"Command {command_name} failed: {error}")
        self.error_occurred.emit(f"{command_name} failed: {error}")
    
    # UI action handlers
    
    @pyqtSlot()
    def select_project_folder(self):
        """Show folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self.main_window,
            "Select Project Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.bridge.set_project_folder(folder)
    
    @pyqtSlot(str, bool)
    def check_file(self, file_path: str, checked: bool):
        """Check or uncheck a file"""
        from src.features.file_management.commands import CheckFile
        self.bridge.execute_command("file_management", CheckFile(file_path=file_path, checked=checked))
    
    @pyqtSlot(bool)
    def check_all_files(self, checked: bool):
        """Check or uncheck all files"""
        from src.features.file_management.commands import CheckAllFiles
        self.bridge.execute_command("file_management", CheckAllFiles(checked=checked))
    
    @pyqtSlot(str)
    def update_system_prompt(self, content: str):
        """Update system prompt content"""
        from src.features.prompt_builder.commands import SetSystemPrompt
        self.bridge.execute_command("prompt_builder", SetSystemPrompt(content=content))
    
    @pyqtSlot(str)
    def update_user_prompt(self, content: str):
        """Update user prompt content"""
        from src.features.prompt_builder.commands import SetUserPrompt
        self.bridge.execute_command("prompt_builder", SetUserPrompt(content=content))
    
    @pyqtSlot()
    def build_prompt(self):
        """Build the final prompt"""
        from src.features.prompt_builder.commands import BuildPrompt
        
        def handle_result(result):
            if result.get("success"):
                # Copy to clipboard
                prompt = result.get("prompt", "")
                clipboard = self.main_window.app.clipboard()
                clipboard.setText(prompt)
                
                # Show success message
                QMessageBox.information(
                    self.main_window,
                    "Prompt Built",
                    f"Prompt built successfully!\n"
                    f"Length: {result.get('length', 0)} characters\n"
                    f"The prompt has been copied to clipboard."
                )
        
        self.bridge.execute_command("prompt_builder", BuildPrompt(), callback=handle_result)
    
    @pyqtSlot()
    def calculate_prompt_tokens(self):
        """Calculate tokens for the current prompt"""
        from src.features.tokens.commands import CalculatePromptTokens
        
        # Get current model selection (default to gpt-4)
        model = self.main_window.token_model_combo.currentText() or "gpt-4"
        
        def handle_result(result):
            if "error" not in result:
                self.tokens_calculated.emit(result)
        
        self.bridge.execute_command(
            "tokens",
            CalculatePromptTokens(model=model),
            callback=handle_result
        )
    
    @pyqtSlot()
    def refresh_file_tree(self):
        """Refresh the file tree"""
        from src.features.file_management.commands import RefreshFileSystem
        self.bridge.execute_command("file_management", RefreshFileSystem())
        self.status_message.emit("File system refreshed")
    
    @pyqtSlot()
    def generate_directory_tree(self):
        """Generate directory tree text"""
        from src.features.file_management.commands import GetDirectoryTree, GetProjectFolder
        
        # First get the project folder
        def get_folder_callback(result):
            folder = result.get("path")
            if folder:
                # Then generate tree
                from src.features.file_management.commands import GetDirectoryTree
                self.bridge.execute_command(
                    "file_management",
                    GetDirectoryTree(root_path=folder),
                    callback=self._handle_directory_tree
                )
        
        self.bridge.execute_command(
            "file_management",
            GetProjectFolder(),
            callback=get_folder_callback
        )
    
    def _handle_directory_tree(self, result):
        """Handle directory tree generation result"""
        tree = result.get("tree", "")
        if tree:
            # Copy to clipboard
            clipboard = self.main_window.app.clipboard()
            clipboard.setText(tree)
            
            QMessageBox.information(
                self.main_window,
                "Directory Tree",
                "Directory tree has been copied to clipboard!"
            )
    
    @pyqtSlot()
    def save_state(self):
        """Save application state"""
        logger.warning("State saving feature is not yet implemented.")
        self.status_message.emit("State saving not implemented.")
        # from src.features.state.commands import SaveState
        # self.bridge.execute_command("state", SaveState())
        # self.status_message.emit("State saved")
    
    @pyqtSlot()
    def load_last_state(self):
        """Load last saved state"""
        logger.warning("State loading feature is not yet implemented.")
        self.status_message.emit("State loading not implemented.")
        # from src.features.state.commands import LoadLastState
        # self.bridge.execute_command("state", LoadLastState())
        # self.status_message.emit("Last state loaded")
    
    def shutdown(self):
        """Cleanup on shutdown"""
        # Save state before shutdown
        self.save_state()
        
        # Shutdown bridge
        self.bridge.shutdown()
