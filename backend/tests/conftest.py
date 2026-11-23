import itertools
import os
import tempfile

# প্রতিটি টেস্ট রান আলাদা ডেটাবেস ফাইল ব্যবহার করে, আসল ডেটায় হাত পড়ে না
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ.pop("VERCEL", None)
os.environ["REUSE_GRACE_SECONDS"] = "0"  # টেস্টে reuse সাথে সাথে ধরা পড়ুক

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.auth.models import User  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import engine  # noqa: E402
from main import app  # noqa: E402

PASSWORD = "Passw0rd123"
_counter = itertools.count(1)


class Actor:
    """একজন লগইন করা ব্যবহারকারী, নিজের আলাদা cookie সহ।"""

    def __init__(self, role: str = "user"):
        self.client = TestClient(app)
        self.email = f"user{next(_counter)}@test.com"
        r = self.client.post("/api/v1/auth/signup", json={"email": self.email, "name": "Test User", "password": PASSWORD})
        assert r.status_code == 201, r.text
        self.id = r.json()["id"]
        if role == "admin":
            with Session(engine) as s:
                u = s.get(User, self.id)
                u.role = "admin"
                s.add(u)
                s.commit()
        self.login()

    def login(self):
        r = self.client.post("/api/v1/auth/login", json={"email": self.email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        self.token = r.json()["access_token"]
        return r

    @property
    def h(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, **kw):
        return self.client.get(url, headers=self.h, **kw)

    def post(self, url, json=None, **kw):
        return self.client.post(url, json=json, headers=self.h, **kw)

    def patch(self, url, json=None, **kw):
        return self.client.patch(url, json=json, headers=self.h, **kw)

    def delete(self, url, **kw):
        return self.client.delete(url, headers=self.h, **kw)


@pytest.fixture
def make():
    return Actor


@pytest.fixture
def anon():
    return TestClient(app)


def product_body(**over):
    body = {"name_bn": "টেস্ট পণ্য", "category_id": 1, "unit": "kg", "price": 50, "stock": 5}
    body.update(over)
    return body


def forged_token(user_id: int, secret: str | None = None, minutes: int = 15) -> str:
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "role": "admin", "iat": now, "exp": now + timedelta(minutes=minutes)},
                      secret or settings.jwt_secret, algorithm="HS256")


def user_row(user_id: int) -> User:
    with Session(engine) as s:
        return s.exec(select(User).where(User.id == user_id)).one()
