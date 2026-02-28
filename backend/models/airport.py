from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict

class Coordinates(BaseModel):
    x: float
    y: float

class AirportNode(BaseModel):
    id: str
    name: str
    type: str  # entrance, exit, gate, bathroom, security, info, food/restaurant, stairs, baggage
    coordinates: Coordinates
    description: str
    terminal: Optional[str] = None
    floor: Optional[int] = None  # Floor number (1 for arrivals, 2 for departures)

class AirportPath(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(alias='from')
    to: str
    distance: float
    directions: str
    duration: int  # in seconds

class AirportMap(BaseModel):
    airport: str
    terminal: str
    nodes: List[AirportNode]
    paths: List[AirportPath]
    floors: Optional[int] = None  # Number of floors in the airport

class LocationSearchResult(BaseModel):
    id: str
    name: str
    type: str
    description: str
    confidence: float  # 0.0 to 1.0
