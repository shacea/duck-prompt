"""FAH-based main controller - manages main window operations using FAH architecture"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
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
    file_tree_ready = pyqtSignal(dict)
    
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

    def _set_default_ui_states(self):
        """Sets default states for UI elements not covered by configuration."""
        logger.debug("Setting default UI component states.")
        self.main_window.gemini_dmp_checkbox.setChecked(True)
    
    @pyqtSlot(str, object)
    def _handle_command_completion(self, command_name: str, result: Any):
        """Handle successful command completion"""
        logger.debug(f"Command {command_name} completed: {result}")
        
        # Handle specific command results
        if command_name == "SetProjectFolder":
            if result.get("success"):
                self.project_folder_changed.emit(result.get("path", ""))
                self.status_message.emit(f"Project folder set: {result.get('path', '')}")
                if result.get("tree"):
                    self.file_tree_ready.emit(result["tree"])
        
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
            if result and 'settings' in result:
                self._load_default_system_prompt(result['settings'])
            # Set default UI states after config is loaded
            self._set_default_ui_states()
    
    @pyqtSlot(str, str)
    def _handle_command_failure(self, command_name: str, error: str):
        """Handle command failure"""
        logger.error(f"Command {command_name} failed: {error}")
        self.error_occurred.emit(f"{command_name} failed: {error}")
    
    def _load_default_system_prompt(self, settings: dict):
        """Loads the default system prompt from the path specified in settings."""
        prompt_path_str = settings.get('default_system_prompt_path')
        if not prompt_path_str:
            logger.info("No default system prompt path configured.")
            return

        # The path in config is relative to the project root.
        # The FAHBridge runs commands from the project root directory,
        # so relative paths should work correctly.
        prompt_path = Path(prompt_path_str)

        try:
            from src.features.file_management.commands import GetFileContent

            def on_prompt_content_received(result):
                if result and result.get('content') is not None:
                    content = result['content']
                    self.main_window.system_tab.setPlainText(content)
                    self.status_message.emit("Default system prompt loaded.")
                    logger.info("Successfully loaded default system prompt.")
                else:
                    error_msg = f"Failed to read default system prompt file: {prompt_path_str}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
            
            self.bridge.execute_command(
                "file_management", 
                GetFileContent(file_path=str(prompt_path)),
                callback=on_prompt_content_received
            )
            
        except Exception as e:
            logger.error(f"Error loading default system prompt: {e}", exc_info=True)
            self.error_occurred.emit(f"Error loading system prompt: {e}")

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
        """Build the final prompt using only checked files."""
        from src.features.prompt_builder.commands import BuildPrompt
        from src.features.file_management.commands import GetDirectoryTree, GetProjectFolder

        def _on_prompt_built(result):
            if result.get("success"):
                prompt = result.get("prompt", "")
                clipboard = QApplication.instance().clipboard()
                clipboard.setText(prompt)
                self.status_message.emit(f"Prompt ({result.get('length', 0)} chars) built and copied to clipboard.")
        
        def _on_tree_generated(result):
            tree_text = result.get("tree", "")
            checked_files = [p for p in self.main_window.checkable_proxy.get_all_checked_paths() if not Path(p).is_dir()]
            self.bridge.execute_command(
                "prompt_builder", 
                BuildPrompt(files_to_include=checked_files, directory_tree=tree_text), 
                callback=_on_prompt_built
            )

        def _on_folder_retrieved(result):
            folder = result.get("path")
            if folder:
                self.bridge.execute_command(
                    "file_management",
                    GetDirectoryTree(root_path=folder, checked_only=True),
                    callback=_on_tree_generated
                )

        self.bridge.execute_command("file_management", GetProjectFolder(), callback=_on_folder_retrieved)
    
    @pyqtSlot()
    def calculate_prompt_tokens(self):
        """Calculate tokens for the current prompt"""
        from src.features.tokens.commands import CalculatePromptTokens
        model = self.main_window.token_model_combo.currentText() or "gpt-4"
        def handle_result(result):
            if "error" not in result:
                self.tokens_calculated.emit(result)
        self.bridge.execute_command("tokens", CalculatePromptTokens(model=model), callback=handle_result)
    
    @pyqtSlot()
    def refresh_file_tree(self):
        """Refresh the file tree"""
        from src.features.file_management.commands import RefreshFileSystem
        self.bridge.execute_command("file_management", RefreshFileSystem())
        self.status_message.emit("File system refreshed")
    
    @pyqtSlot()
    def generate_directory_tree(self):
        """Generate directory tree text for checked items only."""
        from src.features.file_management.commands import GetDirectoryTree, GetProjectFolder
        
        def get_folder_callback(result):
            folder = result.get("path")
            if folder:
                self.bridge.execute_command(
                    "file_management",
                    GetDirectoryTree(root_path=folder, checked_only=True),
                    callback=self._handle_directory_tree
                )
        
        self.bridge.execute_command("file_management", GetProjectFolder(), callback=get_folder_callback)
    
    def _handle_directory_tree(self, result):
        """Handle directory tree generation result, updating UI and clipboard."""
        tree = result.get("tree", "")
        if tree:
            self.main_window.dir_structure_tab.setPlainText(tree)
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(tree)
            self.status_message.emit("Directory tree generated and copied to clipboard.")
    
    @pyqtSlot()
    def run_all_sequence(self):
        """Execute the full sequence using only checked files."""
        self.build_prompt() # Re-use the build_prompt logic which now does the full sequence
        # After the prompt is built, we want to switch the tab
        # The prompt_built signal is connected to the main window's display slot,
        # so we can connect another slot to it for tab switching.
        # To avoid connecting multiple times, we can use a single-shot connection.
        try:
            self.prompt_built.disconnect(self._switch_to_prompt_tab)
        except TypeError:
            pass # was not connected
        self.prompt_built.connect(self._switch_to_prompt_tab, type=Qt.ConnectionType.SingleShotConnection)

    @pyqtSlot(str)
    def _switch_to_prompt_tab(self, prompt_text: str):
        """Switches the main tab widget to the prompt output tab."""
        if prompt_text:
            self.main_window.build_tabs.setCurrentWidget(self.main_window.prompt_output_tab)

    @pyqtSlot()
    def save_state(self):
        """Save application state"""
        logger.warning("State saving feature is not yet implemented.")
        self.status_message.emit("State saving not implemented.")
    
    @pyqtSlot()
    def load_last_state(self):
        """Load last saved state"""
        logger.warning("State loading feature is not yet implemented.")
        self.status_message.emit("State loading not implemented.")
    
    def shutdown(self):
        """Cleanup on shutdown"""
        self.save_state()
        self.bridge.shutdown()
