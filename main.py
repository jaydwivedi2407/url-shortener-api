
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field


DATABASE = "urls.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                clicks INTEGER NOT NULL DEFAULT 0,
                last_clicked TEXT
            )
        """)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="URL Shortener API",
    lifespan=lifespan
)


class LinkRequest(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, min_length=3, max_length=30)
    expires_at: datetime | None = None


def utc_now():
    return datetime.now(timezone.utc)


def normalize_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@app.get("/")
def home():
    return {"message": "URL Shortener API is running"}


@app.post("/links", status_code=201)
def create_link(data: LinkRequest):
    original_url = str(data.url)
    parsed = urlparse(original_url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=422, detail="A valid HTTP or HTTPS URL is required")

    expires = normalize_datetime(data.expires_at)

    if expires is not None and expires <= utc_now():
        raise HTTPException(status_code=422, detail="Expiry must be in the future")

    code = data.alias or uuid4().hex[:7]
    created = utc_now().isoformat()

    try:
        with get_db() as db:
            db.execute(
                """INSERT INTO links
                   (code, original_url, created_at, expires_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    code,
                    original_url,
                    created,
                    expires.isoformat() if expires else None
                )
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This alias or code already exists"
        )

    return {
        "code": code,
        "short_url": f"http://127.0.0.1:8000/{code}",
        "original_url": original_url,
        "expires_at": expires.isoformat() if expires else None
    }


@app.get("/{code}/stats")
def link_stats(code: str):
    with get_db() as db:
        link = db.execute(
            "SELECT * FROM links WHERE code = ?", (code,)
        ).fetchone()

    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")

    return {
        "code": link["code"],
        "original_url": link["original_url"],
        "clicks": link["clicks"],
        "last_clicked": link["last_clicked"],
        "expires_at": link["expires_at"]
    }


@app.get("/{code}")
def redirect_link(code: str):
    with get_db() as db:
        link = db.execute(
            "SELECT * FROM links WHERE code = ?", (code,)
        ).fetchone()

        if link is None:
            raise HTTPException(status_code=404, detail="Short link not found")

        expires_at = (
            datetime.fromisoformat(link["expires_at"])
            if link["expires_at"] else None
        )

        if expires_at and normalize_datetime(expires_at) <= utc_now():
            raise HTTPException(status_code=410, detail="This short link has expired")

        db.execute(
            "UPDATE links SET clicks = clicks + 1, last_clicked = ? WHERE code = ?",
            (utc_now().isoformat(), code)
        )

    return RedirectResponse(url=link["original_url"], status_code=307)
