from foundry_app.config import settings


def resolve_api_key(provider: str) -> str:
    if provider == "openai":
        return settings.openai_api_key
    elif provider == "anthropic":
        return settings.anthropic_api_key
    return ""


def create_model_client(model_string: str, provider: str, api_key: str, base_url: str):
    model_name = model_string.split(":", 1)[-1] if ":" in model_string else model_string
    if provider == "anthropic":
        try:
            from anthropic import AsyncAnthropic
            from pydantic_ai.models.anthropic import AnthropicModel
            from pydantic_ai.providers.anthropic import AnthropicProvider

            if base_url:
                client = AsyncAnthropic(base_url=base_url, api_key=api_key)
                provider_obj = AnthropicProvider(anthropic_client=client)
            else:
                provider_obj = AnthropicProvider(api_key=api_key)
            return AnthropicModel(model_name, provider=provider_obj)
        except Exception:
            import traceback
            traceback.print_exc()
            return model_string
    else:
        try:
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider

            provider_obj = OpenAIProvider(base_url=base_url, api_key=api_key)
            return OpenAIModel(model_name, provider=provider_obj)
        except Exception:
            import traceback
            traceback.print_exc()
            return model_string
