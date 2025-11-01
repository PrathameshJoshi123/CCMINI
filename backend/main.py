from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.routers import auth, users, documents, chat
import logging
import sys

# Basic logging configuration so module logs are visible when running uvicorn
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler to prevent binary data from being included in error responses.
    This prevents UnicodeDecodeError when FastAPI tries to serialize binary content.
    """
    # Sanitize error details to remove potentially problematic binary content
    sanitized_errors = []
    for error in exc.errors():
        sanitized_error = error.copy()
        # Remove input field if it might contain binary data
        if 'input' in sanitized_error and isinstance(sanitized_error['input'], (bytes, bytearray)):
            sanitized_error['input'] = '<binary data omitted>'
        elif 'input' in sanitized_error and isinstance(sanitized_error['input'], str):
            # Truncate very long strings that might contain binary data
            if len(sanitized_error['input']) > 1000:
                sanitized_error['input'] = sanitized_error['input'][:500] + '... <truncated>'
        sanitized_errors.append(sanitized_error)
    
    return JSONResponse(
        status_code=422,
        content={"detail": sanitized_errors}
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to NotesLLM API"}
