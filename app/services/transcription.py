import json
import os
import tempfile
from typing import Literal

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings
from app.models.schemas import Transcript, TranscriptSegment

_client = genai.Client(api_key=settings.gemini_api_key)
_MODEL = "gemini-3.6-flash"
_SIZE_THRESHOLD = 20 * 1024 * 1024  # 20 MB

ScriptMode = Literal["urdu", "roman_urdu", "mixed"]

_EXT_MAP = {
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/vnd.wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/x-mp3": ".mp3",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/aac": ".aac",
    "audio/aiff": ".aiff",
    "audio/webm": ".webm",
}

_SCRIPT_INSTRUCTIONS = {
    "urdu": (
        "Write ALL transcribed text in Urdu script (Arabic letters). "
        "Even if speakers use English words, transliterate them into Urdu script."
    ),
    "roman_urdu": (
        "Write ALL transcribed text in Roman Urdu (Latin alphabet transliteration). "
        "Even if speakers use Urdu words, write them in Roman script (e.g. 'Assalam-o-Alaikum', 'theek hai'). "
        "English words stay in English."
    ),
    "mixed": (
        "Transcribe each word in the script the speaker actually used — "
        "Urdu script for Urdu words, English letters for English words."
    ),
}

_PROMPT_BASE = (
    "Transcribe this stereo business phone call. "
    "The audio is in Urdu with English code-switching. "
    "SPEAKER_1 is the caller, SPEAKER_2 is the callee.\n\n"
    "{script_instruction}\n\n"
    "Return ONLY a valid JSON array. Each element must have exactly these fields:\n"
    '{{"speaker": "SPEAKER_1" or "SPEAKER_2", '
    '"start_time": <float seconds>, '
    '"end_time": <float seconds>, '
    '"text": "<transcribed text>", '
    '"language": "ur" or "en" or "mixed"}}\n\n'
    "No markdown, no explanation — raw JSON array only."
)


def _build_prompt(script: ScriptMode) -> str:
    return _PROMPT_BASE.format(script_instruction=_SCRIPT_INSTRUCTIONS[script])


def _parse_response(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(raw)


def transcribe(audio_bytes: bytes, mime_type: str = "audio/mpeg", script: ScriptMode = "mixed") -> Transcript:
    prompt = _build_prompt(script)

    try:
      return _transcribe(audio_bytes, mime_type, prompt)
    except genai_errors.ServerError as e:
        raise HTTPException(status_code=503, detail=f"Gemini unavailable: {e}")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected Gemini response format: {e}")


def _transcribe(audio_bytes: bytes, mime_type: str, prompt: str) -> Transcript:
    if len(audio_bytes) <= _SIZE_THRESHOLD:
        response = _client.models.generate_content(
            model=_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )
    else:
        ext = _EXT_MAP.get(mime_type, ".mp3")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            uploaded = _client.files.upload(
                file=tmp_path,
                config={"mime_type": mime_type},
            )
            response = _client.models.generate_content(
                model=_MODEL,
                contents=[prompt, uploaded],
            )
            _client.files.delete(name=uploaded.name)
        finally:
            os.unlink(tmp_path)

    segments_data = _parse_response(response.text)
    segments = [TranscriptSegment(**seg) for seg in segments_data]
    full_text = "\n".join(f"[{s.speaker}] ({s.start_time:.1f}s-{s.end_time:.1f}s) {s.text}" for s in segments)

    return Transcript(segments=segments, full_text=full_text)
