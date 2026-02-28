#!/usr/bin/env python3
"""
Basic Streamlit frontend for local microphone recording and Gemini transcription.
"""

from __future__ import annotations

import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import streamlit as st
from dotenv import load_dotenv

from listen_and_transcribe import AudioConfig, EUROPEAN_LANGS, transcribe_wav_file, write_wav


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "data" / "audios_from_file"
TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts_from_wav"


class StreamingRecorder:
    def __init__(self, cfg: AudioConfig, device: Optional[int]) -> None:
        self.cfg = cfg
        self.device = device
        self.frames: list[np.ndarray] = []
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None

    def _callback(self, indata: np.ndarray, frame_count: int, time_info: object, status: object) -> None:
        del frame_count, time_info, status
        self.frames.append(indata.copy())

    def _record_forever(self) -> None:
        try:
            with sd.InputStream(
                samplerate=self.cfg.sample_rate,
                channels=self.cfg.channels,
                dtype=self.cfg.dtype,
                device=self.device,
                callback=self._callback,
            ):
                self.started_at = time.time()
                while not self.stop_event.wait(0.1):
                    pass
        except Exception as exc:
            self.error = str(exc)

    def start(self) -> None:
        self.thread = threading.Thread(target=self._record_forever, daemon=True)
        self.thread.start()

    def stop(self) -> np.ndarray:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

        if self.error:
            raise RuntimeError(self.error)

        if not self.frames:
            return np.empty((0, self.cfg.channels), dtype=np.int16)

        return np.concatenate(self.frames, axis=0).astype(np.int16)


