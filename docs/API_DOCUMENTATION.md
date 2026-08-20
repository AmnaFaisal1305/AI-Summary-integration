# CRM Call Recording Pipeline — API Documentation

**Deployed URL:** `https://crm-intelligence-voxa.vercel.app`  
**Local URL:** `http://localhost:8000`  
**Interactive docs:** `https://crm-intelligence-voxa.vercel.app/docs`

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `POST` | `/calls/process` | Transcribe + summarize audio file |
| `POST` | `/calls/process-url` | Transcribe + summarize audio URL |
| `POST` | `/calls/summarize` | Summarize audio file (no transcript in response) |
| `POST` | `/calls/summarize-url` | Summarize audio URL (no transcript in response) |
| `POST` | `/calls/transcribe` | Transcribe audio file (no summary) |
| `POST` | `/calls/transcribe-url` | Transcribe audio URL (no summary) |

---

## GET /health

Returns server status.

**Response `200`**

```json
{ "status": "ok" }
```

---

## POST /calls/process

Transcribes an audio file and returns both the transcript and CRM summary.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (MP3, WAV, etc.) |
| `call_id` | string | Yes | Your identifier for this call |
| `script` | string | No | Transcript script: `urdu`, `roman_urdu`, or `mixed` (default: `mixed`) |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/process \
  -F "audio=@call.mp3" \
  -F "call_id=abc123" \
  -F "script=mixed"
```

**Python example**

```python
import httpx

with open("call.mp3", "rb") as f:
    r = httpx.post(
        "https://crm-intelligence-voxa.vercel.app/calls/process",
        files={"audio": ("call.mp3", f, "audio/mpeg")},
        data={"call_id": "abc123", "script": "mixed"},
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
    "full_text": "[SPEAKER_1] (0.0s-1.1s) السلام علیکم۔\n[SPEAKER_2] (1.8s-4.7s) وعلیکم السلام..."
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
    "action_items": ["Forward caller's contact to sales team for follow-up"],
    "topics_discussed": ["Project details", "Pricing", "Payment plan"],
    "language_notes": "Urdu with English code-switching"
  }
}
```

---

## POST /calls/process-url

Same as `/calls/process` but the server fetches the audio from a URL.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio_url` | string | Yes | Publicly accessible URL to the audio file |
| `call_id` | string | Yes | Your identifier for this call |
| `script` | string | No | Transcript script: `urdu`, `roman_urdu`, or `mixed` (default: `mixed`) |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/process-url \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/call.mp3", "call_id": "abc123", "script": "mixed"}'
```

**Response `200`** — same `ProcessResult` shape as `/calls/process`

---

## POST /calls/summarize

Transcribes the audio and returns only the CRM summary (no transcript in response). Use this when you only need structured call intelligence and want a smaller response payload.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (MP3, WAV, etc.) |
| `call_id` | string | Yes | Your identifier for this call |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/summarize \
  -F "audio=@call.mp3" \
  -F "call_id=abc123"
```

**Response `200`** — `SummarizeResult`

```json
{
  "call_id": "abc123",
  "summary": {
    "outcome": "interested",
    "sentiment": "positive",
    "caller_intent": "Enquire about apartment pricing and availability",
    "key_points": ["Interested in 2-bedroom unit", "Budget around 1.2 crore"],
    "action_items": ["Send brochure", "Schedule site visit"],
    "topics_discussed": ["Pricing", "Availability", "Location"],
    "language_notes": "Urdu with English code-switching"
  }
}
```

---

## POST /calls/summarize-url

Same as `/calls/summarize` but accepts a URL.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio_url` | string | Yes | Publicly accessible URL to the audio file |
| `call_id` | string | Yes | Your identifier for this call |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/summarize-url \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/call.mp3", "call_id": "abc123"}'
```

**Response `200`** — same `SummarizeResult` shape as `/calls/summarize`

---

## POST /calls/transcribe

Transcribes an audio file and returns the diarized transcript with timestamps. No summary is generated.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio` | file | Yes | Audio file (MP3, WAV, etc.) |
| `call_id` | string | Yes | Your identifier for this call |
| `script` | string | No | Transcript script: `urdu`, `roman_urdu`, or `mixed` (default: `mixed`) |

**script options**

| Value | Output |
|---|---|
| `urdu` | All text in Urdu script (Arabic letters), including English words transliterated |
| `roman_urdu` | All text in Roman/Latin script, Urdu words written phonetically |
| `mixed` | Each word in the script the speaker actually used (default) |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/transcribe \
  -F "audio=@call.wav" \
  -F "call_id=abc123" \
  -F "script=roman_urdu"
```

**Response `200`** — `TranscribeResult`

```json
{
  "call_id": "abc123",
  "transcript": {
    "segments": [
      {
        "speaker": "SPEAKER_1",
        "start_time": 0.0,
        "end_time": 1.1,
        "text": "Assalam-o-Alaikum.",
        "language": "ur"
      }
    ],
    "full_text": "[SPEAKER_1] (0.0s-1.1s) Assalam-o-Alaikum.\n..."
  }
}
```

---

## POST /calls/transcribe-url

Same as `/calls/transcribe` but accepts a URL.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `audio_url` | string | Yes | Publicly accessible URL to the audio file |
| `call_id` | string | Yes | Your identifier for this call |
| `script` | string | No | Transcript script: `urdu`, `roman_urdu`, or `mixed` (default: `mixed`) |

**cURL example**

```bash
curl -X POST https://crm-intelligence-voxa.vercel.app/calls/transcribe-url \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/call.wav", "call_id": "abc123"}'
```

**Response `200`** — same `TranscribeResult` shape as `/calls/transcribe`

---

## Response Schemas

### ProcessResult

| Field | Type | Description |
|---|---|---|
| `call_id` | string | Echo of the `call_id` you provided |
| `transcript` | Transcript | Full diarized transcript |
| `summary` | CallSummary | Structured CRM summary |

### TranscribeResult

| Field | Type | Description |
|---|---|---|
| `call_id` | string | Echo of the `call_id` you provided |
| `transcript` | Transcript | Full diarized transcript |

### SummarizeResult

| Field | Type | Description |
|---|---|---|
| `call_id` | string | Echo of the `call_id` you provided |
| `summary` | CallSummary | Structured CRM summary |

### Transcript

| Field | Type | Description |
|---|---|---|
| `segments` | TranscriptSegment[] | Ordered list of speaker turns |
| `full_text` | string | All segments joined as `[SPEAKER_N] (start-end) text` |

### TranscriptSegment

| Field | Type | Description |
|---|---|---|
| `speaker` | string | `"SPEAKER_1"` (caller) or `"SPEAKER_2"` (callee) |
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
| `key_points` | string[] | Main points from the call |
| `action_items` | string[] | Follow-up tasks identified |
| `topics_discussed` | string[] | Topics covered during the call |
| `language_notes` | string \| null | Notes on language use |

---

## Error Responses

| Status | When |
|---|---|
| `422 Unprocessable Entity` | Missing required field (`call_id`, `audio`, or `audio_url`) |
| `400 Bad Request` | Audio URL returned a non-2xx response |
| `503 Service Unavailable` | Gemini API is temporarily overloaded — retry after a few minutes |
| `502 Bad Gateway` | Gemini returned an unexpected response format |

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

## Running Locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Requires `.env` with:

```
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```
