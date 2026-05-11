from fastapi import APIRouter
from dream_foundry.agent.registry import list_models

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def get_models():
    models = list_models()
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "provider_prefix": m.provider_prefix,
                "context_window": m.context_window,
                "max_output_tokens": m.max_output_tokens,
            }
            for m in models
        ]
    }


@router.get("/active")
async def get_active_model():
    from dream_foundry.agent.registry import MODEL_REGISTRY
    from dream_foundry.config import settings

    model_id = settings.default_model
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        info = list(MODEL_REGISTRY.values())[0]
        model_id = info.id

    return {
        "model_id": model_id,
        "provider": info.provider,
    }
