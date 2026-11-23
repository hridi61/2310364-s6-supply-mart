import logging
import threading
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_database_url

logger = logging.getLogger("supply_mart")

DATABASE_URL = get_database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Supabase transaction pooler (port 6543) prepared statement চালায় না,
    # আর pooling pooler নিজেই করে, তাই NullPool।
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )

_ready = False
_lock = threading.Lock()


def init_db() -> None:
    """টেবিল বানায় আর খালি থাকলে নমুনা ডেটা বসায়। প্রতি process-এ একবারই চলে।"""
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        # models import না করলে SQLModel টেবিলগুলো চেনে না
        from app.audit import models as _audit  # noqa: F401
        from app.auth import models as _auth  # noqa: F401
        from app.catalog import models  # noqa: F401
        from app.groups import models as _groups  # noqa: F401
        from app.migrate import ensure_columns
        from app.seed import seed_if_empty

        SQLModel.metadata.create_all(engine)
        ensure_columns(engine)
        with Session(engine) as session:
            seed_if_empty(session)
        _ready = True
        logger.info("Database ready")


def get_session() -> Iterator[Session]:
    # Vercel serverless-এ startup event ভরসাযোগ্য না, তাই প্রথম request-এই টেবিল তৈরি হয়
    init_db()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
