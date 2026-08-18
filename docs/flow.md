# CRM Call Recording Pipeline — How It Works

## Overview

When a call ends on Asterisk (your phone system), this pipeline transcribes it
and produces a structured CRM summary in a single API call — no queues, no
database, no polling needed.

---

## The Full Flow (Step by Step)

```
Phone Call Ends
      │
      ▼
Step 1 → Send Recording to API
         (MP3 or WAV — file upload or URL)
      │
      ▼
Step 2 → Transcribe with Gemini 3.6 Flash
         (diarized Urdu/English transcript)
      │
      ▼
Step 3 → Summarize with Groq GPT-OSS 20B
         (structured CRM summary)
      │
      ▼
Step 4 → Results returned directly in the response
```

---

## Step 1 — Send the Recording

- Asterisk finishes the call and sends the audio file (MP3 or WAV).
- Two ways to submit:
  - **File upload** → `POST /calls/process` with the audio file attached
  - **URL** → `POST /calls/process-url` with a link to the audio
- The API processes it synchronously and returns results when done.
- No job IDs, no polling — one request, one response.

---

## Step 2 — Transcription

**Model: Google Gemini 3.6 Flash**

- The audio is sent directly to Gemini 3.6 Flash.
- Gemini listens to both channels of the stereo call and returns a diarized
  transcript — who said what, when, and in which language.
- Files up to 20 MB are sent inline. Larger files go through the Gemini File API.
- Each segment looks like this:

```json
{
  "speaker":    "SPEAKER_1",
  "start_time": 4.3,
  "end_time":   18.1,
  "text":       "ہمارے پروجیکٹ کا نام ہے Sky Mark...",
  "language":   "mixed"
}
```

- Why Gemini? It handles **Urdu + English code-switching** far better than
  any other model, with near-zero error rate on this audio type.

---

## Step 3 — Summarization

**Model: Groq GPT-OSS 20B**

- The full transcript text is sent to Groq's GPT-OSS 20B.
- The model returns a fixed JSON structure — no free-form text.
- The summary looks like this:

```json
{
  "outcome":          "follow_up_required",
  "sentiment":        "neutral",
  "caller_intent":    "Inquiring about 2-bedroom unit pricing and payment plan",
  "key_points":       ["Budget: 1.75 crore", "Wants 2BR unit", "Needs installment plan"],
  "action_items":     ["Share brochure", "Sales exec to call after 7pm"],
  "topics_discussed": ["Pricing", "Payment plans", "Location preference"],
  "language_notes":   "Urdu with English code-switching"
}
```

- Why Groq? Ultra-fast inference, free tier available, no extra infrastructure.

---

## Step 4 — Results Returned

- Both transcript and summary are returned together in a single JSON response.
- No waiting, no status checks — the response arrives when processing is complete.

```json
{
  "call_id":    "abc123",
  "transcript": { "segments": [...], "full_text": "..." },
  "summary":    { "outcome": "...", "sentiment": "...", ... }
}
```

---

## Available Endpoints

| Endpoint | Input | Returns |
|---|---|---|
| `POST /calls/process` | Audio file (MP3 or WAV) | Transcript + Summary |
| `POST /calls/process-url` | Audio URL | Transcript + Summary |
| `POST /calls/transcribe` | Audio file (MP3 or WAV) | Transcript only |
| `POST /calls/transcribe-url` | Audio URL | Transcript only |
| `GET /health` | — | `{ "status": "ok" }` |

---

## Infrastructure at a Glance

| Component | Tool | Role |
|---|---|---|
| API | FastAPI + Uvicorn | Receives recordings, returns results |
| STT Model | Gemini 3.6 Flash | Transcribes + diarizes audio |
| Summary Model | Groq GPT-OSS 20B | Produces structured CRM summary |

No database. No queue. No worker. No Docker required.

---

## Supported Audio Formats

| Format | MIME Type |
|---|---|
| MP3 | `audio/mpeg` |
| WAV | `audio/wav` |
| AAC | `audio/aac` |
| FLAC | `audio/flac` |
| OGG | `audio/ogg` |
| WebM | `audio/webm` |

---

## Typical Timeline

| Event | Time |
|---|---|
| Call ends, audio sent to API | 0s |
| Gemini transcribes audio | ~30–60s |
| Groq summarizes transcript | ~2–5s |
| Full results returned | ~35–65s after call ends |
