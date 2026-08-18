# CRM Call Recording Pipeline — API Documentation

**Base URL:** `http://localhost:8000`  
**Interactive docs:** `http://localhost:8000/docs`

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `POST` | `/calls/process` | Transcribe + summarize an audio file |
| `POST` | `/calls/process-url` | Transcribe + summarize an audio URL |
| `POST` | `/calls/transcribe` | Transcribe an audio file (no summary) |
| `POST` | `/calls/transcribe-url` | Transcribe an audio URL (no summary) |

---

## GET /health

Returns server status. Use this to confirm the API is running before sending audio.

**Response `200`**

```json
{ "status": "ok" }
```

---

## POST /calls/process

Transcribes an audio file and returns a structured CRM summary. Both results are
returned in a single response — no polling required.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (MP3 or WAV) |
| `call_id` | string | No | Your identifier for this call |

**cURL example**

```bash
curl -X POST http://localhost:8000/calls/process \
  -F "audio=@call.mp3" \
  -F "call_id=abc123"
```

**Python example**

```python
import httpx

with open("call.mp3", "rb") as f:
    r = httpx.post(
        "http://localhost:8000/calls/process",
        files={"audio": ("call.mp3", f, "audio/mpeg")},
        data={"call_id": "abc123"},
        timeout=180,
    )
result = r.json()
```

**Response `200`** — `ProcessResult`

```json
{
  "call_id": "abc123",
  "transcript": {
    "segments": [
      {
        "speaker": "SPEAKER_1",
        "start_time": 0.0,
        "end_time": 1.1,
        "text": "السلام علیکم۔",
        "language": "ur"
      },
      {
        "speaker": "SPEAKER_2",
        "start_time": 1.8,
        "end_time": 4.7,
        "text": "وعلیکم السلام، جی کون بات کر رہا ہے؟",
        "language": "ur"
      }
    ],
    "full_text": "[SPEAKER_1] السلام علیکم۔\n[SPEAKER_2] وعلیکم السلام..."
  },
  "summary": {
    "outcome": "follow_up_required",
    "sentiment": "neutral",
    "caller_intent": "Inform a potential buyer about a new residential project and its payment plan",
    "key_points": [
      "Project name: Sky Mark",
      "Studio price: 80 lakh, monthly installment: 85,000",
      "Payment plan: 4 years, 70% during construction, 30% at possession"
    ],
    "action_items": [
      "Forward caller's contact to sales team for follow-up"
    ],
    "topics_discussed": ["Project details", "Pricing", "Payment plan"],
    "language_notes": "Urdu with English code-switching"
  }
}
```

---

## POST /calls/process-url

Same as `/calls/process` but accepts a URL instead of a file upload.
The server fetches the audio itself.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio_url` | string | Yes | Publicly accessible URL to the audio file |
| `call_id` | string | No | Your identifier for this call |

**cURL example**

```bash
curl -X POST http://localhost:8000/calls/process-url \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/call.mp3", "call_id": "abc123"}'
```

**Python example**

```python
import httpx

r = httpx.post(
    "http://localhost:8000/calls/process-url",
    json={"audio_url": "https://example.com/call.mp3", "call_id": "abc123"},
    timeout=180,
)
result = r.json()
```

**Response `200`** — same `ProcessResult` shape as `/calls/process`

---

## POST /calls/transcribe

Transcribes an audio file and returns only the diarized transcript.
Use this when you don't need the CRM summary.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (MP3 or WAV) |

**cURL example**

```bash
curl -X POST http://localhost:8000/calls/transcribe \
  -F "audio=@call.wav"
```

**Response `200`** — `Transcript`

```json
{
  "segments": [
    {
      "speaker": "SPEAKER_1",
      "start_time": 0.0,
      "end_time": 1.1,
      "text": "السلام علیکم۔",
      "language": "ur"
    }
  ],
  "full_text": "[SPEAKER_1] السلام علیکم۔\n..."
}
```

---

## POST /calls/transcribe-url

Same as `/calls/transcribe` but accepts a URL.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio_url` | string | Yes | Publicly accessible URL to the audio file |

**cURL example**

```bash
curl -X POST http://localhost:8000/calls/transcribe-url \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/call.wav"}'
```

**Response `200`** — same `Transcript` shape as `/calls/transcribe`

---

## Response Schemas

### ProcessResult

| Field | Type | Description |
|---|---|---|
| `call_id` | string \| null | Echo of the `call_id` you provided |
| `transcript` | Transcript | Full diarized transcript |
| `summary` | CallSummary | Structured CRM summary |

### Transcript

| Field | Type | Description |
|---|---|---|
| `segments` | TranscriptSegment[] | Ordered list of speaker turns |
| `full_text` | string | All segments joined as `[SPEAKER_N] text` |

### TranscriptSegment

| Field | Type | Description |
|---|---|---|
| `speaker` | string | `"SPEAKER_1"` or `"SPEAKER_2"` |
| `start_time` | float | Segment start in seconds |
| `end_time` | float | Segment end in seconds |
| `text` | string | Transcribed text for this segment |
| `language` | string \| null | `"ur"`, `"en"`, or `"mixed"` |

### CallSummary

| Field | Type | Values |
|---|---|---|
| `outcome` | string | `interested` \| `not_interested` \| `follow_up_required` \| `converted` \| `complaint` \| `other` |
| `sentiment` | string | `positive` \| `neutral` \| `negative` |
| `caller_intent` | string | One-sentence description of why the caller called |
| `key_points` | string[] | Up to 5 main points from the call |
| `action_items` | string[] | Follow-up tasks identified |
| `topics_discussed` | string[] | Topics covered during the call |
| `language_notes` | string \| null | Notes on language use (e.g. Urdu/English mix) |

---

## Error Responses

| Status | When |
|---|---|
| `422 Unprocessable Entity` | Missing required field (`audio_url` not provided) |
| `400 Bad Request` | Audio URL returned a non-2xx response |
| `500 Internal Server Error` | Transcription or summarization failed |

**Example `422`**

```json
{ "detail": "Provide 'audio_url'." }
```

---

## Supported Audio Formats

| Format | Extension | MIME Type |
|---|---|---|
| MP3 | `.mp3` | `audio/mpeg` |
| WAV | `.wav` | `audio/wav` |
| AAC | `.aac` | `audio/aac` |
| FLAC | `.flac` | `audio/flac` |
| OGG | `.ogg` | `audio/ogg` |
| WebM | `.webm` | `audio/webm` |

Files up to **20 MB** are sent inline. Larger files are uploaded via the Gemini File API automatically.

---

## Timeouts

Processing time depends on audio length:

| Audio Length | Typical Response Time |
|---|---|
| < 1 minute | 20–40s |
| 1–5 minutes | 40–90s |
| 5–15 minutes | 90–180s |

Set your HTTP client timeout to at least **180 seconds**.

---

## Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Requires `.env` with:

```
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```
