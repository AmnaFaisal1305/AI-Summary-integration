"""
End-to-end pipeline test (simple synchronous API — no polling needed).

Usage:
    python test_pipeline.py --file "your_call.mp3"
    python test_pipeline.py --url  https://example.com/call.mp3
"""

import argparse
import mimetypes
import os
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE_URL = "http://localhost:8000"


def ok(msg):  print(f"  [OK]  {msg}")
def info(msg): print(f"  ...   {msg}")
def fail(msg):
    print(f"  [FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def test_health():
    print("\n[1] Health check")
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
    except httpx.ConnectError:
        fail("Cannot reach API on localhost:8000 — run: uvicorn app.main:app --reload")
    if r.status_code != 200:
        fail(f"API not healthy: {r.status_code}")
    ok("API is up")


def test_process_file(file_path: str):
    print(f"\n[2] Process file: {os.path.basename(file_path)}")
    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or "audio/mpeg"
    size_mb = os.path.getsize(file_path) / 1024 / 1024
    info(f"Size: {size_mb:.2f} MB  |  MIME: {mime}")
    info("Sending to Gemini 3.6 Flash for transcription... (30-90s)")

    t0 = time.time()
    with open(file_path, "rb") as f:
        r = httpx.post(
            f"{BASE_URL}/calls/process",
            files={"audio": (os.path.basename(file_path), f, mime)},
            timeout=180,
        )
    elapsed = time.time() - t0

    if r.status_code != 200:
        fail(f"Process returned {r.status_code}: {r.text}")

    result = r.json()
    ok(f"Done in {elapsed:.1f}s")
    return result


def test_process_url(audio_url: str):
    print(f"\n[2] Process URL: {audio_url}")
    info("Sending to Gemini 3.6 Flash for transcription... (30-90s)")

    t0 = time.time()
    r = httpx.post(
        f"{BASE_URL}/calls/process-url",
        json={"audio_url": audio_url},
        timeout=180,
    )
    elapsed = time.time() - t0

    if r.status_code != 200:
        fail(f"Process-url returned {r.status_code}: {r.text}")

    result = r.json()
    ok(f"Done in {elapsed:.1f}s")
    return result


def print_transcript(result: dict):
    print(f"\n[3] Transcript — Gemini 3.6 Flash")
    segments = result["transcript"]["segments"]
    ok(f"{len(segments)} segments")
    print()
    for seg in segments[:5]:
        lang = seg.get("language", "?")
        print(f"      [{seg['speaker']}] ({seg['start_time']:.1f}s-{seg['end_time']:.1f}s) [{lang}]")
        print(f"       {seg['text'][:100]}")
        print()
    if len(segments) > 5:
        print(f"      ... and {len(segments) - 5} more segments")


def print_summary(result: dict):
    print(f"\n[4] Summary — Groq GPT-OSS 20B")
    s = result["summary"]
    ok("Structured summary received")
    print()
    print(f"      outcome:        {s.get('outcome')}")
    print(f"      sentiment:      {s.get('sentiment')}")
    print(f"      caller_intent:  {s.get('caller_intent')}")
    print()
    print("      key_points:")
    for p in s.get("key_points", []):
        print(f"        - {p}")
    print("      action_items:")
    for a in s.get("action_items", []):
        print(f"        - {a}")
    print("      topics_discussed:")
    for t in s.get("topics_discussed", []):
        print(f"        - {t}")
    print(f"\n      language_notes: {s.get('language_notes')}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to audio file (MP3/WAV)")
    group.add_argument("--url", help="URL of audio file")
    args = parser.parse_args()

    print("=" * 60)
    print("  CRM Pipeline — End-to-End Test")
    print("=" * 60)

    test_health()

    if args.file:
        if not os.path.exists(args.file):
            fail(f"File not found: {args.file}")
        result = test_process_file(args.file)
    else:
        result = test_process_url(args.url)

    print_transcript(result)
    print_summary(result)

    print("\n" + "=" * 60)
    print("  All tests passed.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
