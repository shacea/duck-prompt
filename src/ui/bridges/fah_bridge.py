"""FAH Bridge - Main bridge between UI and FAH architecture"""
import asyncio
import logging
from typing import Any, Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)


class AsyncWorker(QThread):
    """Worker thread for running async FAH commands"""
    
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, coro, parent=None):
        super().__init__(parent)
        self.coro = coro
        self.loop = None
    
    def run(self):
        """Run the async coroutine in a new event loop"""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Run the coroutine
            result = self.loop.run_until_complete(self.coro)
            self.result_ready.emit(result)
            
        except Exception as e:
            logger.error(f"Error in async worker: {e}")
            self.error_occurred.emit(str(e))
        finally:
            if self.loop:
                self.loop.close()


class FAHBridge(QObject):
    """Bridge between PyQt6 UI and FAH command bus architecture"""
    
    # Signals for UI updates
    command_completed = pyqtSignal(str, object)  # command_name, result
    command_failed = pyqtSignal(str, str)  # command_name, error
    
    def __init__(self):
        super().__init__()
        self._workers = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Import gateway after initialization
        self._gateway = None
        self._initialize_gateway()
    
    def _initialize_gateway(self):
        """Initialize gateway and import all handlers"""
        try:
            # Import gateway
            from src import gateway as gw
            self._gateway = gw
            
            # Import all feature handlers to register them
            import src.features.database.handlers
            import src.features.config.handlers
            import src.features.file_management.handlers
            import src.features.prompt_builder.handlers
            import src.features.tokens.handlers
            import src.features.dmp_processor.handlers
            
            logger.info("FAH Bridge initialized with all handlers")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAH Bridge: {e}")
            raise
    
    def execute_command(self, bus_name: str, command: Any, callback: Optional[Callable] = None):
        """Execute a FAH command asynchronously"""
        
        async def _execute():
            """Inner async function to execute command"""
            try:
                # Get the command bus
                bus = getattr(self._gateway, f"{bus_name}_command_bus", None)
                if not bus:
                    raise ValueError(f"Command bus '{bus_name}_command_bus' not found")
                
                # Execute command
                result = await bus.handle(command)
                return result
                
            except Exception as e:
                logger.error(f"Error executing command {command.__class__.__name__}: {e}")
                raise
        
        # Create worker thread
        worker = AsyncWorker(_execute())
        
        # Connect signals
        if callback:
            worker.result_ready.connect(callback)
        
        worker.result_ready.connect(
            lambda result: self.command_completed.emit(command.__class__.__name__, result)
        )
        worker.error_occurred.connect(
            lambda error: self.command_failed.emit(command.__class__.__name__, error)
        )
        
        # Track worker and start
        self._workers.append(worker)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.start()
    
    def execute_command_sync(self, bus_name: str, command: Any) -> Any:
        """Execute a FAH command synchronously (blocks)"""
        future = self._executor.submit(self._execute_sync, bus_name, command)
        return future.result()
    
    def _execute_sync(self, bus_name: str, command: Any) -> Any:
        """Internal sync execution"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            bus = getattr(self._gateway, f"{bus_name}_command_bus", None)
            if not bus:
                raise ValueError(f"Command bus '{bus_name}_command_bus' not found")
            
            result = loop.run_until_complete(bus.handle(command))
            return result
        finally:
            loop.close()
    
    def _cleanup_worker(self, worker: AsyncWorker):
        """Clean up finished worker"""
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()
    
    def shutdown(self):
        """Shutdown the bridge"""
        # Wait for all workers to finish
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
    
    # Convenience methods for common operations
    
    @pyqtSlot(str)
    def set_project_folder(self, folder_path: str):
        """Set project folder"""
        from src.features.file_management.commands import SetProjectFolder
        self.execute_command("file_management", SetProjectFolder(folder_path=folder_path))
    
    @pyqtSlot()
    def load_configuration(self):
        """Load application configuration"""
        from src.features.config.commands import LoadConfiguration
        self.execute_command("config", LoadConfiguration())
    
    @pyqtSlot(str, bool)
    def check_file(self, file_path: str, checked: bool):
        """Check or uncheck a file"""
        from src.features.file_management.commands import CheckFile
        self.execute_command("file_management", CheckFile(file_path=file_path, checked=checked))
    
    @pyqtSlot(str)
    def set_system_prompt(self, content: str):
        """Set system prompt content"""
        from src.features.prompt_builder.commands import SetSystemPrompt
        self.execute_command("prompt_builder", SetSystemPrompt(content=content))
    
    @pyqtSlot(str)
    def set_user_prompt(self, content: str):
        """Set user prompt content"""
        from src.features.prompt_builder.commands import SetUserPrompt
        self.execute_command("prompt_builder", SetUserPrompt(content=content))
    
    @pyqtSlot()
    def build_prompt(self, callback: Optional[Callable] = None):
        """Build the final prompt"""
        from src.features.prompt_builder.commands import BuildPrompt
        self.execute_command("prompt_builder", BuildPrompt(), callback)
    
    @pyqtSlot(str, str)
    def calculate_tokens(self, text: str, model: str = "gpt-4"):
        """Calculate tokens for text"""
        from src.features.tokens.commands import CalculateTokens
        self.execute_command("tokens", CalculateTokens(text=text, model=model))
