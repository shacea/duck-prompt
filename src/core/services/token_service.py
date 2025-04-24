import os
import threading
from typing import Optional, Dict, Any
import tiktoken

# --- Optional Imports for API Calls ---
try:
    # Use the google-generativeai SDK
    import google.generativeai as genai
    from google.api_core import exceptions as google_api_exceptions # Import specific exceptions
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
# Import ConfigService type hint safely
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .config_service import ConfigService
    from core.pydantic_models.config_settings import ConfigSettings # Import settings model

# --- Tiktoken Encoding Cache ---
_enc_cache: Dict[str, tiktoken.Encoding] = {}
_enc_lock = threading.Lock()

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
                _enc_cache[encoding_name] = None # Mark as failed
        return _enc_cache[encoding_name]

# --- Token Calculation Service ---
class TokenCalculationService:
    """Handles token calculation for different LLM providers."""

    def __init__(self, config_service: 'ConfigService'):
        """
        Initializes the service.

        Args:
            config_service: The application's configuration service instance.
        """
        self.config_service = config_service
        self.settings: 'ConfigSettings' = config_service.get_settings() # Type hint settings
        self.anthropic_client: Optional[anthropic.Anthropic] = None # Initialize client instance variable
        self.gemini_configured = False # Track Gemini API configuration status

        # Initialize API clients if available and configured
        self._init_gemini()
        self._init_anthropic()

    def _init_gemini(self):
        """Initializes the google-generativeai SDK if available and configured."""
        if not _GOOGLE_GENAI_AVAILABLE:
            self.gemini_configured = False
            return

        try:
            api_key = self.settings.gemini_api_key
            if api_key:
                genai.configure(api_key=api_key)
                print("Google Generative AI SDK configured using API key from config.yml.")
                self.gemini_configured = True
            else:
                # The google-generativeai library might implicitly use ADC or other methods
                # if available, but explicit configuration is preferred for clarity.
                print("Warning: gemini_api_key not set in config.yml. Gemini token calculation might fail if other auth methods (e.g., ADC) are not configured.")
                # We'll assume it's not configured if the key is missing.
                self.gemini_configured = False
        except Exception as e:
            print(f"Error configuring Google Generative AI SDK: {e}")
            self.gemini_configured = False


    def _init_anthropic(self):
        """Initializes Anthropic client if available and API key is in config.yml."""
        if not _ANTHROPIC_AVAILABLE:
            return
        try:
            api_key = self.settings.anthropic_api_key
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                print("Anthropic client initialized using API key from config.yml.")
            else:
                self.anthropic_client = None
                print("Warning: anthropic_api_key not set in config.yml. Claude token calculation via API disabled.")
        except Exception as e:
            self.anthropic_client = None
            print(f"Error initializing Anthropic client: {e}")

    def calculate_tokens(self, model_type: str, model_name: str, text: str) -> Optional[int]:
        """
        Calculates the number of tokens for the given text based on the model type and name.

        Args:
            model_type: "GPT", "Claude", or "Gemini".
            model_name: The specific model identifier (e.g., "gpt-4o", "claude-3-opus-20240229", "gemini-1.5-pro-latest").
            text: The input text to tokenize.

        Returns:
            The calculated token count, or None if calculation fails.
        """
        print(f"Calculating tokens for Model Type: {model_type}, Model Name: {model_name}")

        if model_type == "GPT":
            return self._calculate_gpt_tokens(text)
        elif model_type == "Claude":
            return self._calculate_claude_tokens(model_name, text)
        elif model_type == "Gemini":
            return self._calculate_gemini_tokens(model_name, text)
        else:
            print(f"Error: Unknown model type '{model_type}'")
            return None

    def _calculate_gpt_tokens(self, text: str) -> Optional[int]:
        """Calculates tokens using tiktoken (assuming o200k_base for newer models)."""
        enc = _get_encoding("o200k_base") # Use appropriate encoding
        if enc is None:
            print("Token calculation failed: Tiktoken encoding not available.")
            return None
        try:
            # Handle potential empty string edge case for encoding
            if not text:
                return 0
            return len(enc.encode(text))
        except Exception as e:
            print(f"Error calculating GPT tokens with tiktoken: {str(e)}")
            return None

    def _calculate_claude_tokens(self, model_name: str, text: str) -> Optional[int]:
        """Calculates tokens using the Anthropic API."""
        if not _ANTHROPIC_AVAILABLE or self.anthropic_client is None:
            print("Claude token calculation skipped: Anthropic SDK not available or API key missing in config.yml.")
            return None
        if not model_name:
            print("Claude token calculation skipped: Model name is required.")
            return None
        # Handle empty string before API call
        if not text:
            return 0

        try:
            # Use the correct API call: client.messages.count_tokens
            messages = [{"role": "user", "content": text}]
            count_response = self.anthropic_client.messages.count_tokens(
                model=model_name,
                messages=messages
            )

            # The response object directly has the input_tokens attribute
            token_count = count_response.input_tokens
            print(f"Claude API token count: {token_count}")
            return token_count

        except anthropic.APIConnectionError as e:
            print(f"Anthropic API connection error: {e}")
            return None
        except anthropic.RateLimitError as e:
            print(f"Anthropic API rate limit exceeded: {e}")
            return None
        except anthropic.AuthenticationError as e:
            print(f"Anthropic API authentication error (check API key in config.yml): {e}")
            return None
        except anthropic.APIStatusError as e:
            print(f"Anthropic API status error: {e.status_code} - {e.response}")
            return None
        except Exception as e:
            print(f"Error calculating Claude tokens via API: {str(e)}")
            return None

    def _calculate_gemini_tokens(self, model_name: str, text: str) -> Optional[int]:
        """Calculates tokens using the google-generativeai SDK."""
        if not _GOOGLE_GENAI_AVAILABLE:
            print("Gemini token calculation skipped: google-generativeai SDK not available.")
            return None
        if not self.gemini_configured:
             print("Gemini token calculation skipped: Gemini API key not configured in config.yml.")
             return None
        if not model_name:
            print("Gemini token calculation skipped: Model name is required.")
            return None
        # Handle empty string before API call
        if not text:
            return 0

        try:
            # Instantiate the model
            # The GenerativeModel constructor typically expects the model name without the "models/" prefix.
            # Example: "gemini-1.5-pro-latest"
            effective_model_name = model_name.replace("models/", "")
            print(f"Instantiating genai.GenerativeModel with model: {effective_model_name}")
            model = genai.GenerativeModel(effective_model_name)

            # Call the count_tokens method on the model instance
            print(f"Calling model.count_tokens for model: {effective_model_name}")
            response = model.count_tokens(contents=text) # Pass contents directly

            # Access total_tokens from the response object
            token_count = response.total_tokens
            print(f"Gemini API token count: {token_count}")
            return token_count
        # Catch specific exceptions from google-generativeai / google-api-core
        except google_api_exceptions.PermissionDenied as e:
             print(f"Gemini API permission error: {e}")
             print("Hint: Check if the Gemini API key in config.yml is correct and has permissions.")
             return None
        except google_api_exceptions.InvalidArgument as e:
             print(f"Gemini API invalid argument error: {e}")
             print(f"Hint: Check if the model name '{effective_model_name}' is valid for the API key and the count_tokens method.")
             return None
        except AttributeError as e:
             # Catch potential AttributeError if 'GenerativeModel' or 'count_tokens' is missing
             print(f"Error accessing Gemini SDK components: {e}")
             print("Hint: Ensure the 'google-generativeai' library is installed correctly and up-to-date.")
             return None
        except Exception as e:
            # Catch other potential errors
            print(f"Error calculating Gemini tokens via google-generativeai API: {str(e)}")
            return None

# Preload default encoding on module import
_get_encoding()
