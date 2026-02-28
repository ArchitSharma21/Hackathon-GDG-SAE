#!/usr/bin/env python3
"""
Listen from microphone -> save WAV -> transcribe with Gemini -> write transcript to file.

Usage examples:
  python listen_and_transcribe.py --seconds 10 --out transcript.txt
  python listen_and_transcribe.py --seconds 20 --out transcript.txt --translate_to en
  python listen_and_transcribe.py --device 2 --seconds 15 --out out.txt --json_out out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import wave
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv

import numpy as np
import sounddevice as sd
from google import genai
from google.genai import types



load_dotenv()

# Get variables
api_key = os.getenv("GEMINI_API_KEY")

# ---------------------------
# Language helpers (BCP-47)
# ---------------------------
EUROPEAN_LANGS: Dict[str, str] = {
    # Major European languages
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "da": "Danish",
    "nb": "Norwegian Bokmål",
    "nn": "Norwegian Nynorsk",
    "fi": "Finnish",
    "cs": "Czech",
    "sk": "Slovak",
    "sl": "Slovenian",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "el": "Greek",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ru": "Russian",
}


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"


def record_microphone(seconds: float, device: Optional[int], cfg: AudioConfig) -> np.ndarray:
    """Record audio from microphone and return int16 PCM samples."""
    frames = int(seconds * cfg.sample_rate)
    recording = sd.rec(
        frames,
        samplerate=cfg.sample_rate,
        channels=cfg.channels,
        dtype=cfg.dtype,
        device=device,
    )
    sd.wait()
    return recording


def write_wav(path: str, pcm_int16: np.ndarray, cfg: AudioConfig) -> None:
    """Write int16 PCM numpy array to a WAV file."""
    # Ensure shape: (frames,) or (frames, channels)
    pcm = pcm_int16
    if pcm.dtype != np.int16:
        pcm = pcm.astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(cfg.channels)
        wf.setsampwidth(2)  # int16 => 2 bytes
        wf.setframerate(cfg.sample_rate)
        wf.writeframes(pcm.tobytes())


def load_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).parent
    if parent and str(parent) != ".":
        parent.mkdir(parents=True, exist_ok=True)


def build_transcription_prompt(translate_to: Optional[str]) -> str:
    """
    Ask Gemini for:
      - detected language (BCP-47 if possible)
      - transcription
      - optional translation to translate_to
    """
    base = (
        "Transcribe the speech in this audio.\n"
        "Return JSON with:\n"
        '  - "detected_language_code" (BCP-47 if you can)\n'
        '  - "detected_language_name"\n'
        '  - "transcript" (verbatim, keep punctuation)\n'
    )
    if translate_to:
        base += f'  - "translation" (translate the transcript to {translate_to})\n'
    base += "If there are multiple speakers, keep it readable (e.g., Speaker 1: ...).\n"
    return base


def transcribe_with_gemini(
    audio_bytes: bytes,
    mime_type: str,
    api_key: str,
    model: str,
    translate_to: Optional[str],
) -> Dict[str, Any]:
    """
    Send audio inline (best for <= ~20MB total request). For bigger audio, use Files API.
    Docs note inline size considerations. :contentReference[oaicite:2]{index=2}
    """
    client = genai.Client(api_key=api_key)

    prompt = build_transcription_prompt(translate_to)

    # Structured output schema
    props = {
        "detected_language_code": types.Schema(type=types.Type.STRING),
        "detected_language_name": types.Schema(type=types.Type.STRING),
        "transcript": types.Schema(type=types.Type.STRING),
    }
    required = ["detected_language_code", "detected_language_name", "transcript"]
    if translate_to:
        props["translation"] = types.Schema(type=types.Type.STRING)
        required.append("translation")

    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties=props,
                required=required,
            ),
        ),
    )

    # response.text will be JSON string due to response_mime_type
    return json.loads(response.text)


def save_outputs(
    txt_out: str,
    json_out: Optional[str],
    result: Dict[str, Any],
    also_save_translation: bool,
) -> None:
    transcript = result.get("transcript", "").strip()
    translation = result.get("translation", "").strip() if also_save_translation else ""

    ensure_parent_dir(txt_out)
    with open(txt_out, "w", encoding="utf-8") as f:
        f.write(transcript + "\n")
        if also_save_translation and translation:
            f.write("\n--- TRANSLATION ---\n")
            f.write(translation + "\n")

    if json_out:
        ensure_parent_dir(json_out)
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


def validate_translate_to(translate_to: Optional[str]) -> None:
    if translate_to and translate_to not in EUROPEAN_LANGS and len(translate_to) < 2:
        print("WARNING: translate_to should be a BCP-47 code like 'en', 'de', 'fr', etc.", file=sys.stderr)


def transcribe_wav_file(
    wav_path: str,
    api_key: str,
    model: str,
    translate_to: Optional[str] = None,
    txt_out: Optional[str] = None,
    json_out: Optional[str] = None,
) -> Dict[str, Any]:
    if not api_key:
        raise ValueError("Provide an API key or set GEMINI_API_KEY.")

    validate_translate_to(translate_to)

    audio_bytes = load_bytes(wav_path)
    result = transcribe_with_gemini(
        audio_bytes=audio_bytes,
        mime_type="audio/wav",
        api_key=api_key,
        model=model,
        translate_to=translate_to,
    )

    if txt_out:
        save_outputs(
            txt_out=txt_out,
            json_out=json_out,
            result=result,
            also_save_translation=bool(translate_to),
        )

    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=float, default=10.0, help="Recording duration.")
    p.add_argument("--device", type=int, default=None, help="Audio input device index.")
    p.add_argument("--wav_out", type=str, default="recording.wav", help="Where to save recorded wav.")
    p.add_argument("--out", type=str, default="transcript.txt", help="Transcript output file.")
    p.add_argument("--json_out", type=str, default=None, help="Optional JSON output file.")
    p.add_argument(
        "--translate_to",
        type=str,
        default=None,
        help="Optional BCP-47 language code to translate into (e.g., en, de, fr, es).",
    )
    p.add_argument(
        "--model",
        type=str,
        default="gemini-3-flash-preview",
        help="Gemini model for audio understanding.",
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

    validate_translate_to(args.translate_to)

    cfg = AudioConfig(sample_rate=16000, channels=1, dtype="int16")

    print(f"Recording {args.seconds:.1f}s @ {cfg.sample_rate}Hz ...")
    pcm = record_microphone(args.seconds, args.device, cfg)
    write_wav(args.wav_out, pcm, cfg)
    print(f"Saved WAV: {args.wav_out}")

    print(f"Transcribing with model: {args.model} ...")
    result = transcribe_wav_file(
        wav_path=args.wav_out,
        api_key=args.api_key,
        model=args.model,
        translate_to=args.translate_to,
        txt_out=args.out,
        json_out=args.json_out,
    )
    print(f"Saved transcript: {args.out}")
    if args.json_out:
        print(f"Saved JSON: {args.json_out}")

    # Helpful console summary:
    print("\nDetected language:", result.get("detected_language_name"), f"({result.get('detected_language_code')})")


if __name__ == "__main__":
    main()
