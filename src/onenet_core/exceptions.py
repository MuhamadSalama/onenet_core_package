from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any

class APIError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


async def api_error_handler(request: Request, exc: APIError):
    request_id = getattr(request.state, "request_id", None)
    payload = {
        "success": False,
        "error_code": exc.error_code,
        "message": exc.message,
        "request_id": request_id,
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    # If detail is dict with error_code, keep it. Otherwise build a generic one.
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        payload = exc.detail
        if "success" not in payload:
            payload["success"] = False
    else:
        payload = {
            "success": False,
            "error_code": "HTTP_ERROR",
            "message": str(exc.detail) if exc.detail else "An error occurred",
        }
    payload["request_id"] = request_id
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    request_id = getattr(request.state, "request_id", None)

    errors = []
    if hasattr(exc, "errors"):
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
            errors.append(
                {"field": field, "message": error["msg"], "type": error["type"]}
            )

    payload = {
        "success": False,
        "error_code": "VAL-001",
        "message": "Validation error: Please check your input data",
        "details": errors,
        "request_id": request_id,
    }
    return JSONResponse(status_code=422, content=payload)
