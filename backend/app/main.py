import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import models
from .database import engine
from .routers import auth as auth_router
from .routers import analysis as analysis_router
from .routers import profile as profile_router
from .routers import admin as admin_router

log = logging.getLogger("chroma")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Serverless Cloud Assistant for Contextual Color Analysis and Accessibility Support",
    version="0.2.0",
)

# Vite dev server (either spelling of "localhost") and the single-server
# production mode (frontend served by this app on :8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:8000", "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Errors: always answer with JSON {"detail": "..."} ---------------------
# The frontend shows `detail` to the user. Before, an unexpected crash returned
# plain-text "Internal Server Error", which the UI could only show as the
# useless "Something went wrong. Please try again."
@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x not in ("body", "query")]
        field = ".".join(loc)
        msg = str(err.get("msg", "Invalid value")).replace("Value error, ", "")
        parts.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Invalid request."})


@app.exception_handler(StarletteHTTPException)
async def http_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {type(exc).__name__}: {exc}"},
    )


app.include_router(auth_router.router)
app.include_router(analysis_router.router)
app.include_router(profile_router.router)
app.include_router(admin_router.router)

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_STORAGE_ROOT = os.path.join(_BACKEND_DIR, "storage")
os.makedirs(_STORAGE_ROOT, exist_ok=True)
app.mount("/storage", StaticFiles(directory=_STORAGE_ROOT), name="storage")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---- Offline / single-server mode -------------------------------------------
# If the frontend has been built (`npm run build` -> frontend/dist), this app
# serves it too, so the whole project runs from ONE process on
# http://localhost:8000 with no Node, no Vite and no internet needed.
_DIST = os.path.abspath(os.path.join(_BACKEND_DIR, "..", "frontend", "dist"))
if os.path.isfile(os.path.join(_DIST, "index.html")):
    _assets = os.path.join(_DIST, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith(("api/", "storage/")):
            return JSONResponse(status_code=404, content={"detail": "Not found."})
        candidate = os.path.abspath(os.path.join(_DIST, full_path))
        if full_path and candidate.startswith(_DIST + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_DIST, "index.html"))