def init_state() -> None:
    defaults = {
        "record_state": "idle",
        "recorder": None,
        "latest_result": None,
        "latest_wav_path": None,
        "latest_txt_path": None,
        "latest_json_path": None,
        "ui_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ensure_data_dirs() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


def build_output_paths() -> tuple[Path, Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (
        AUDIO_DIR / f"recording_{stamp}.wav",
        TRANSCRIPT_DIR / f"transcript_{stamp}.txt",
        TRANSCRIPT_DIR / f"transcript_{stamp}.json",
    )


def parse_device(device_text: str) -> Optional[int]:
    value = device_text.strip()
    if not value:
        return None
    return int(value)


def read_text_file(path: Optional[str]) -> str:
    if not path:
        return ""

    file_path = Path(path)
    if not file_path.exists():
        return ""

    return file_path.read_text(encoding="utf-8").strip()


def read_json_file(path: Optional[str]) -> dict:
    if not path:
        return {}

    file_path = Path(path)
    if not file_path.exists():
        return {}

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def start_recording(device: Optional[int]) -> None:
    recorder = StreamingRecorder(AudioConfig(sample_rate=16000, channels=1, dtype="int16"), device=device)
    st.session_state.recorder = recorder
    st.session_state.ui_error = None
    st.session_state.latest_result = None
    recorder.start()
    st.session_state.record_state = "recording"


def stop_recording_and_transcribe(
    api_key: str,
    model: str,
    translate_to: Optional[str],
) -> None:
    recorder: Optional[StreamingRecorder] = st.session_state.recorder
    if recorder is None:
        st.session_state.record_state = "idle"
        st.session_state.ui_error = "No active recording was found."
        return

    try:
        pcm = recorder.stop()
    except Exception as exc:
        st.session_state.recorder = None
        st.session_state.record_state = "idle"
        st.session_state.ui_error = f"Recording failed: {exc}"
        return

    st.session_state.recorder = None

    if pcm.size == 0:
        st.session_state.record_state = "idle"
        st.session_state.ui_error = "No audio was captured. Check your microphone and try again."
        return

    wav_path, txt_path, json_path = build_output_paths()
    write_wav(str(wav_path), pcm, recorder.cfg)

    st.session_state.latest_wav_path = str(wav_path)
    st.session_state.latest_txt_path = str(txt_path)
    st.session_state.latest_json_path = str(json_path)
    st.session_state.record_state = "stopped"

    if not api_key:
        st.session_state.latest_result = None
        st.session_state.ui_error = "Recording saved, but transcription was skipped because GEMINI_API_KEY is missing."
        return

    try:
        result = transcribe_wav_file(
            wav_path=str(wav_path),
            api_key=api_key,
            model=model,
            translate_to=translate_to,
            txt_out=str(txt_path),
            json_out=str(json_path),
        )
    except Exception as exc:
        st.session_state.latest_result = None
        st.session_state.ui_error = f"Recording saved, but transcription failed: {exc}"
        return

    st.session_state.latest_result = result
    st.session_state.ui_error = None


def reset_recorder() -> None:
    st.session_state.record_state = "idle"
    st.session_state.recorder = None
    st.session_state.ui_error = None


def render_text_block(label: str, value: str) -> None:
    st.markdown(f"**{label}**")
    st.code(value if value else "(empty)", language=None)


def main() -> None:
    st.set_page_config(page_title="Gemini Voice Transcriber", page_icon="🎙️", layout="centered")
    load_dotenv()
    ensure_data_dirs()
    init_state()

    st.markdown(
        """
        <style>
        .stButton button {
            font-size: 1.15rem;
            font-weight: 600;
            min-height: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Gemini Voice Transcriber")
    st.caption("Record from your local microphone, stop, and transcribe the saved WAV with Gemini.")

    col1, col2 = st.columns(2)
    with col1:
        model = st.text_input("Transcription model", value="gemini-3-flash-preview")
    with col2:
        device_text = st.text_input("Input device index", value="", placeholder="Leave empty for default")

    translate_options = ["None"] + [f"{code} ({name})" for code, name in EUROPEAN_LANGS.items()]
    translate_choice = st.selectbox("Translate to", options=translate_options, index=0)
    translate_to = None if translate_choice == "None" else translate_choice.split(" ", 1)[0]

    api_key_input = st.text_input(
        "Gemini API key",
        value="",
        type="password",
        help="Leave empty to use GEMINI_API_KEY from the backend .env file.",
    )

    try:
        device = parse_device(device_text)
    except ValueError:
        device = None
        st.error("Input device index must be an integer.")

    effective_api_key = api_key_input.strip() or os.getenv("GEMINI_API_KEY", "")
    current_state = st.session_state.record_state

    start_col, stop_col, reset_col = st.columns(3)
    with start_col:
        start_clicked = st.button(
            "▶ Start",
            key="start_button",
            type="primary",
            use_container_width=True,
            disabled=current_state == "recording",
        )
    with stop_col:
        stop_clicked = st.button(
            "|| Stop",
            key="stop_button",
            use_container_width=True,
            disabled=current_state != "recording",
        )
    with reset_col:
        reset_clicked = st.button(
            "■ Reset",
            key="reset_button",
            use_container_width=True,
            disabled=current_state == "idle",
        )

    if start_clicked:
        start_recording(device)
        st.rerun()

    if stop_clicked:
        with st.spinner("Transcribing..."):
            stop_recording_and_transcribe(
                api_key=effective_api_key,
                model=model.strip() or "gemini-3-flash-preview",
                translate_to=translate_to,
            )
        st.rerun()

    if reset_clicked:
        reset_recorder()
        st.rerun()

    if st.session_state.record_state == "recording":
        st.info("Recording is active. Click the same button again to stop, save the WAV, and transcribe it.")
        recorder: Optional[StreamingRecorder] = st.session_state.recorder
        if recorder and recorder.started_at:
            st.caption(f"Elapsed: {time.time() - recorder.started_at:.1f}s")

    if st.session_state.ui_error:
        st.error(st.session_state.ui_error)

    latest_wav_path = st.session_state.latest_wav_path
    if latest_wav_path and Path(latest_wav_path).exists():
        st.subheader("Latest Recording")
        with open(latest_wav_path, "rb") as wav_file:
            st.audio(wav_file.read(), format="audio/wav")
        st.caption(f"WAV saved to: {latest_wav_path}")

        result = st.session_state.latest_result or read_json_file(st.session_state.latest_json_path)
        transcript_text = result.get("transcript", "").strip() if result else ""
        if not transcript_text:
            transcript_text = read_text_file(st.session_state.latest_txt_path)
            if "\n--- TRANSLATION ---\n" in transcript_text:
                transcript_text = transcript_text.split("\n--- TRANSLATION ---\n", 1)[0].strip()

        translation = result.get("translation", "").strip() if result else ""
        if not translation:
            transcript_file_contents = read_text_file(st.session_state.latest_txt_path)
            if "\n--- TRANSLATION ---\n" in transcript_file_contents:
                translation = transcript_file_contents.split("\n--- TRANSLATION ---\n", 1)[1].strip()

        if result or transcript_text:
            detected_name = result.get("detected_language_name", "Unknown") if result else "Unknown"
            detected_code = result.get("detected_language_code", "unknown") if result else "unknown"
            st.write(f"Detected language: {detected_name} ({detected_code})")
            render_text_block("Transcript", transcript_text)

            if translation:
                render_text_block("Translation", translation)

            st.caption(f"Transcript text: {st.session_state.latest_txt_path}")
            st.caption(f"Transcript JSON: {st.session_state.latest_json_path}")
        else:
            st.info("The recording was saved, but no transcript content is available yet.")


if __name__ == "__main__":
    main()
