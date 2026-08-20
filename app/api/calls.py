import mimetypes
from typing import Annotated

import httpx
from fastapi import APIRouter, File, Form, UploadFile

from app.models.schemas import (
    ProcessResult,
    ProcessUrlRequest,
    SummarizeResult,
    SummarizeUrlRequest,
    TranscribeResult,
    TranscribeUrlRequest,
)
from app.services import summarization, transcription
from app.services.transcription import ScriptMode

router = APIRouter(prefix="/calls", tags=["calls"])


def _fetch_url(url: str) -> tuple[bytes, str]:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
    mime = r.headers.get("content-type", "audio/mpeg").split(";")[0].strip()
    return r.content, mime


_MIME_NORM = {
    "audio/vnd.wave": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/mp3": "audio/mpeg",
    "audio/x-mp3": "audio/mpeg",
}


def _mime_from_file(filename: str, content_type: str | None) -> str:
    if content_type and content_type not in ("application/octet-stream", ""):
        mime = content_type
    else:
        guessed, _ = mimetypes.guess_type(filename or "")
        mime = guessed or "audio/mpeg"
    return _MIME_NORM.get(mime, mime)


# ── process (transcript + summary) ───────────────────────────────────────────

@router.post("/process", response_model=ProcessResult, summary="Transcribe + summarize audio file")
def process_file(
    audio: Annotated[UploadFile, File()],
    call_id: Annotated[str, Form()],
    script: Annotated[ScriptMode, Form()] = "mixed",
):
    mime = _mime_from_file(audio.filename, audio.content_type)
    audio_bytes = audio.file.read()
    transcript = transcription.transcribe(audio_bytes, mime, script=script)
    summary = summarization.summarize(transcript)
    return ProcessResult(call_id=call_id, transcript=transcript, summary=summary)


@router.post("/process-url", response_model=ProcessResult, summary="Transcribe + summarize audio URL")
def process_url(body: ProcessUrlRequest):
    audio_bytes, mime = _fetch_url(body.audio_url)
    transcript = transcription.transcribe(audio_bytes, mime, script=body.script)
    summary = summarization.summarize(transcript)
    return ProcessResult(call_id=body.call_id, transcript=transcript, summary=summary)


# ── summarize only ────────────────────────────────────────────────────────────

@router.post("/summarize", response_model=SummarizeResult, summary="Transcribe + summarize audio file — return summary only")
def summarize_file(
    audio: Annotated[UploadFile, File()],
    call_id: Annotated[str, Form()],
):
    mime = _mime_from_file(audio.filename, audio.content_type)
    audio_bytes = audio.file.read()
    transcript = transcription.transcribe(audio_bytes, mime, script="mixed")
    return SummarizeResult(call_id=call_id, summary=summarization.summarize(transcript))


@router.post("/summarize-url", response_model=SummarizeResult, summary="Transcribe + summarize audio URL — return summary only")
def summarize_url(body: SummarizeUrlRequest):
    audio_bytes, mime = _fetch_url(body.audio_url)
    transcript = transcription.transcribe(audio_bytes, mime, script="mixed")
    return SummarizeResult(call_id=body.call_id, summary=summarization.summarize(transcript))


# ── transcribe only ───────────────────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResult, summary="Transcribe audio file only")
def transcribe_file(
    audio: Annotated[UploadFile, File()],
    call_id: Annotated[str, Form()],
    script: Annotated[ScriptMode, Form()] = "mixed",
):
    mime = _mime_from_file(audio.filename, audio.content_type)
    audio_bytes = audio.file.read()
    return TranscribeResult(call_id=call_id, transcript=transcription.transcribe(audio_bytes, mime, script=script))


@router.post("/transcribe-url", response_model=TranscribeResult, summary="Transcribe audio URL only")
def transcribe_url(body: TranscribeUrlRequest):
    audio_bytes, mime = _fetch_url(body.audio_url)
    return TranscribeResult(call_id=body.call_id, transcript=transcription.transcribe(audio_bytes, mime, script=body.script))
