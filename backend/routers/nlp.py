"""
Natural Language Processing router
Uses Gemini AI to understand navigation queries
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.gemini_nlp import get_gemini_service

router = APIRouter()


class NLPRequest(BaseModel):
    query: str
    context: dict = {}

class NLPResponse(BaseModel):
    intent: str
    location_type: str
    location_id: Optional[str] = None
    urgency: str
    context: str
    search_query: str
    original_query: str


@router.post("/understand", response_model=NLPResponse)
async def understand_query(request: NLPRequest):
    """
    Process natural language query using Gemini AI

    Examples:
    - "I need to use the restroom urgently"
    - "Where is gate B12?"
    - "I'm hungry, where can I eat?"
    - "Help! I need assistance"
    """
    try:
        gemini_service = get_gemini_service()

        result = gemini_service.understand_navigation_query(
            user_query=request.query,
            available_locations=request.context.get('available_locations')
        )

        # Add original query to response
        result['original_query'] = request.query

        return result

    except ValueError as e:
        # API key not configured
        raise HTTPException(
            status_code=503,
            detail=f"Gemini AI not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )
