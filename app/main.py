from fastapi import FastAPI, Request

from app.api.calls import router as calls_router

app = FastAPI(
    title="CRM Call Recording Pipeline",
    description="Transcribe and summarize call recordings via Gemini 3.6 Flash and Groq GPT-OSS 20B.",
    version="2.0.0",
)

app.include_router(calls_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/{full_path:path}", tags=["debug"])
def catch_all(full_path: str, request: Request):
    return {"path_received": full_path, "url": str(request.url), "headers": dict(request.headers)}
