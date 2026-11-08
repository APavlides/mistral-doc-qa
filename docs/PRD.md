# PRD: Document Q&A (simple RAG)

## Goal

Let a user paste or upload some text, ask a question, and get an answer grounded in that text.

## User

Someone with a text document who wants quick answers without reading all of it.

## Core flow

1. User pastes text (or uploads a `.txt` file) and clicks "Save document".
2. Backend splits the text into chunks, embeds them with Mistral, and saves them to a JSON file (M6: SQLite replaces the JSON file).
3. User types a question and clicks "Ask".
4. Backend embeds the question, ranks chunks by cosine similarity, and takes the top 3.
5. Backend sends those chunks plus the question to a Mistral chat model.
6. Frontend shows the answer (and the chunks used).

## Out of scope

- Vector database, Docker, auth, tests, styling.
- Multiple documents or per-user documents (one document at a time; a new upload replaces it).
- Streaming the answer (unless the interviewer asks).
- PDF/DOCX parsing, OCR.
- Chat history or follow-up questions.
- Re-ranking, hybrid search, smart chunking (sentence/semantic).
- M6: ORMs, migrations, SQLite vector extensions (similarity stays in plain Python), copying old `doc.json` data into SQLite (just re-save the document).

## Endpoints and data

- `GET /api/health` (exists).
- `POST /api/documents` body `{text}` returns `{chunk_count}`. Chunks, embeds, writes `backend/data/doc.json` (M6: writes to SQLite instead).
- `POST /api/ask` body `{question}` returns `{answer, sources: [chunk text]}`. Returns 404 if no document saved.
- Data: `backend/data/doc.json` = `{"chunks": [{"text": str, "embedding": [float]}]}`. Loaded into a Python list on each request (or at startup), so `--reload` loses nothing. Cosine similarity in plain Python.
- M6: data moves to `backend/data/doc.db` (standard-library `sqlite3`, no new dependency). One table `chunks(id INTEGER PRIMARY KEY, text TEXT, embedding TEXT)`, with the embedding stored as a JSON string. A save deletes all rows and inserts the new ones in one transaction, so a new upload replaces the old document. Ask loads the rows into a Python list and ranks them with the same cosine function. API shapes do not change.
- One shared async Mistral client, created in the FastAPI lifespan. Models: `mistral-embed` and a small chat model.

## Milestones

- [x] **M1: thinnest slice (~5 min).** Page with a textarea for the document, an input for the question and an Ask button. `POST /api/ask` takes `{document, question}`, sends both whole to Mistral chat, and returns `{answer}`. Frontend shows loading, error and the answer.
      Done when: pasting a short text and asking about it shows a correct answer, and the `curl` works.
- [x] **M2: chunk, embed, save (~5 min).** `POST /api/documents` chunks the text (about 800 characters, 100 overlap), embeds the chunks in one call, and writes `data/doc.json`.
      Done when: `curl` returns `chunk_count`, and `doc.json` holds chunks with embeddings that survive a `--reload`.
- [x] **M3: retrieve (~5 min).** `POST /api/ask` takes only `{question}`: embed it, rank the saved chunks by cosine similarity, and answer from the top 3. Return `sources`.
      Done when: a question about a detail deep in a long text is answered correctly, and `sources` contains the matching chunk.
- [x] **M4: frontend wiring (~5 min).** "Save document" button calls `/api/documents` and shows the chunk count. Ask uses the new `/api/ask`. Add a `.txt` file upload that fills the textarea. Show the sources under the answer, and an empty state when no document is saved.
      Done when: the full flow works in the browser (paste or upload, save, ask, answer with sources).
- [x] **M5: hardening (~5 min).** Timeouts and SDK retry config on Mistral calls (429, 5xx, timeouts only). Map errors: 429 passed through, 502 or 504 for other upstream failures, 404 if no document, 422 for empty text.
      Done when: a bad API key and an empty document each give a clear error in the UI instead of a crash.
- [x] **M6: SQLite storage (~5 min).** Add `save_chunks(chunks)` and `load_chunks()` helpers using `sqlite3` and `backend/data/doc.db`. They create the `chunks` table if missing, and save replaces all rows in one transaction. `POST /api/documents` and `POST /api/ask` use them instead of `doc.json`. Request and response shapes are unchanged, so the frontend is untouched.
  Done when: the save `curl` returns `chunk_count`, `sqlite3 backend/data/doc.db "select count(*) from chunks"` shows the same number, and the ask `curl` still answers with `sources`, also after a `--reload`.
- [x] **M7: remove doc.json (~5 min).** Create the table once in the FastAPI lifespan, delete the `doc.json` code and constant, delete the old `doc.json` file, and make an empty `chunks` table return the existing 404.
  Done when: saving a second, different document leaves only its chunks in the table, a fresh empty database returns 404 "No document saved yet" from ask, and no reference to `doc.json` remains in `main.py`.

## Open questions

1. **Stream the answer?** _Ask._ Default: no, return the full answer at once (simpler, saves about 5 minutes).
2. **Which file types for upload?** _Ask._ Default: `.txt` only, read in the browser and put in the textarea.
3. **Chunk size and top-k?** _I decide._ Default: about 800 characters with 100 overlap, top 3.
