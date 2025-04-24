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

    class Config:
        validate_assignment = True
