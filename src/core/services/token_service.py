
import os
import threading
from typing import Optional, Dict, Any, List, Union
import tiktoken
import mimetypes
import base64
import logging

# --- Optional Imports for API Calls ---
try:
    import google.generativeai as genai
    from google.generativeai.types import ContentDict, PartDict
    from google.api_core import exceptions as google_api_exceptions
    _GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    _GOOGLE_GENAI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Gemini token calculation via API disabled.")

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic not installed. Claude token calculation via API disabled.")

# --- Service Dependencies ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .config_service import ConfigService
    from core.pydantic_models.config_settings import ConfigSettings

# --- Tiktoken Encoding Cache ---
_enc_cache: Dict[str, tiktoken.Encoding] = {}
_enc_lock = threading.Lock()

# 로거 설정
logger = logging.getLogger(__name__)


def _get_encoding(encoding_name: str = "o200k_base") -> Optional[tiktoken.Encoding]:
    """Gets or loads a tiktoken encoding."""
    with _enc_lock:
        if encoding_name not in _enc_cache:
            try:
                print(f"Loading tiktoken encoding: {encoding_name}...")
                _enc_cache[encoding_name] = tiktoken.get_encoding(encoding_name)
                print(f"Tiktoken encoding '{encoding_name}' loaded.")
            except Exception as e:
                print(f"Error loading tiktoken encoding '{encoding_name}': {e}")
                _enc_cache[encoding_name] = None
        return _enc_cache[encoding_name]

