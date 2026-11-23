import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def _normalize_database_url(url: str) -> str:
    """Supabase/Vercel-এর URL-কে SQLAlchemy + psycopg 3 যে আকারে চায় সেই আকারে আনে।"""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if not url.startswith("postgresql"):
        return url
    # Supabase integration কখনো `supa=` নামের একটা অতিরিক্ত parameter দেয়, driver সেটা চেনে না
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "supa"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def get_database_url() -> str:
    """DATABASE_URL, না থাকলে POSTGRES_URL, না থাকলে লোকাল SQLite ফাইল।"""
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if url:
        return _normalize_database_url(url)

    # Vercel-এ শুধু /tmp-তে লেখা যায় (ডেটা স্থায়ী হয় না, তাই production-এ DATABASE_URL দিতে হবে)
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/supply_mart.db"

    path = Path(__file__).resolve().parent.parent / "supply_mart.db"
    return f"sqlite:///{path.as_posix()}"


class Settings:
    """সব গোপন মান ও সেটিং এক জায়গায়, environment variable থেকে।"""

    def __init__(self) -> None:
        on_vercel = bool(os.getenv("VERCEL"))
        # লোকালে সুবিধার জন্য dev মান আছে; production-এ না দিলে সরাসরি থেমে যায় (নিরাপত্তার জন্য)
        self.jwt_secret = os.getenv("JWT_SECRET") or ("" if on_vercel else "dev-only-jwt-secret-change-me-0123456789abcdef")
        self.pepper = os.getenv("PEPPER") or ("" if on_vercel else "dev-only-pepper")
        if on_vercel and (len(self.jwt_secret) < 32 or not self.pepper):
            raise RuntimeError("Vercel-এ JWT_SECRET (৩২+ অক্ষর) আর PEPPER বসাতে হবে")
        self.access_token_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
        self.refresh_token_days = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
        self.cookie_secure = os.getenv("COOKIE_SECURE", "1" if on_vercel else "0") == "1"
        extra = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
        self.cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173", *extra]
        # পুরনো refresh token এই কয়েক সেকেন্ডের মধ্যে আবার এলে এটা দুই ট্যাবের দৌড় ধরে নিই (চুরি না)
        self.reuse_grace_seconds = int(os.getenv("REUSE_GRACE_SECONDS", "10"))
        self.max_failed_logins = 5
        self.lockout_minutes = 15


settings = Settings()
