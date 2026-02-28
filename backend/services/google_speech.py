"""
Google Cloud Speech-to-Text and Text-to-Speech service wrapper
"""
from google.cloud import speech_v1
from google.cloud import texttospeech_v1
import os
from typing import Optional
import io

class GoogleSpeechService:
    """Service for Google Cloud Speech-to-Text and Text-to-Speech"""

    def __init__(self):
        """Initialize Google Cloud clients"""
        # Clients will use GOOGLE_APPLICATION_CREDENTIALS env var
        self.speech_client = speech_v1.SpeechClient()
        self.tts_client = texttospeech_v1.TextToSpeechClient()

    def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: str = "en-US",
        sample_rate_hertz: int = 48000,
        encoding: speech_v1.RecognitionConfig.AudioEncoding = speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS
    ) -> dict:
        """
        Transcribe audio to text using Google Speech-to-Text

        Args:
            audio_content: Audio file bytes
            language_code: Language code (e.g., 'en-US', 'de-DE')
            sample_rate_hertz: Sample rate of audio
            encoding: Audio encoding format

        Returns:
            dict with 'text', 'confidence', and 'language' keys
        """
        try:
            # Configure recognition
            config = speech_v1.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="default",  # Use 'command_and_search' for short queries
            )

            audio = speech_v1.RecognitionAudio(content=audio_content)

            # Perform recognition
            response = self.speech_client.recognize(config=config, audio=audio)

            # Extract results
            if response.results:
                result = response.results[0]
                if result.alternatives:
                    alternative = result.alternatives[0]
                    return {
                        "text": alternative.transcript,
                        "confidence": alternative.confidence if hasattr(alternative, 'confidence') else 0.0,
                        "language": language_code
                    }

            # No results
            return {
                "text": "",
                "confidence": 0.0,
                "language": language_code
            }

        except Exception as e:
            print(f"Speech recognition error: {e}")
            raise

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        speaking_rate: float = 0.85,  # Slower for accessibility and clarity
        pitch: float = 0.0
    ) -> bytes:
        """
        Convert text to speech using Google Text-to-Speech

        Args:
            text: Text to synthesize
            language_code: Language code (e.g., 'en-US', 'de-DE')
            voice_name: Specific voice name (optional, auto-selects if None)
            speaking_rate: Speech rate (0.25 to 4.0, default 1.0)
            pitch: Voice pitch (-20.0 to 20.0, default 0.0)

        Returns:
            Audio content as bytes (MP3 format)
        """
        try:
            # Build synthesis input
            synthesis_input = texttospeech_v1.SynthesisInput(text=text)

            # Select voice
            if voice_name:
                voice = texttospeech_v1.VoiceSelectionParams(
                    name=voice_name,
                    language_code=language_code
                )
            else:
                # Auto-select Neural2 voice for better quality
                # For English: use Neural2-F (warm female voice)
                # For German: use Neural2-A (female voice)
                if language_code.startswith("en"):
                    default_voice = "en-US-Journey-F"   # Gemini-powered Journey voice
                elif language_code.startswith("de"):
                    default_voice = "de-DE-Neural2-A"
                else:
                    default_voice = None

                if default_voice:
                    voice = texttospeech_v1.VoiceSelectionParams(
                        name=default_voice,
                        language_code=language_code
                    )
                else:
                    voice = texttospeech_v1.VoiceSelectionParams(
                        language_code=language_code,
                        ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
                    )

            # Configure audio
            audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )

            # Perform synthesis
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            return response.audio_content

        except Exception as e:
            print(f"Speech synthesis error: {e}")
            raise

    def get_available_voices(self, language_code: Optional[str] = None) -> list:
        """
        Get list of available voices

        Args:
            language_code: Filter by language code (optional)

        Returns:
            List of voice dictionaries
        """
        try:
            response = self.tts_client.list_voices(language_code=language_code)

            voices = []
            for voice in response.voices:
                voices.append({
                    "name": voice.name,
                    "language_codes": voice.language_codes,
                    "gender": texttospeech_v1.SsmlVoiceGender(voice.ssml_gender).name
                })

            return voices

        except Exception as e:
            print(f"Error getting voices: {e}")
            raise


# Singleton instance
_speech_service = None

def get_speech_service() -> GoogleSpeechService:
    """Get or create GoogleSpeechService singleton"""
    global _speech_service
    if _speech_service is None:
        _speech_service = GoogleSpeechService()
    return _speech_service
