from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routers
from backend.routers import speech, navigation, flights, emergency

app = FastAPI(
    title="Airport Navigation Assistant API",
    description="Voice-driven navigation system for visually impaired travelers",
    version="1.0.0"
)

# CORS middleware for PWA frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(speech.router, prefix="/api/speech", tags=["speech"])
app.include_router(navigation.router, prefix="/api", tags=["navigation"])
app.include_router(flights.router, prefix="/api/flights", tags=["flights"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["emergency"])

# Mount static files for frontend
# Get the path relative to the project root
import pathlib
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Airport Navigation Assistant",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
