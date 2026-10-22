import hashlib
import json
import os
from pathlib import Path

import chromadb
from google import genai
from google.genai import types
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
MIN_SCORE = 0.35
EMBED_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-2.5-flash"

_collection = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db")).get_or_create_collection(
    name="docs", metadata={"hnsw:space": "cosine"}
)
_client = None


def _get_client():
    """Create the Gemini SDK client only when a Gemini operation is requested."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Set the GEMINI_API_KEY environment variable to use Gemini.")
        _client = genai.Client(api_key=api_key)
    return _client


def chunk(text, size=800, overlap=150):
    if size <= 0:
        raise ValueError("size must be greater than zero")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be non-negative and smaller than size")

    chunks = []
    step = size - overlap
    for start in range(0, len(text), step):
        chunks.append(text[start:start + size])
    return chunks


def _source_name(file_or_path):
    name = getattr(file_or_path, "name", file_or_path)
    return Path(str(name)).name


def _extract(file_or_path):
    """Return page-numbered text for a path or Django-style uploaded file."""
    source_name = _source_name(file_or_path)
    owns_stream = isinstance(file_or_path, (str, os.PathLike))
    stream = open(file_or_path, "rb") if owns_stream else file_or_path
    try:
        if source_name.lower().endswith(".pdf"):
            reader = PdfReader(stream)
            return [(page.extract_text() or "", page_number)
                    for page_number, page in enumerate(reader.pages, start=1)]
        if source_name.lower().endswith(".txt"):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            return [(content, 1)]
        raise ValueError(f"Unsupported knowledge-base file type: {source_name}")
    finally:
        if owns_stream:
            stream.close()


def _embed(texts):
    response = _get_client().models.embed_content(model=EMBED_MODEL, contents=texts)
    return [item.values for item in response.embeddings]


def ingest(file_or_path):
    """Extract, chunk, embed and store a PDF/TXT path or uploaded file."""
    source = _source_name(file_or_path)
    ids, documents, metadatas = [], [], []
    source_key = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    for text, page_number in _extract(file_or_path):
        for chunk_number, passage in enumerate(chunk(text)):
            ids.append(f"{source_key}-{page_number}-{chunk_number}")
            documents.append(passage)
            metadatas.append({"source": source, "page": page_number})

    for start in range(0, len(documents), 90):
        stop = start + 90
        batch_documents = documents[start:stop]
        _collection.upsert(
            ids=ids[start:stop],
            documents=batch_documents,
            metadatas=metadatas[start:stop],
            embeddings=_embed(batch_documents),
        )
    return len(documents)


def retrieve(query, k=5):
    result = _collection.query(query_embeddings=_embed([query]), n_results=k)
    documents = (result.get("documents") or [[]])[0] or []
    metadatas = (result.get("metadatas") or [[]])[0] or []
    distances = (result.get("distances") or [[]])[0] or []
    hits = [
        {"text": text, "source": metadata["source"], "page": metadata["page"],
         "score": round(1 - distance, 3)}
        for text, metadata, distance in zip(documents, metadatas, distances)
    ]
    return [hit for hit in hits if hit["score"] >= MIN_SCORE]


_PROMPT = """You are a programming tutor. Use only the retrieved context for documentation claims. Do not invent documentation claims. If no relevant context was retrieved, set kb_coverage to "none". If context only partly covers the question, set it to "partial"; if it fully covers it, set it to "full".
Return valid JSON with exactly these keys:
- explanation: string
- issues: array of objects with line_hint, problem, and why
- corrected_code: string
- used_sources: array of retrieved source identifiers or numbers
- kb_coverage: "full", "partial", or "none"

Retrieved context:
{context}

Problem:
{problem}

Code:
{code}
"""


def explain(code, problem):
    hits = retrieve(f"{problem}\n{code}"[:2000])
    context = "\n\n".join(
        f"[{index + 1}] ({hit['source']}, page {hit['page']}, score {hit['score']})\n{hit['text']}"
        for index, hit in enumerate(hits)
    ) or "No relevant context was retrieved."
    response = _get_client().models.generate_content(
        model=LLM_MODEL,
        contents=_PROMPT.format(context=context, problem=problem, code=code),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return {"result": json.loads(response.text), "sources": hits}
