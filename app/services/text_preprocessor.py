from __future__ import annotations

from app.schemas import InputType

MODEL_PREFIX_RULES = {
    "intfloat/": {"query": "query: ", "document": "passage: "},
    "BAAI/bge": {"query": "", "document": ""},
}


def preprocess_texts(model_name: str, texts: list[str], input_type: InputType) -> list[str]:
    """Apply model-specific query/document prefixes in one service-owned place."""
    prefix = _prefix_for(model_name, input_type)
    return [f"{prefix}{text}" for text in texts]


def _prefix_for(model_name: str, input_type: InputType) -> str:
    for model_prefix, rules in MODEL_PREFIX_RULES.items():
        if model_name.startswith(model_prefix):
            return rules[input_type.value]
    return ""

