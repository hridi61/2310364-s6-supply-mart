import logging
import os
import sys
from pathlib import Path

# Vercel পুরো repo থেকে চালালেও `app` প্যাকেজ যেন পাওয়া যায়
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.catalog.router import router as catalog_router
from app.config import settings
from app.groups.router import router as groups_router

logger = logging.getLogger("supply_mart")

# vercel.json /api/* এই backend-এ পাঠায়, তাই docs-ও /api/docs-এ রাখা হয়েছে
app = FastAPI(
    title="Supply Mart API",
    description="Supply Mart: JWT auth, RBAC, গ্রুপ-অনুমতি ও অ্যাডমিন ড্যাশবোর্ডসহ REST API",
    version="0.2.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

# CORS: শুধু আমাদের frontend-এর origin (কোনো `*` নেই)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count", "Content-Disposition"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(groups_router)
app.include_router(admin_router)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    # আসল কারণ শুধু log-এ যায়, ব্যবহারকারীকে ডেটাবেসের তথ্য দেখানো হয় না
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# লোকালে `npm run build`-এর পর localhost:8000-এও সাইট দেখা যায়। Vercel-এ এই ফোল্ডার থাকে না।
_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
