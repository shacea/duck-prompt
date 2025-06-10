"""Font configuration for the application"""
import sys
import os
import logging
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class FontConfig:
    """Manages font configuration for the application"""
    
    # Platform-specific font recommendations
    FONT_FAMILIES = {
        "win32": [
            "Segoe UI",           # Modern Windows UI font
            "Microsoft YaHei UI", # Chinese support
            "Malgun Gothic",      # Korean support
            "Yu Gothic UI",       # Japanese support
            "Tahoma",            # Fallback
            "Arial"              # Last resort
        ],
        "darwin": [
            "SF Pro Text",       # macOS system font
            "Helvetica Neue",    # Classic macOS
            "Arial",            # Fallback
            "Lucida Grande"     # Legacy macOS
        ],
        "linux": [
            "Ubuntu",           # Ubuntu default
            "DejaVu Sans",      # Common Linux font
            "Liberation Sans",  # Red Hat fonts
            "Noto Sans",        # Google's universal font
            "Arial"            # Fallback
        ]
    }
    
    # Font sizes for different UI elements
    FONT_SIZES = {
        "default": 10,
        "small": 8,
        "medium": 10,
        "large": 12,
        "title": 14
    }
    
    @classmethod
    def setup_application_fonts(cls, app: QApplication):
        """Setup fonts for the entire application"""
        # First try to load the Malgun Gothic font from resources
        custom_font_loaded = cls._load_custom_font()
        
        if custom_font_loaded:
            # Use Malgun Gothic as the default font
            default_font = QFont("Malgun Gothic")
            default_font.setPointSize(cls.FONT_SIZES["default"])
            default_font.setStyleHint(QFont.StyleHint.SansSerif)
            default_font.setWeight(QFont.Weight.Normal)
            
            # Apply to application
            app.setFont(default_font)
            logger.info(f"Application font set to: Malgun Gothic ({default_font.pointSize()}pt)")
        else:
            # Fallback to platform-specific fonts
            platform = sys.platform
            if platform not in cls.FONT_FAMILIES:
                platform = "linux"  # Default to Linux fonts
            
            font_families = cls.FONT_FAMILIES[platform]
            
            # Find the first available font
            default_font = cls._find_available_font(font_families)
            
            # Configure the font
            default_font.setPointSize(cls.FONT_SIZES["default"])
            default_font.setStyleHint(QFont.StyleHint.SansSerif)
            default_font.setWeight(QFont.Weight.Normal)
            
            # Apply to application
            app.setFont(default_font)
            
            logger.info(f"Application font set to: {default_font.family()} ({default_font.pointSize()}pt)")
        
        # Log available fonts for debugging
        cls._log_available_fonts()
    
    @classmethod
    def _find_available_font(cls, font_families: list) -> QFont:
        """Find the first available font from the list"""
        # In PyQt6, QFontDatabase is used as static methods
        available_families = QFontDatabase.families()
        
        for family in font_families:
            if family in available_families:
                font = QFont(family)
                # In PyQt6, we check if the font family was actually set
                if font.family() == family:
                    logger.debug(f"Found exact match for font: {family}")
                    return font
        
        # If no exact match, try partial match
        for family in font_families:
            for available in available_families:
                if family.lower() in available.lower():
                    font = QFont(available)
                    logger.debug(f"Found partial match: {available} for {family}")
                    return font
        
        # Last resort - use system default
        logger.warning("No preferred fonts found, using system default")
        return QFont()
    
    @classmethod
    def _load_custom_font(cls) -> bool:
        """Load custom Malgun Gothic font from resources"""
        try:
            # Find the font file path
            font_paths = [
                Path("resources/fonts/malgun.ttf"),
                Path(__file__).parent.parent.parent.parent / "resources" / "fonts" / "malgun.ttf",
                Path(os.getcwd()) / "resources" / "fonts" / "malgun.ttf"
            ]
            
            font_path = None
            for path in font_paths:
                if path.exists():
                    font_path = path
                    break
            
            if not font_path:
                logger.warning("Malgun Gothic font file not found in resources")
                return False
            
            # Load the font
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id == -1:
                logger.error(f"Failed to load font from {font_path}")
                return False
            
            # Get the font family name
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if not font_families:
                logger.error("No font families found in loaded font")
                return False
            
            logger.info(f"Successfully loaded custom font: {font_families[0]} from {font_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading custom font: {e}")
            return False
    
    @classmethod
    def _log_available_fonts(cls):
        """Log available system fonts for debugging"""
        # In PyQt6, QFontDatabase is used as static methods
        families = QFontDatabase.families()
        
        logger.debug(f"Total available font families: {len(families)}")
        
        # Log a sample of available fonts
        sample_size = min(10, len(families))
        logger.debug(f"Sample of available fonts: {families[:sample_size]}")
    
    @classmethod
    def get_font_for_element(cls, element_type: str) -> QFont:
        """Get configured font for specific UI element"""
        base_font = QApplication.font()
        
        if element_type == "title":
            font = QFont(base_font)
            font.setPointSize(cls.FONT_SIZES["title"])
            font.setWeight(QFont.Weight.Bold)
            return font
        elif element_type == "code":
            # Use monospace font for code
            font = QFont("Consolas" if sys.platform == "win32" else "Monaco" if sys.platform == "darwin" else "Monospace")
            font.setPointSize(cls.FONT_SIZES["medium"])
            font.setStyleHint(QFont.StyleHint.Monospace)
            return font
        elif element_type == "small":
            font = QFont(base_font)
            font.setPointSize(cls.FONT_SIZES["small"])
            return font
        else:
            return base_font
    
    @classmethod
    def apply_font_fixes(cls):
        """Apply platform-specific font fixes"""
        if sys.platform == "win32":
            # Windows-specific fixes
            import os
            # Disable font warnings
            os.environ['QT_LOGGING_RULES'] = 'qt.text.font.db=false'
            
            # Try to set better font rendering
            try:
                from PyQt6.QtCore import Qt
                QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
                QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            except:
                pass