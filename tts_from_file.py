#!/usr/bin/env python3
"""
Read text from a file -> Gemini TTS -> save WAV.

Usage examples:
  python tts_from_file.py --in transcript.txt --out out.wav --voice Kore
  python tts_from_file.py --in german.txt --out de.wav --voice Achird
  python tts_from_file.py --in script.txt --out podcast.wav --style "Warm, slow, audiobook style"
"""

from __future__ import annotations

import argparse
import os
import sys
import wave
from typing import Optional

from dotenv import load_dotenv

from google import genai
from google.genai import types


load_dotenv()

# Get variables
api_key = os.getenv("GEMINI_API_KEY")

VOICE_CHOICES = [
    # From Gemini TTS docs (30 voices). :contentReference[oaicite:5]{index=5}
    "Zephyr","Puck","Charon","Kore","Fenrir","Leda","Orus","Aoede","Callirrhoe","Autonoe",
    "Enceladus","Iapetus","Umbriel","Algieba","Despina","Erinome","Algenib","Rasalgethi","Laomedeia",
    "Achernar","Alnilam","Schedar","Gacrux","Pulcherrima","Achird","Zubenelgenubi","Vindemiatrix",
    "Sadachbia","Sadaltager","Sulafat"
]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_wave_file(filename: str, pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
    """
    Gemini TTS example writes PCM to a wave container similarly. :contentReference[oaicite:6]{index=6}
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def synthesize_tts(
    text: str,
    api_key: str,
    model: str,
    voice_name: str,
    style_hint: Optional[str],
) -> bytes:
    client = genai.Client(api_key=api_key)

    # TTS models detect input language automatically. :contentReference[oaicite:7]{index=7}
    prompt = text
    if style_hint:
        prompt = f"{style_hint.strip()}:\n\n{text}"

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
        ),
    )

    # Audio PCM bytes live in inline_data.data in the first candidate part. :contentReference[oaicite:8]{index=8}
    return response.candidates[0].content.parts[0].inline_data.data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_path", required=True, help="Input text file.")
    p.add_argument("--out", dest="out_path", default="out.wav", help="Output WAV path.")
    p.add_argument("--voice", type=str, default="Kore", choices=VOICE_CHOICES, help="Prebuilt voice name.")
    p.add_argument("--style", type=str, default=None, help="Optional style/director hint (e.g., 'Say warmly, slowly').")
    p.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash-preview-tts",
        help="Gemini TTS model.",
    )
    p.add_argument(
        "--api_key",
        type=str,
        default=os.getenv("GEMINI_API_KEY", ""),
        help="Gemini API key (or set GEMINI_API_KEY env var).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        print("ERROR: Provide --api_key or set GEMINI_API_KEY.", file=sys.stderr)
        sys.exit(1)

    text = read_text(args.in_path)
    if not text:
        print("ERROR: Input file is empty.", file=sys.stderr)
        sys.exit(1)

    pcm = synthesize_tts(
        text=text,
        api_key=args.api_key,
        model=args.model,
        voice_name=args.voice,
        style_hint=args.style,
    )

    write_wave_file(args.out_path, pcm)
    print(f"Saved TTS WAV: {args.out_path}")


if __name__ == "__main__":
    main()