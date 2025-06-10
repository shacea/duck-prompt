"""
FAH-based Duck Prompt Application
This is the new main application using FAH architecture
"""
import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont

# Add parent directory to path for imports
# This is no longer strictly necessary if run via the root main.py, but good for robustness
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import UI components and the new controller
from src.ui.main_window import MainWindow
from src.ui.controllers.main_controller import MainController
from src.shared.atoms.logger import Logger
from src.ui.styles.font_config import FontConfig
from src.ui.models.file_system_models import dict_to_file_tree_node

# Configure logging
Logger.setup(
    level=logging.INFO,
    format_string='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DuckPromptApp(QApplication):
    """FAH-based Duck Prompt Application"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application metadata
        self.setApplicationName("Duck Prompt FAH")
        self.setOrganizationName("DuckPrompt")
        self.setApplicationDisplayName("Duck Prompt - FAH Edition")
        
        # Configure font settings and load malgun.ttf
        FontConfig.setup_application_fonts(self)
        
        # Set application icon
        try:
            icon_path = str(Path(__file__).parent.parent / "resources" / "icons" / "rubber_duck.ico")
            if Path(icon_path).exists():
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Initialize main window and controller
        self.main_window = None
        self.controller = None
        
        # Setup application
        self._setup_application()
    
    
    def _setup_application(self):
        """Setup the application"""
        try:
            # Suppress font warnings in Qt
            os.environ['QT_LOGGING_RULES'] = 'qt.text.font.db.warning=false'
            
            # Create main window
            self.main_window = MainWindow()
            self.main_window.setWindowTitle("Duck Prompt - FAH Edition")
            
            # Create FAH controller
            self.controller = MainController(self.main_window)
            
            # Connect UI to controller
            self._connect_ui_signals()
            
            # Show main window
            self.main_window.show()
            
            # Initialize application after GUI is shown
            QTimer.singleShot(100, self._initialize_app)
            
        except Exception as e:
            logger.critical(f"Failed to setup application: {e}", exc_info=True)
            raise
    
    def _connect_ui_signals(self):
        """Connect UI signals to the FAH controller"""
        logger.debug("Connecting UI signals to FAH controller.")

        # --- Top buttons ---
        self.main_window.select_project_btn.clicked.connect(self.controller.select_project_folder)
        self.main_window.save_current_work_btn.clicked.connect(self.controller.save_state)
        self.main_window.load_previous_work_btn.clicked.connect(self.controller.load_last_state)
        # Note: reset_program_btn is not connected as it's not part of the FAH controller logic.

        # --- Prompt building ---
        self.main_window.system_tab.textChanged.connect(
            lambda: self.controller.update_system_prompt(self.main_window.system_tab.toPlainText())
        )
        self.main_window.user_tab.textChanged.connect(
            lambda: self.controller.update_user_prompt(self.main_window.user_tab.toPlainText())
        )
        self.main_window.generate_btn.clicked.connect(self.controller.build_prompt)
        self.main_window.generate_tree_btn.clicked.connect(self.controller.generate_directory_tree)
        self.main_window.generate_all_btn.clicked.connect(self.controller.run_all_sequence)
        
        # --- File tree ---
        # Connect the model's check state change signal to the controller
        self.main_window.checkable_proxy.file_check_state_changed.connect(self.controller.check_file)

        if hasattr(self.main_window, 'check_all_btn'): # Assuming a button exists for this
            self.main_window.check_all_btn.clicked.connect(lambda: self.controller.check_all_files(True))
        if hasattr(self.main_window, 'uncheck_all_btn'):
            self.main_window.uncheck_all_btn.clicked.connect(lambda: self.controller.check_all_files(False))
        
        # Context menu refresh action
        # This is handled within MainWindow's context menu creation logic now, which calls the controller.
        
        # --- Controller signals to UI ---
        self.controller.project_folder_changed.connect(self._update_project_folder)
        self.controller.prompt_built.connect(self._update_prompt_display)
        self.controller.tokens_calculated.connect(self._update_token_display)
        self.controller.status_message.connect(self.main_window.statusBar().showMessage)
        self.controller.error_occurred.connect(self._show_error_messagebox)
        self.controller.file_tree_ready.connect(self._update_file_tree_model)

    def _initialize_app(self):
        """Initialize application after GUI is ready"""
        logger.info("Initializing FAH-based Duck Prompt application...")
        # Controller's __init__ handles the initialization sequence now.
        logger.info("Application initialized successfully")
    
    def _update_project_folder(self, folder_path: str):
        """Update UI when project folder changes"""
        if hasattr(self.main_window, 'project_folder_label'):
            self.main_window.project_folder_label.setText(f"현재 프로젝트 폴더: {folder_path}")
        self.main_window.setWindowTitle(f"{Path(folder_path).name} - Duck Prompt FAH")
    
    def _update_prompt_display(self, prompt: str):
        """Update prompt display if available"""
        if hasattr(self.main_window, 'prompt_output_tab'):
            self.main_window.prompt_output_tab.setPlainText(prompt)
    
    def _update_token_display(self, token_info: dict):
        """Update token count display"""
        if hasattr(self.main_window, 'token_count_label'):
            total_tokens = token_info.get('total_tokens', 0)
            model = token_info.get('model', 'Unknown')
            self.main_window.token_count_label.setText(f"Tokens: {total_tokens:,} ({model})")

    def _show_error_messagebox(self, error_message: str):
        """Show error in a message box."""
        QMessageBox.critical(self.main_window, "Error", error_message)
    
    def _update_file_tree_model(self, tree_dict: dict):
        """Update the file tree view model with new data."""
        if not tree_dict:
            self.main_window.cached_model.clear()
            logger.warning("Received empty tree dictionary, clearing model.")
            return
        
        try:
            # Rebuild the FileTreeNode structure
            root_node = dict_to_file_tree_node(tree_dict)
            
            # Populate the model
            self.main_window.cached_model.populate_from_cache(root_node)
            logger.info("File tree model updated successfully.")
        except Exception as e:
            logger.error(f"Failed to update file tree model from dictionary: {e}", exc_info=True)

    def cleanup(self):
        """Cleanup on application exit"""
        logger.info("Shutting down FAH application...")
        if self.controller:
            self.controller.shutdown()
        logger.info("Application shutdown complete")

def main():
    """Main entry point"""
    # Apply font fixes before creating QApplication
    FontConfig.apply_font_fixes()
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # Create and run application
    app = DuckPromptApp(sys.argv)
    
    # Set global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    # Run application
    exit_code = app.exec()
    
    # Cleanup
    app.cleanup()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
