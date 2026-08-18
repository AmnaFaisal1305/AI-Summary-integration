import json

from groq import Groq

from app.config import settings
from app.models.schemas import CallSummary, Transcript

_client = Groq(api_key=settings.groq_api_key)
_MODEL = "openai/gpt-oss-20b"

_SYSTEM_PROMPT = (
    "You are a CRM assistant. Analyze the call transcript and extract structured information. "
    "The conversation is in Urdu with English code-switching. Be concise and business-focused. "
    "Return ONLY valid JSON matching this exact schema — no extra keys, no markdown:\n"
    "{\n"
    '  "outcome": one of ["interested","not_interested","follow_up_required","converted","complaint","other"],\n'
    '  "sentiment": one of ["positive","neutral","negative"],\n'
    '  "caller_intent": "<one sentence describing why the caller called>",\n'
    '  "key_points": ["<point1>", "<point2>", ...],\n'
    '  "action_items": ["<item1>", ...],\n'
    '  "topics_discussed": ["<topic1>", ...],\n'
    '  "language_notes": "<brief note on language mix, or null>"\n'
    "}"
)


def summarize(transcript: Transcript) -> CallSummary:
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": transcript.full_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return CallSummary(**data)
