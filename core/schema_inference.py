import json
from typing import Any

from flux_analysis_agent.core.llm_manager import LLMManager


def infer_schema(
    columns: list[str],
    sample_rows: list[dict[str, Any]],
    llm: LLMManager | None,
) -> dict[str, Any]:
    if not llm:
        return _heuristic_schema(columns, sample_rows)

    prompt = _build_prompt(columns, sample_rows)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a data schema analyzer. Respond with JSON only, "
                "using keys description and column_types."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response = llm.chat(messages)
    message = llm.extract_message(response)
    content = message.content or ""

    try:
        parsed = llm.parse_json(content)
        return _normalize_schema(parsed, columns)
    except Exception:
        return _heuristic_schema(columns, sample_rows)


def _build_prompt(columns: list[str], sample_rows: list[dict[str, Any]]) -> str:
    sample_preview = sample_rows[:3]
    return (
        "We have a table with columns: "
        f"{', '.join(columns)}. "
        "Here are sample rows (JSON): "
        f"{json.dumps(sample_preview)}. "
        "Explain the schema and identify the role/type of each column."
    )


def _normalize_schema(parsed: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    description = str(parsed.get("description", "")).strip()
    column_types = parsed.get("column_types", {})
    if not isinstance(column_types, dict):
        column_types = {}

    normalized = {"description": description, "column_types": {}}
    for column in columns:
        value = column_types.get(column)
        if value is None:
            value = _guess_type_from_name(column)
        normalized["column_types"][column] = str(value)

    return normalized


def _heuristic_schema(columns: list[str], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    column_types: dict[str, str] = {}
    for column in columns:
        column_types[column] = _guess_type_from_samples(column, sample_rows)

    description = f"Dataset with {len(columns)} columns: {', '.join(columns)}."
    return {"description": description, "column_types": column_types}


def _guess_type_from_samples(column: str, sample_rows: list[dict[str, Any]]) -> str:
    values = [row.get(column) for row in sample_rows]
    numeric_hits = 0
    total = 0
    for value in values:
        if value is None:
            continue
        total += 1
        if _is_numeric(value):
            numeric_hits += 1

    if total > 0 and numeric_hits == total:
        return "numeric"

    return _guess_type_from_name(column)


def _guess_type_from_name(column: str) -> str:
    name = column.lower()
    if "id" in name:
        return "identifier"
    if "date" in name or "period" in name:
        return "date"
    if any(token in name for token in ["amount", "value", "balance", "price", "cost", "rate", "percent", "pct", "threshold"]):
        return "numeric"
    return "text"


def _is_numeric(value: Any) -> bool:
    try:
        float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return False
    return True