from fastapi import FastAPI

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
