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

    class Config:
        validate_assignment = True
