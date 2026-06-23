from fastapi import APIRouter
from var_app.model.registry import list_models, MODEL_REGISTRY

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def get_models():
    models = list_models()
    return [
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


@router.get("/active")
async def get_active_model():
    from var_app.config import settings

    model_id = settings.default_model
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        info = list(MODEL_REGISTRY.values())[0]
        model_id = info.id

    return {
        "model_id": model_id,
        "provider": info.provider,
    }
