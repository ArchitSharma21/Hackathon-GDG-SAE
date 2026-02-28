from fastapi import APIRouter, HTTPException, Path, Query
from backend.services.lufthansa import get_lufthansa_client
from typing import Optional

router = APIRouter()

@router.get("/{flight_number}")
async def get_flight_status(
    flight_number: str = Path(..., description="Flight number (e.g., LH123)"),
    date: Optional[str] = Query(None, description="Flight date (YYYY-MM-DD)"),
    use_mock: bool = Query(False, description="Use mock data for demo")
):
    """
    Get flight status from Lufthansa API
    Returns gate, time, and status information
    """
    try:
        lufthansa = get_lufthansa_client()

        # Use mock data if requested or if credentials not configured
        if use_mock or not lufthansa.client_id:
            flight_data = await lufthansa.get_mock_flight(flight_number)
        else:
            flight_data = await lufthansa.get_flight_status(flight_number, date)

            # Fallback to mock if API fails
            if not flight_data:
                flight_data = await lufthansa.get_mock_flight(flight_number)

        return flight_data

    except Exception as e:
        print(f"Flight status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_my_flight():
    """
    Get current user's flight information
    (In production, this would be based on user's boarding pass/profile)
    For demo, returns a default flight
    """
    try:
        # For demo, return default flight LH123
        lufthansa = get_lufthansa_client()
        flight_data = await lufthansa.get_mock_flight("LH123")

        return flight_data

    except Exception as e:
        print(f"Get my flight error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
