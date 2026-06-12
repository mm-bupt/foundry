from pydantic_ai.messages import ModelMessage

from foundry_app.agent.compaction import filter_compacted


async def trim_and_summarize(messages: list[ModelMessage]) -> list[ModelMessage]:
    return filter_compacted(messages)
