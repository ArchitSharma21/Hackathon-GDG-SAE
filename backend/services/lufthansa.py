"""
Lufthansa OpenAPI client for flight information
"""
import httpx
import os
from typing import Optional, Dict
from datetime import datetime, timedelta

class LufthansaAPIClient:
    """Client for Lufthansa OpenAPI"""

    BASE_URL = "https://api.lufthansa.com/v1"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize Lufthansa API client

        Args:
            client_id: OAuth client ID (from env if not provided)
            client_secret: OAuth client secret (from env if not provided)
        """
        self.client_id = client_id or os.getenv("LUFTHANSA_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LUFTHANSA_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            print("Warning: Lufthansa API credentials not configured")

        self.access_token = None
        self.token_expires_at = None

    async def _get_access_token(self) -> str:
        """
        Get or refresh OAuth access token

        Returns:
            Access token string
        """
        # Check if token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        # Request new token
        token_url = f"{self.BASE_URL}/oauth/token"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            response.raise_for_status()
            data = response.json()

            self.access_token = data["access_token"]
            # Set expiration time (with 5 min buffer)
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            return self.access_token

    async def get_flight_status(
        self,
        flight_number: str,
        date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get flight status information

        Args:
            flight_number: Flight number (e.g., "LH400")
            date: Flight date in YYYY-MM-DD format (defaults to today)

        Returns:
            Flight information dict or None if not found
        """
        try:
            # Get access token
            token = await self._get_access_token()

            # Default to today's date
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            # Make API request
            url = f"{self.BASE_URL}/operations/flightstatus/{flight_number}/{date}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json"
                    }
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()

                # Parse response
                if "FlightStatusResource" in data:
                    flights = data["FlightStatusResource"].get("Flights", {}).get("Flight", [])
                    if flights:
                        flight = flights[0] if isinstance(flights, list) else flights
                        return self._parse_flight_data(flight)

                return None

        except Exception as e:
            print(f"Lufthansa API error: {e}")
            return None

    def _parse_flight_data(self, flight_data: Dict) -> Dict:
        """
        Parse Lufthansa API flight data into our format

        Args:
            flight_data: Raw flight data from API

        Returns:
            Normalized flight information dict
        """
        departure = flight_data.get("Departure", {})
        arrival = flight_data.get("Arrival", {})

        # Extract gate information
        departure_gate = None
        if "AirportCode" in departure:
            departure_gate = departure.get("Terminal", {}).get("Gate")

        # Extract status
        status_code = flight_data.get("FlightStatus", {}).get("Code", "")
        status_map = {
            "CD": "Cancelled",
            "DP": "Departed",
            "LD": "Landed",
            "RT": "Rerouted",
            "": "Scheduled"
        }
        status = status_map.get(status_code, "Unknown")

        # Extract times
        scheduled_departure = departure.get("ScheduledTimeLocal", {}).get("DateTime", "")
        estimated_departure = departure.get("EstimatedTimeLocal", {}).get("DateTime", "")

        # Format time
        departure_time = self._format_time(scheduled_departure or estimated_departure)

        return {
            "flight_number": flight_data.get("MarketingCarrier", {}).get("FlightNumber", ""),
            "airline": flight_data.get("MarketingCarrier", {}).get("AirlineID", "LH"),
            "status": status,
            "gate": departure_gate or "TBD",
            "departure_time": departure_time,
            "departure_airport": departure.get("AirportCode", ""),
            "arrival_airport": arrival.get("AirportCode", ""),
            "terminal": departure.get("Terminal", {}).get("Name", "1"),
            "scheduled_time": scheduled_departure,
            "estimated_time": estimated_departure
        }

    def _format_time(self, iso_datetime: str) -> str:
        """Format ISO datetime to readable time"""
        if not iso_datetime:
            return "TBD"

        try:
            dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return iso_datetime

    async def get_mock_flight(self, flight_number: str) -> Dict:
        """
        Get mock flight data for demo purposes
        (Used when API credentials are not configured)

        Args:
            flight_number: Flight number

        Returns:
            Mock flight information
        """
        # Mock data for common Lufthansa flights from Hamburg
        mock_flights = {
            "LH123": {
                "flight_number": "LH123",
                "airline": "LH",
                "status": "On Time",
                "gate": "B12",
                "departure_time": "14:30",
                "departure_airport": "HAM",
                "arrival_airport": "FRA",
                "terminal": "1"
            },
            "LH456": {
                "flight_number": "LH456",
                "airline": "LH",
                "status": "Boarding",
                "gate": "A5",
                "departure_time": "16:45",
                "departure_airport": "HAM",
                "arrival_airport": "MUC",
                "terminal": "1"
            },
            "LH789": {
                "flight_number": "LH789",
                "airline": "LH",
                "status": "Delayed",
                "gate": "B20",
                "departure_time": "18:00",
                "departure_airport": "HAM",
                "arrival_airport": "FRA",
                "terminal": "1"
            }
        }

        # Extract numeric part if full flight number provided (e.g., "LH123" -> "123")
        flight_key = flight_number.upper()

        return mock_flights.get(
            flight_key,
            {
                "flight_number": flight_number,
                "airline": "LH",
                "status": "Scheduled",
                "gate": "B15",
                "departure_time": "15:00",
                "departure_airport": "HAM",
                "arrival_airport": "FRA",
                "terminal": "1"
            }
        )


# Singleton instance
_lufthansa_client = None

def get_lufthansa_client() -> LufthansaAPIClient:
    """Get or create LufthansaAPIClient singleton"""
    global _lufthansa_client
    if _lufthansa_client is None:
        _lufthansa_client = LufthansaAPIClient()
    return _lufthansa_client
