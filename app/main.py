from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from app.api.calls import router as calls_router

app = FastAPI(
    title="CRM Call Recording Pipeline",
    description="Transcribe and summarize call recordings via Gemini 3.6 Flash and Groq GPT-OSS 20B.",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)

app.include_router(calls_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/docs", include_in_schema=False)
async def swagger_ui() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CRM Pipeline — API Docs",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@4.18.3/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@4.18.3/swagger-ui.css",
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    app.openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.3",
    )
    return app.openapi_schema


app.openapi = custom_openapi
