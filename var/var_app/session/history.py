import json

from pydantic_ai.messages import ModelMessage


def load_history(messages: list[dict]) -> list[ModelMessage]:
    if not messages:
        return []

    for msg in reversed(messages):
        raw = msg.get("model_messages_json", "[]")
        if raw and raw != "[]":
            try:
                data = json.loads(raw)
                result = []
                for m in data:
                    try:
                        result.append(ModelMessage.model_validate(m))
                    except Exception:
                        pass
                if result:
                    return result
            except Exception:
                pass
    return []


def serialize_msg(msg):
    if hasattr(msg, "model_dump"):
        return msg.model_dump()
    return str(msg)
