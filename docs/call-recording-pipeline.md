# CRM call recording → transcript → summary pipeline

## Overview

CRM receives call recordings (stereo WAV, dual-channel — caller on one
channel, callee on the other) from telephony (Asterisk). We need to:

1. Store the recording for CRM playback.
2. Transcribe the recording with Gemini, asking it to diarize
   (label speakers) and timestamp segments directly.
3. Summarize the transcript into a structured JSON object via an LLM
   using a fixed schema.
4. Expose transcript and summary via two separate FastAPI endpoints.

Language: calls are primarily Urdu with heavy English code-switching
(numbers, business terms). This is why Gemini was chosen over
Whisper-class ASR — see "Model choice" below.

## High-level flow

```
Asterisk call ends
  → stereo WAV received
  → upload stereo WAV to object storage        [playback file, no processing needed]
  → enqueue processing job (call_id, storage_url)
       │
       ▼
  worker downloads stereo WAV
       │
       ├─ send stereo WAV → Gemini STT → transcript
       │     (Gemini asked to diarize + timestamp directly)
       │
       ├─ send transcript → LLM (structured output / JSON schema)
       │     → structured summary
       │
       └─ persist: transcript_json, summary_json, status=done
       │
       ▼
  FastAPI serves:
    GET /calls/{call_id}/transcript
    GET /calls/{call_id}/summary
```

Two endpoints are separate on purpose: transcript can be ready before
summary, they can be retried/cached independently, and the frontend can
poll each without over-fetching.

## Model choice

- **STT: Gemini** (audio input via Gemini API). Chosen specifically
  because it handles Urdu-English code-switching far better than
  Whisper-class acoustic models (semantic understanding vs. pure
  phoneme matching). Benchmark reference: Whisper-large-v3 ~53% WER on
  code-switched Urdu vs. Gemini ~3% WER on the same audio type.
- **Summary LLM**: any model with structured/JSON output (Gemini,
  Claude, or GPT). Start with Gemini for one-vendor simplicity; this
  can be swapped independently of the STT choice since it's a separate
  call on plain text.

### `calls` table (or document)

| field | type | notes |
|---|---|---|
| call_id | string (PK) | unique call/recording id |
| stereo_audio_url | string | object storage link — used for CRM playback |
| status | enum | `pending` → `transcribing` → `summarizing` → `done` / `failed` |
| transcript_json | json, nullable | see Transcript schema below |
| summary_json | json, nullable | see CallSummary schema below |
| error | string, nullable | last error message if `failed` |
| created_at / updated_at | timestamp | |

### Transcript schema (pydantic sketch)

```python
class TranscriptSegment(BaseModel):
    speaker: str          # as labeled by Gemini diarization
    start_time: float     # seconds
    end_time: float
    text: str
    language: str | None = None   # e.g. "ur", "en", "mixed" — optional

class Transcript(BaseModel):
    call_id: str
    segments: list[TranscriptSegment]
    full_text: str   # convenience: segments joined in order
```
