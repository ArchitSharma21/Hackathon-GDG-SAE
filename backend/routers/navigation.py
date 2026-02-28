from fastapi import APIRouter, HTTPException, Query
from backend.models.navigation import NavigationRequest, NavigationRoute
from backend.services.location_search import get_location_service
from typing import List

router = APIRouter()

@router.get("/locations/search")
async def search_locations(
    query: str = Query(..., description="Search query for location"),
    max_results: int = Query(5, description="Maximum number of results")
):
    """
    Search for locations in the airport by name or type
    Supports natural language queries like:
    - "bathroom"
    - "where is gate b12"
    - "find information desk"
    """
    try:
        location_service = get_location_service()
        results = location_service.search(query, max_results=max_results)

        return {
            "query": query,
            "results": [r.model_dump() for r in results],
            "count": len(results)
        }
    except Exception as e:
        print(f"Location search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/{location_id}")
async def get_location(location_id: str):
    """
    Get details of a specific location by ID
    """
    try:
        location_service = get_location_service()
        node = location_service.get_node_by_id(location_id)

        if not node:
            raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found")

        return node.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get location error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/type/{location_type}")
async def get_locations_by_type(location_type: str):
    """
    Get all locations of a specific type (bathroom, gate, entrance, etc.)
    """
    try:
        location_service = get_location_service()
        nodes = location_service.get_nodes_by_type(location_type)

        return {
            "type": location_type,
            "locations": [n.model_dump() for n in nodes],
            "count": len(nodes)
        }
    except Exception as e:
        print(f"Get locations by type error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigation/route")
async def get_navigation_route(request: NavigationRequest):
    """
    Get turn-by-turn navigation route from one location to another
    """
    try:
        from services.pathfinding import get_pathfinding_service

        pathfinding_service = get_pathfinding_service()

        # Find route
        route = pathfinding_service.find_route(
            from_location=request.from_location,
            to_location=request.to_location
        )

        if not route:
            raise HTTPException(
                status_code=404,
                detail=f"No route found from '{request.from_location}' to '{request.to_location}'"
            )

        return route.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Navigation route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
