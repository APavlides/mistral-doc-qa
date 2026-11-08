import json
import os
import sqlite3
from contextlib import asynccontextmanager, closing
from pathlib import Path

import httpx2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from mistralai.client import Mistral
from mistralai.client.errors import MistralError
from mistralai.client.utils import BackoffStrategy, RetryConfig
from pydantic import BaseModel

load_dotenv()

MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
EMBED_MODEL = os.getenv("MISTRAL_EMBED_MODEL", "mistral-embed")
DB_PATH = Path(__file__).parent / "data" / "doc.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # One shared Mistral client for the whole app.
    # The SDK retries only 429, 5xx and timeouts, with backoff and jitter (ms).
    app.state.mistral = Mistral(
        api_key=os.environ["MISTRAL_API_KEY"],
        timeout_ms=20_000,
        retry_config=RetryConfig(
            "backoff",
            BackoffStrategy(
                initial_interval=500,
                max_interval=5_000,
                exponent=2.0,
                max_elapsed_time=30_000,
                jitter_ms=250,
            ),
            retry_connection_errors=True,
        ),
    )
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(MistralError)
async def mistral_error_handler(request: Request, exc: MistralError):
    # Pass 429 through; any other upstream failure is a bad gateway
    if exc.status_code == 429:
        return JSONResponse(
            status_code=429, content={"detail": "Mistral rate limit hit, try again"}
        )
    return JSONResponse(
        status_code=502,
        content={"detail": f"Mistral request failed (upstream {exc.status_code})"},
    )


@app.exception_handler(httpx2.TimeoutException)
async def timeout_handler(request: Request, exc: httpx2.TimeoutException):
    return JSONResponse(status_code=504, content={"detail": "Mistral timed out"})


@app.exception_handler(httpx2.TransportError)
async def transport_handler(request: Request, exc: httpx2.TransportError):
    return JSONResponse(status_code=502, content={"detail": "Could not reach Mistral"})


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


class DocumentRequest(BaseModel):
    text: str


class DocumentResponse(BaseModel):
    chunk_count: int


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    # Slide a window of `size` characters, stepping back `overlap` each time
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    # 1.0 = same direction (same meaning), 0.0 = unrelated
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


def init_db() -> None:
    # Called once at startup from the lifespan
    DB_PATH.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS chunks "
            "(id INTEGER PRIMARY KEY, text TEXT, embedding TEXT)"
        )


def get_db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def save_chunks(chunks: list[dict]) -> None:
    # Replace the whole document in one transaction (the inner `with db` commits)
    with closing(get_db()) as db, db:
        db.execute("DELETE FROM chunks")
        db.executemany(
            "INSERT INTO chunks (text, embedding) VALUES (?, ?)",
            [(c["text"], json.dumps(c["embedding"])) for c in chunks],
        )


def load_chunks() -> list[dict]:
    with closing(get_db()) as db:
        rows = db.execute("SELECT text, embedding FROM chunks ORDER BY id").fetchall()
    return [{"text": text, "embedding": json.loads(emb)} for text, emb in rows]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
async def ask(body: AskRequest, request: Request):
    chunks = load_chunks()
    if not chunks:
        raise HTTPException(status_code=404, detail="No document saved yet")

    mistral = request.app.state.mistral
    emb = await mistral.embeddings.create_async(
        model=EMBED_MODEL, inputs=[body.question]
    )
    q_vec = emb.data[0].embedding

    # Rank every chunk by similarity to the question and keep the best 3
    top = sorted(
        chunks, key=lambda c: cosine_similarity(q_vec, c["embedding"]), reverse=True
    )[:3]
    sources = [c["text"] for c in top]

    context = "\n\n---\n\n".join(sources)
    res = await mistral.chat.complete_async(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Answer the question using only the excerpts. "
                "If the answer is not in the excerpts, say so.",
            },
            {
                "role": "user",
                "content": f"Excerpts:\n{context}\n\nQuestion: {body.question}",
            },
        ],
    )
    return AskResponse(answer=res.choices[0].message.content, sources=sources)


@app.post("/api/documents", response_model=DocumentResponse)
async def save_document(body: DocumentRequest, request: Request):
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Document text is empty")
    chunks = chunk_text(body.text)
    res = await request.app.state.mistral.embeddings.create_async(
        model=EMBED_MODEL, inputs=chunks
    )
    saved = [
        {"text": chunk, "embedding": item.embedding}
        for chunk, item in zip(chunks, res.data)
    ]
    save_chunks(saved)
    return DocumentResponse(chunk_count=len(saved))
