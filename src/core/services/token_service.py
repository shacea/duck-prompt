
import os
import threading
from typing import Optional, Dict, Any, List, Union # Union 추가
import tiktoken
import mimetypes # 추가
import base64 # 추가
import logging # 로깅 추가

# --- Optional Imports for API Calls ---
try:
    import google.generativeai as genai # genai 임포트 추가
    # types 모듈을 직접 사용하는 대신, SDK가 처리하도록 유도
    from google.generativeai.types import ContentDict, PartDict # 필요한 경우 구체적인 타입 힌트 사용 가능
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
        self.settings: 'ConfigSettings' = config_service.get_settings()
        self.anthropic_client: Optional[anthropic.Anthropic] = None
        self.gemini_configured = False
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
                print("Warning: gemini_api_key not set in config.yml. Gemini token calculation might fail if other auth methods (e.g., ADC) are not configured.")
                self.gemini_configured = False
        except Exception as e:
            print(f"Error configuring Google Generative AI SDK: {e}")
            self.gemini_configured = False

    def _init_anthropic(self):
        """Initializes Anthropic client if available and API key is in config.yml."""
        if not _ANTHROPIC_AVAILABLE: return
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

    def calculate_tokens(
        self,
        model_type: str,
        model_name: str,
        text: str,
        attachments: Optional[List[Dict[str, Any]]] = None # 첨부 파일 목록 추가
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
        attachments = attachments or [] # 기본값 빈 리스트

        if model_type == "GPT":
            # GPT (tiktoken)는 현재 텍스트만 지원
            if attachments:
                print("Warning: GPT token calculation currently only supports text. Attachments ignored.")
            return self._calculate_gpt_tokens(text)
        elif model_type == "Claude":
            # Claude API는 멀티모달 메시지 토큰 계산 지원 가능성 있음 (확인 필요)
            # 현재 구현은 텍스트만 계산
            if attachments:
                 print("Warning: Claude token calculation currently only supports text. Attachments ignored.")
            return self._calculate_claude_tokens(model_name, text)
        elif model_type == "Gemini":
            # Gemini는 멀티모달 토큰 계산 시도
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
            print("Claude token calculation skipped: Anthropic SDK not available or API key missing.")
            return None
        if not model_name:
            print("Claude token calculation skipped: Model name is required.")
            return None
        if not text: return 0

        try:
            # 현재는 텍스트 메시지만 계산
            messages = [{"role": "user", "content": text}]
            # TODO: Anthropic SDK가 멀티모달 count_tokens를 지원하는지 확인하고 구현 필요
            count_response = self.anthropic_client.messages.count_tokens(
                model=model_name,
                messages=messages
            )
            token_count = count_response.input_tokens
            print(f"Claude API token count (text only): {token_count}")
            return token_count
        except Exception as e:
            print(f"Error calculating Claude tokens via API: {str(e)}")
            return None

    def _calculate_gemini_tokens(
        self,
        model_name: str,
        text: str,
        attachments: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Calculates tokens using the google-generativeai SDK (multimodal).
           Passes contents directly to the SDK, letting it handle Part creation.
        """
        if not _GOOGLE_GENAI_AVAILABLE:
            print("Gemini token calculation skipped: google-generativeai SDK not available.")
            return None
        if not self.gemini_configured:
             print("Gemini token calculation skipped: Gemini API key not configured.")
             return None
        if not model_name:
            print("Gemini token calculation skipped: Model name is required.")
            return None

        # --- Contents 구성 (텍스트와 파일/이미지 딕셔너리를 리스트에 직접 포함) ---
        # types.Part 를 직접 생성하지 않음
        contents_list: List[Union[str, Dict[str, Any]]] = [] # 타입 힌트 변경
        effective_model_name = "" # Initialize outside try block
        try:
            if text:
                # 텍스트는 문자열 그대로 추가
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
                    if not item_data: continue # 데이터 없으면 건너뜀

                    mime_type = None
                    if item_type == 'image':
                        # 이미지 MIME 타입 추정
                        if item_name.lower().endswith('.png'): mime_type = 'image/png'
                        elif item_name.lower().endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                        elif item_name.lower().endswith('.webp'): mime_type = 'image/webp'
                        else: mime_type = 'application/octet-stream' # 기본값 또는 더 정확한 추정 필요
                        # Part 대신 딕셔너리 형태로 추가
                        contents_list.append({"mime_type": mime_type, "data": item_data})
                    elif item_type == 'file':
                        # 파일 MIME 타입 추정
                        mime_type, _ = mimetypes.guess_type(item_name)
                        if not mime_type: mime_type = 'application/octet-stream'
                        # Part 대신 딕셔너리 형태로 추가
                        contents_list.append({"mime_type": mime_type, "data": item_data})
                    # else: 알 수 없는 타입은 무시

            if not contents_list:
                print("Token calculation skipped: No content (text or attachments) provided.")
                return 0 # 내용 없으면 0 토큰

            effective_model_name = model_name.replace("models/", "")
            print(f"Instantiating genai.GenerativeModel for token count: {effective_model_name}")
            # 모델 인스턴스 생성은 여전히 필요
            # 참고: genai.GenerativeModel(...) 자체가 API 호출이 아님
            model = genai.GenerativeModel(effective_model_name)

            print(f"Calling model.count_tokens for model: {effective_model_name} with {len(contents_list)} content parts (SDK handles conversion)")
            # *** FIX: Pass the list of strings and dictionaries directly to count_tokens ***
            # SDK가 내부적으로 Part 객체로 변환할 것을 기대함
            response = model.count_tokens(contents=contents_list)

            token_count = response.total_tokens
            print(f"Gemini API token count (multimodal): {token_count}")
            return token_count

        except AttributeError as e:
             # 이 오류는 이제 발생하지 않을 것으로 예상되지만, 방어적으로 남겨둠
             # 메시지는 일반적인 AttributeError로 변경
             log_message = (
                 f"AttributeError during Gemini token calculation: {e}. "
                 f"This might indicate an issue with the SDK version or the way content is structured. "
                 f"Please check the google-generativeai library and usage."
             )
             logger.error(log_message, exc_info=True) # Log with traceback
             print(f"Gemini token calculation failed due to AttributeError: {e}")
             return None
        except google_api_exceptions.PermissionDenied as e:
             print(f"Gemini API permission error during token count: {e}")
             return None
        except google_api_exceptions.InvalidArgument as e:
             # 잘못된 인수 오류는 여전히 발생 가능 (예: 지원되지 않는 MIME 타입)
             print(f"Gemini API invalid argument error during token count: {e}")
             print(f"Hint: Check if model '{effective_model_name}' supports multimodal count_tokens or the provided content types/structure.")
             return None
        except Exception as e:
            # 예상치 못한 다른 오류 처리
            print(f"Error calculating Gemini tokens via API: {str(e)}")
            logger.error(f"Unexpected error calculating Gemini tokens: {e}", exc_info=True)
            return None

# Preload default encoding on module import
_get_encoding()
            