from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
from backend.models.navigation import SpeechRequest
from backend.services.google_speech import get_speech_service
from google.cloud import speech_v1
import os

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Query("en-US", description="Language code (e.g., en-US, de-DE)")
):
    """
    Convert speech to text using Google Cloud Speech-to-Text
    Accepts audio file and returns transcribed text
    """
    try:
        # Read audio content
        audio_content = await audio.read()

        # Get speech service
        speech_service = get_speech_service()

        # Determine encoding based on file type
        encoding = speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS
        sample_rate = 48000

        if audio.content_type:
            if 'wav' in audio.content_type.lower():
                encoding = speech_v1.RecognitionConfig.AudioEncoding.LINEAR16
                sample_rate = 16000
            elif 'ogg' in audio.content_type.lower():
                encoding = speech_v1.RecognitionConfig.AudioEncoding.OGG_OPUS
            elif 'flac' in audio.content_type.lower():
                encoding = speech_v1.RecognitionConfig.AudioEncoding.FLAC

        # Transcribe
        result = speech_service.transcribe_audio(
            audio_content=audio_content,
            language_code=language,
            sample_rate_hertz=sample_rate,
            encoding=encoding
        )

        return result

    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_speech(request: SpeechRequest):
    """
    Convert text to speech using Google Cloud Text-to-Speech
    Returns audio file (MP3)
    """
    try:
        # Get speech service
        speech_service = get_speech_service()

        # Synthesize speech
        audio_content = speech_service.synthesize_speech(
            text=request.text,
            language_code=request.language,
            speaking_rate=0.9  # Slightly slower for accessibility
        )

        # Return audio response
        return Response(
            content=audio_content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )

    except Exception as e:
        print(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@router.get("/voices")
async def get_voices(language: str = Query(None, description="Filter by language code")):
    """
    Get available TTS voices
    """
    try:
        speech_service = get_speech_service()
        voices = speech_service.get_available_voices(language_code=language)
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
