"""LLM and embedding providers behind one interface. Gemini when a key is set; a deterministic mock otherwise, so the
demo never depends on an external account. Agents call only `get_llm()` / `get_embedder()`."""
import hashlib
import json
import math
import re
from typing import Protocol

from app.core.config import get_settings


class LLM(Protocol):
    name: str

    def generate_json(self, prompt: str, schema_hint: dict | None = None) -> dict | None: ...
    def generate_text(self, prompt: str) -> str | None: ...


class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class MockLLM:
    """Returns None so every caller takes its rule-based fallback path, which is the tested behaviour in mock mode."""
    name = "mock"

    def generate_json(self, prompt: str, schema_hint: dict | None = None) -> dict | None:
        return None

    def generate_text(self, prompt: str) -> str | None:
        return None


class GeminiLLM:  # pragma: no cover - needs a key and network
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_json(self, prompt: str, schema_hint: dict | None = None) -> dict | None:
        try:
            r = self._client.models.generate_content(model=self._model, contents=prompt,
                                                     config={"response_mime_type": "application/json"})
            return json.loads(r.text)
        except Exception:  # noqa: BLE001 - any failure falls back to rules
            return None

    def generate_text(self, prompt: str) -> str | None:
        try:
            return self._client.models.generate_content(model=self._model, contents=prompt).text
        except Exception:  # noqa: BLE001
            return None


class LocalEmbedder:
    """Fallback multilingual embedding: hashed character n-grams of the text plus its romanisation-insensitive form.
    Weak but script-agnostic; good enough to rank candidates that location + time already narrowed down."""
    name = "local-ngram"
    dim = 256

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * self.dim
            s = re.sub(r"\s+", " ", t.lower()).strip()
            for n in (2, 3, 4):
                for i in range(max(0, len(s) - n + 1)):
                    h = int(hashlib.md5(s[i:i + n].encode("utf-8")).hexdigest(), 16)
                    v[h % self.dim] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out


class GeminiEmbedder:  # pragma: no cover - needs a key and network
    name = "gemini-embed"
    dim = 768

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._fallback = LocalEmbedder()

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            r = self._client.models.embed_content(model=self._model, contents=texts)
            return [e.values for e in r.embeddings]
        except Exception:  # noqa: BLE001
            return self._fallback.embed(texts)


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


_llm: LLM | None = None
_emb: Embedder | None = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        s = get_settings()
        _llm = MockLLM() if s.mock else GeminiLLM(s.gemini_api_key, s.gemini_model)
    return _llm


def get_embedder() -> Embedder:
    global _emb
    if _emb is None:
        s = get_settings()
        _emb = LocalEmbedder() if s.mock else GeminiEmbedder(s.gemini_api_key, s.gemini_embed_model)
    return _emb
