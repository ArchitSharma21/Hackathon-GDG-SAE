## Gemini Voice Transcriber

A small Python prototype for multilingual speech workflows built around Gemini:

- record audio from your microphone
- transcribe speech from a saved WAV file
- optionally translate the transcript
- synthesize speech from text with Gemini TTS
- use a basic Streamlit frontend for local testing

This repo is currently a hackathon-style prototype focused on getting the end-to-end flow working quickly.

## What It Does

There are two core backend flows:

1. Speech to text
   - Record from the microphone
   - Save the recording as a `.wav`
   - Send the audio to Gemini for transcription
   - Optionally ask Gemini to translate the transcript

2. Text to speech
   - Read text from a file
   - Send the text to Gemini TTS
   - Save the generated audio as a `.wav`

On top of that, there is a Streamlit app that lets you:

- start recording
- stop recording
- see a `Transcribing...` status while Gemini processes the file
- play back the saved recording
- view the transcript and optional translation directly in the UI

## Project Structure

`streamlit_app.py`

- Streamlit frontend for recording and transcription

`listen_and_transcribe.py`

- CLI script for recording audio and transcribing with Gemini
- also exposes reusable helpers for transcribing an existing WAV file

`tts_from_file.py`

- CLI script for Gemini text-to-speech from a text file

`data/audios_from_file/`

- saved WAV recordings from the Streamlit app

`data/transcripts_from_wav/`

- saved transcript `.txt` and `.json` files from the Streamlit app

`requirements.txt`

- Python dependencies

## Requirements

- Python 3.12+
- A valid Gemini API key
- A working microphone input on your machine

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Add your Gemini API key to a `.env` file.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

## Run The Streamlit App

Start the UI with:

```bash
.venv/bin/streamlit run streamlit_app.py
```

### Streamlit Flow

1. Click `▶ Start` to begin recording from your microphone.
2. Click `|| Stop` to stop recording.
3. The app saves the WAV file and shows `Transcribing...` while Gemini processes it.
4. Once finished, the page shows:
   - the saved audio player
   - detected language
   - transcript
   - optional translation
5. Click `■ Reset` to clear the current recording state.

### Streamlit Notes

- The API key field in the UI is intentionally blank by default.
- If you leave it empty, the app uses `GEMINI_API_KEY` from `.env` on the backend.
- If you enter a key in the field, that key is used for that run only.
- Recordings are saved in `data/audios_from_file/`.
- Transcript files are saved in `data/transcripts_from_wav/`.

## CLI Usage

### 1. Record And Transcribe From Microphone

Basic usage:

```bash
.venv/bin/python listen_and_transcribe.py --seconds 10 --out transcript.txt
```

Translate to English:

```bash
.venv/bin/python listen_and_transcribe.py --seconds 10 --out transcript.txt --translate_to en
```

Save structured JSON too:

```bash
.venv/bin/python listen_and_transcribe.py --seconds 10 --out transcript.txt --json_out transcript.json
```

Choose a specific input device:

```bash
.venv/bin/python listen_and_transcribe.py --device 2 --seconds 10 --out transcript.txt
```

Useful options:

- `--seconds`: recording length in seconds
- `--device`: audio input device index
- `--wav_out`: path to save the recorded WAV
- `--out`: transcript text output file
- `--json_out`: optional JSON output file
- `--translate_to`: translation target language code like `en`, `de`, `fr`
- `--model`: Gemini model for transcription
- `--api_key`: override `GEMINI_API_KEY`

### 2. Generate TTS From A Text File

Basic usage:

```bash
.venv/bin/python tts_from_file.py --in transcript.txt --out out.wav --voice Kore
```

With a style hint:

```bash
.venv/bin/python tts_from_file.py --in script.txt --out podcast.wav --style "Warm, slow, audiobook style"
```

Useful options:

- `--in`: input text file
- `--out`: output WAV path
- `--voice`: Gemini prebuilt voice
- `--style`: optional speaking style hint
- `--model`: Gemini TTS model
- `--api_key`: override `GEMINI_API_KEY`

## Supported Translation Targets

The transcription script currently includes a built-in list of common European language codes, including:

- `en`
- `de`
- `fr`
- `es`
- `it`
- `pt`
- `nl`
- `pl`
- `sv`
- `da`
- `fi`
- `cs`
- `sk`
- `sl`
- `hu`
- `ro`
- `bg`
- `hr`
- `sr`
- `el`
- `tr`
- `uk`
- `ru`

You can still pass other BCP-47-style codes, but the current helper list is optimized around these.

## Common Issues

### No transcript appears

- Make sure `GEMINI_API_KEY` is set correctly.
- Check whether the app saved a WAV file successfully.
- If recording works but transcription fails, the UI should show an error message.
- Very short or silent recordings may produce empty or poor transcription output.

### Microphone problems

- Make sure your OS microphone permissions are enabled.
- If the default input device does not work, try entering an audio device index manually.

### Dependency problems

If `streamlit` or other modules are missing, reinstall:

```bash
pip install -r requirements.txt
```

## Current Limitations

- This is a local prototype, not a production app.
- The Streamlit app records from the local machine microphone only.
- Transcription runs after recording stops; there is no live streaming transcription yet.
- The UI is intentionally basic and focused on testing the flow.
- Error handling is present but still fairly lightweight.

## Next Possible Improvements

- Add TTS playback directly in the Streamlit UI
- Add upload support for existing audio files
- Add continuous conversation mode
- Add better device selection UI
- Add export/download buttons for transcript and audio

## License

No license has been added yet. If you plan to share or publish this repo, add one explicitly.
