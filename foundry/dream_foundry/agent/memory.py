async def embed_text(text: str) -> bytes:
    import struct
    from dream_foundry.config import settings

    try:
        from pydantic_ai.direct import model_request_sync
    except ImportError:
        pass

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=settings.embedding_dimensions,
        )
        embedding = response.data[0].embedding
        return struct.pack(f"{len(embedding)}f", *embedding)
    except Exception:
        dim = settings.embedding_dimensions
        return struct.pack(f"{dim}f", *([0.0] * dim))