# --- Token Calculation Service ---
class TokenCalculationService:
    """Handles token calculation for different LLM providers."""

    def __init__(self, config_service: 'ConfigService'):
        """Initializes the service."""
        self.config_service = config_service
        # Settings are now fetched when needed via config_service.get_settings()
        self.anthropic_client: Optional[anthropic.Anthropic] = None
        self.gemini_configured = False
        self._init_clients() # Combined initialization

    def _get_settings(self) -> 'ConfigSettings':
        """Helper to get current settings."""
        return self.config_service.get_settings()

    def _init_clients(self):
        """Initializes API clients based on keys found in config settings."""
        settings = self._get_settings()

        # Initialize Gemini
        if _GOOGLE_GENAI_AVAILABLE:
            api_key = settings.gemini_api_key
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    print("Google Generative AI SDK configured using API key from DB.")
                    self.gemini_configured = True
                except Exception as e:
                    print(f"Error configuring Google Generative AI SDK: {e}")
                    self.gemini_configured = False
            else:
                print("Warning: Gemini API key not found in DB config. Gemini token calculation might fail.")
                self.gemini_configured = False
        else:
             self.gemini_configured = False

        # Initialize Anthropic
        if _ANTHROPIC_AVAILABLE:
            api_key = settings.anthropic_api_key
            if api_key:
                try:
                    self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                    print("Anthropic client initialized using API key from DB.")
                except Exception as e:
                    self.anthropic_client = None
                    print(f"Error initializing Anthropic client: {e}")
            else:
                self.anthropic_client = None
                print("Warning: Anthropic API key not found in DB config. Claude token calculation via API disabled.")
        else:
            self.anthropic_client = None


    def calculate_tokens(
        self,
        model_type: str,
        model_name: str,
        text: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[int]:
        """
        Calculates the number of tokens for the given text and attachments
        based on the model type and name.

        Args:
            model_type: "GPT", "Claude", or "Gemini".
            model_name: The specific model identifier.
            text: The input text to tokenize.
            attachments: List of attached items (dicts with 'type', 'name', 'data'/'path').

        Returns:
            The calculated token count, or None if calculation fails.
        """
        print(f"Calculating tokens for Model Type: {model_type}, Model Name: {model_name}")
        attachments = attachments or []

        # Re-initialize clients in case API keys changed in DB (though config is loaded once now)
        # self._init_clients() # Might be redundant if config is loaded once

        if model_type == "GPT":
            if attachments:
                print("Warning: GPT token calculation currently only supports text. Attachments ignored.")
            return self._calculate_gpt_tokens(text)
        elif model_type == "Claude":
            if attachments:
                 print("Warning: Claude token calculation currently only supports text. Attachments ignored.")
            return self._calculate_claude_tokens(model_name, text)
        elif model_type == "Gemini":
            return self._calculate_gemini_tokens(model_name, text, attachments)
        else:
            print(f"Error: Unknown model type '{model_type}'")
            return None

    def _calculate_gpt_tokens(self, text: str) -> Optional[int]:
        """Calculates tokens using tiktoken (assuming o200k_base for newer models)."""
        enc = _get_encoding("o200k_base")
        if enc is None:
            print("Token calculation failed: Tiktoken encoding not available.")
            return None
        try:
            if not text: return 0
            return len(enc.encode(text))
        except Exception as e:
            print(f"Error calculating GPT tokens with tiktoken: {str(e)}")
            return None

    def _calculate_claude_tokens(self, model_name: str, text: str) -> Optional[int]:
        """Calculates tokens using the Anthropic API (currently text only)."""
        if not _ANTHROPIC_AVAILABLE or self.anthropic_client is None:
            print("Claude token calculation skipped: Anthropic SDK not available or API key missing/invalid.")
            return None
        if not model_name:
            print("Claude token calculation skipped: Model name is required.")
            return None
        if not text: return 0

        try:
            messages = [{"role": "user", "content": text}]
            count_response = self.anthropic_client.messages.count_tokens(
                model=model_name,
                messages=messages
            )
            token_count = count_response.input_tokens
            print(f"Claude API token count (text only): {token_count}")
            return token_count
        except anthropic.APIConnectionError as e:
             print(f"Claude API connection error during token count: {e}")
             return None
        except anthropic.AuthenticationError as e:
             print(f"Claude API authentication error (check API key): {e}")
             return None
        except anthropic.RateLimitError as e:
             print(f"Claude API rate limit exceeded during token count: {e}")
             return None
        except Exception as e:
            print(f"Error calculating Claude tokens via API: {str(e)}")
            return None

    def _calculate_gemini_tokens(
        self,
        model_name: str,
        text: str,
        attachments: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Calculates tokens using the google-generativeai SDK (multimodal)."""
        if not _GOOGLE_GENAI_AVAILABLE:
            print("Gemini token calculation skipped: google-generativeai SDK not available.")
            return None
        if not self.gemini_configured:
             print("Gemini token calculation skipped: Gemini API key not configured or invalid.")
             return None
        if not model_name:
            print("Gemini token calculation skipped: Model name is required.")
            return None

        contents_list: List[Union[str, Dict[str, Any]]] = []
        effective_model_name = ""
        try:
            if text:
                contents_list.append(text)

            if attachments:
                for attachment in attachments:
                    item_type = attachment.get('type')
                    item_name = attachment.get('name', 'unknown')
                    item_data = attachment.get('data')
                    item_path = attachment.get('path')

                    if not item_data and item_path and os.path.exists(item_path):
                        try:
                            with open(item_path, 'rb') as f: item_data = f.read()
                        except Exception as e:
                            logger.error(f"Token Calc: Failed to read attachment {item_path}: {e}")
                            continue
                    if not item_data: continue

                    mime_type = None
                    if item_type == 'image':
                        if item_name.lower().endswith('.png'): mime_type = 'image/png'
                        elif item_name.lower().endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                        elif item_name.lower().endswith('.webp'): mime_type = 'image/webp'
                        else: mime_type = 'application/octet-stream'
                        contents_list.append({"mime_type": mime_type, "data": item_data})
                    elif item_type == 'file':
                        mime_type, _ = mimetypes.guess_type(item_name)
                        if not mime_type: mime_type = 'application/octet-stream'
                        contents_list.append({"mime_type": mime_type, "data": item_data})

            if not contents_list:
                print("Token calculation skipped: No content (text or attachments) provided.")
                return 0

            effective_model_name = model_name.replace("models/", "")
            print(f"Instantiating genai.GenerativeModel for token count: {effective_model_name}")
            model = genai.GenerativeModel(effective_model_name)

            print(f"Calling model.count_tokens for model: {effective_model_name} with {len(contents_list)} content parts")
            response = model.count_tokens(contents=contents_list)

            token_count = response.total_tokens
            print(f"Gemini API token count (multimodal): {token_count}")
            return token_count

        except AttributeError as e:
             log_message = (
                 f"AttributeError during Gemini token calculation: {e}. "
                 f"Check SDK version and content structure."
             )
             logger.error(log_message, exc_info=True)
             print(f"Gemini token calculation failed due to AttributeError: {e}")
             return None
        except google_api_exceptions.PermissionDenied as e:
             print(f"Gemini API permission error during token count (check API key): {e}")
             # Invalidate configuration if key is bad?
             # self.gemini_configured = False
             return None
        except google_api_exceptions.InvalidArgument as e:
             print(f"Gemini API invalid argument error during token count: {e}")
             print(f"Hint: Check if model '{effective_model_name}' supports multimodal count_tokens or the provided content types/structure.")
             return None
        except google_api_exceptions.ResourceExhausted as e:
             print(f"Gemini API rate limit likely exceeded during token count: {e}")
             return None
        except Exception as e:
            print(f"Error calculating Gemini tokens via API: {str(e)}")
            logger.error(f"Unexpected error calculating Gemini tokens: {e}", exc_info=True)
            return None

# Preload default encoding on module import
_get_encoding()
