
from pydantic import BaseModel, Field
from typing import List, Optional

class AppState(BaseModel):
    """
    Represents the application state.
    """
    mode: str = "Code Enhancer Prompt Builder"
    project_folder: Optional[str] = None
    system_prompt: str = ""
    user_prompt: str = ""
    checked_files: List[str] = Field(default_factory=list)
    selected_llm: str = "Gemini" # Default LLM for token calculation
    selected_model_name: str = "" # Specific model name, loaded from config initially

    # Gemini 파라미터는 config.yml에서 관리하므로 AppState에서 제거
    # gemini_temperature: float = 0.0
    # gemini_enable_thinking: bool = True
    # gemini_thinking_budget: int = 24576
    # gemini_enable_search: bool = True

    class Config:
        validate_assignment = True
