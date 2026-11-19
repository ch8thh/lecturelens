"""App entry point: creates the FastAPI app, CORS, error handlers, and registers ALL routers.

Every router is mounted under /api, so a route written as "/chat" is served at /api/chat.
Person B only edits their own files in routes/ - this file already includes their stubs."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .claude_client import AppError
from .routes import audio, chat, concepts, flashcards, image, quiz, synthesize

app = FastAPI(title="LectureLens AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (image, synthesize, chat, audio, flashcards, quiz, concepts):
    app.include_router(module.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


# All errors leave the server in the same {"error": {"code", "message"}} shape.
@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return _error(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(p) for p in first.get("loc", []))
    return _error(422, "invalid_request", f"Invalid request ({where}): {first.get('msg', 'bad input')}")


@app.exception_handler(StarletteHTTPException)
async def http_handler(_: Request, exc: StarletteHTTPException):
    return _error(exc.status_code, "http_error", str(exc.detail))
