import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.catalog.router import router as catalog_router

logger = logging.getLogger("supply_mart")

# vercel.json /api/* এই backend-এ পাঠায়, তাই docs-ও /api/docs-এ রাখা হয়েছে
app = FastAPI(
    title="Supply Mart API",
    description="মুদির পণ্য ও ক্যাটাগরির REST API (MVP)",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.include_router(catalog_router)


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