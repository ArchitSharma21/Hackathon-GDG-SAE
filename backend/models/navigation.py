from pydantic import BaseModel
from typing import List, Optional

class NavigationStep(BaseModel):
    step_number: int
    instruction: str
    distance: float
    duration: int  # in seconds
    from_location: str
    to_location: str

class NavigationRoute(BaseModel):
    from_location: str
    to_location: str
    total_distance: float
    total_duration: int  # in seconds
    steps: List[NavigationStep]
    current_step: int = 0

class NavigationRequest(BaseModel):
    from_location: str
    to_location: str
    current_position: Optional[str] = None

class VoiceQuery(BaseModel):
    query: str
    language: str = "en-US"

class SpeechRequest(BaseModel):
    text: str
    language: str = "en-US"
    audio_format: str = "mp3"
