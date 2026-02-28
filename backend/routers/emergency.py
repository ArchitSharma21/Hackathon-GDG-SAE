from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.location_search import get_location_service
from backend.services.pathfinding import get_pathfinding_service

router = APIRouter()

class EmergencyRequest(BaseModel):
    current_location: str
    emergency_type: str = "help"

@router.post("/help")
async def request_emergency_help(request: EmergencyRequest):
    """
    Trigger emergency help request
    Returns nearest information desk location and navigation
    """
    try:
        location_service = get_location_service()
        pathfinding_service = get_pathfinding_service()

        # Find nearest help location (info desk)
        nearest_help = location_service.get_nearest_by_type(
            current_location=request.current_location,
            node_type="info"
        )

        if not nearest_help:
            return {
                "status": "error",
                "message": "No help desk found in airport map"
            }

        # Calculate route to help desk
        route = pathfinding_service.find_route(
            from_location=request.current_location,
            to_location=nearest_help.id
        )

        if not route:
            return {
                "status": "help_requested",
                "nearest_help": nearest_help.id,
                "nearest_help_name": nearest_help.name,
                "message": f"Help is available at {nearest_help.name}. Unable to calculate route."
            }

        # Calculate approximate distance and time
        total_distance = route.total_distance
        total_duration = route.total_duration

        message = (
            f"Emergency assistance requested. The nearest help desk is {nearest_help.name}, "
            f"approximately {int(total_distance)} meters away. "
            f"Estimated walking time: {int(total_duration / 60)} minutes. "
            f"Navigation is being started."
        )

        return {
            "status": "help_requested",
            "nearest_help": nearest_help.id,
            "nearest_help_name": nearest_help.name,
            "distance": total_distance,
            "duration": total_duration,
            "message": message,
            "route": route.model_dump()
        }

    except Exception as e:
        print(f"Emergency help error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
