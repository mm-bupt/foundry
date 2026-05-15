import hashlib
import struct

from foundry_app.config import settings

_cache: dict[str, bytes] = {}


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


async def embed_text(text: str) -> bytes:
    key = _cache_key(text)
    if key in _cache:
        return _cache[key]

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=settings.embedding_dimensions,
        )
        embedding = response.data[0].embedding
        result = struct.pack(f"{len(embedding)}f", *embedding)
    except Exception:
        dim = settings.embedding_dimensions
        result = struct.pack(f"{dim}f", *([0.0] * dim))

    _cache[key] = result
    return result
