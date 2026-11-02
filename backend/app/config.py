import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def _normalize_database_url(url: str) -> str:
    """Supabase/Vercel-এর URL-কে SQLAlchemy + psycopg 3 যে আকারে চায় সেই আকারে আনে।"""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
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