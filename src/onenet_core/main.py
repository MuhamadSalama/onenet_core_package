from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import Request
from uuid import uuid4

from .exceptions import APIError, api_error_handler, http_exception_handler, validation_exception_handler
from .routers.auth import router_auth
from .routers.users import router_users
from .routers.roles import router_roles, router_permissions
from .routers.wallet import router_wallet
from .routers.meta import router_meta
from .routers.websocket import router_ws

# Middleware
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

def create_app() -> FastAPI:
    app = FastAPI(
        title="OneNet Bridge Demo Backend",
        description="Simulated Bridge utilities and mock OSOS APIs.",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(router_auth)
    app.include_router(router_users)
    app.include_router(router_roles)
    app.include_router(router_permissions)
    app.include_router(router_wallet)
    app.include_router(router_meta)
    app.include_router(router_ws)

    return app

app = create_app()
