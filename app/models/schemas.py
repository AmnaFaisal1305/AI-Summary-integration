from typing import Literal

from pydantic import BaseModel

ScriptMode = Literal["urdu", "roman_urdu", "mixed"]


class TranscriptSegment(BaseModel):
    speaker: str
    start_time: float
    end_time: float
    text: str
    language: str | None = None


class Transcript(BaseModel):
    segments: list[TranscriptSegment]
    full_text: str


class CallSummary(BaseModel):
    outcome: Literal[
        "interested",
        "not_interested",
        "follow_up_required",
        "converted",
        "complaint",
        "other",
    ]
    sentiment: Literal["positive", "neutral", "negative"]
    caller_intent: str
    key_points: list[str]
    action_items: list[str]
    topics_discussed: list[str]
    language_notes: str | None = None


class ProcessResult(BaseModel):
    call_id: str | None = None
    transcript: Transcript
    summary: CallSummary


class ProcessUrlRequest(BaseModel):
    audio_url: str
    call_id: str | None = None
    script: ScriptMode = "mixed"


class TranscribeUrlRequest(BaseModel):
    audio_url: str
    script: ScriptMode = "mixed"


class SummarizeUrlRequest(BaseModel):
    audio_url: str
