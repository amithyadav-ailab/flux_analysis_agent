import json
from typing import Any

from flux_analysis_agent import config
from flux_analysis_agent.core import analysis_engine
from flux_analysis_agent.core.data_store import DataStore
from flux_analysis_agent.core.llm_manager import LLMManager

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "data_id": {
            "type": "string",
            "description": "Identifier of the dataset to analyze (from upload_data).",
        },
        "query": {
            "type": "string",
            "description": "The user's question or request regarding the data.",
        },
    },
    "required": ["data_id", "query"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {
            "type": "string",
            "description": "A detailed answer or explanation addressing the query.",
        }
    },
    "required": ["explanation"],
}


async def handle(
    data_id: str,
    query: str,
    store: DataStore,
    llm: LLMManager | None,
) -> dict[str, Any]:
    if not llm:
        return {"error": {"message": "LLM is not configured on the server."}}

    try:
        dataset = store.get_data(data_id)
        if not dataset:
            return {"error": {"message": "No dataset found for the given data_id."}}

        data = dataset["data"]
        meta = dataset.get("meta", {})
        variances = analysis_engine.compute_flux(
            data,
            {
                "only_significant": False,
                "default_threshold_percent": config.DEFAULT_THRESHOLD_PERCENT,
            },
        )

        summary = _summarize_variances(variances)
        schema_summary = meta.get("schema_description") or meta.get("schema_summary")

        messages = _build_messages(query, schema_summary, meta.get("columns", []), summary)
        tools = [_compute_flux_tool_schema()]

        response = llm.chat(messages, tools=tools)
        message = llm.extract_message(response)

        if getattr(message, "tool_calls", None):
            tool_messages = _handle_tool_calls(message.tool_calls, data)
            messages.extend(tool_messages)
            response = llm.chat(messages, tools=tools)
            message = llm.extract_message(response)

        explanation = (message.content or "").strip()
        if not explanation:
            return {"error": {"message": "LLM returned an empty response."}}

        return {"explanation": explanation}
    except Exception as exc:
        return {"error": {"message": f"Analysis agent is currently unavailable. {exc}"}}


def _build_messages(
    query: str,
    schema_summary: str | None,
    columns: list[str],
    variance_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    system_prompt = (
        "You are an AI financial analyst. Use only the data provided. "
        "Do not invent causes. If a reason is not in the data, say it is not provided. "
        "Answer clearly and concisely."
    )

    user_parts = [f"User question: {query}"]
    if schema_summary:
        user_parts.append(f"Schema summary: {schema_summary}")
    if columns:
        user_parts.append(f"Columns: {', '.join(columns)}")
    if variance_summary:
        user_parts.append(f"Top variances (JSON): {json.dumps(variance_summary)}")

    user_prompt = "\n".join(user_parts)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _summarize_variances(variances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not variances:
        return []

    sorted_variances = sorted(
        variances,
        key=lambda item: abs(item.get("change_amount") or 0),
        reverse=True,
    )
    top_variances = sorted_variances[:5]
    summary = []
    for item in top_variances:
        summary.append(
            {
                "account_id": item.get("account_id"),
                "account_name": item.get("account_name"),
                "category": item.get("category"),
                "change_amount": item.get("change_amount"),
                "change_percent": item.get("change_percent"),
                "exceeds_threshold": item.get("exceeds_threshold"),
                "je_details": item.get("je_details"),
                "operational_drivers": item.get("operational_drivers"),
            }
        )
    return summary


def _compute_flux_tool_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "compute_flux",
            "description": "Compute period-over-period changes for the dataset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "only_significant": {
                        "type": "boolean",
                        "description": "Return only entries exceeding thresholds.",
                    }
                },
                "required": [],
            },
        },
    }


def _handle_tool_calls(tool_calls: list[Any], data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    tool_call_entries: list[dict[str, Any]] = []
    tool_messages: list[dict[str, Any]] = []

    for call in tool_calls:
        name = call.function.name
        if name != "compute_flux":
            continue
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}

        only_significant = bool(args.get("only_significant", False))
        variances = analysis_engine.compute_flux(
            data,
            {
                "only_significant": only_significant,
                "default_threshold_percent": config.DEFAULT_THRESHOLD_PERCENT,
            },
        )
        result_payload = json.dumps({"variances": variances})

        tool_call_entries.append(
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": call.function.arguments,
                },
            }
        )
        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "content": result_payload,
            }
        )

    if tool_call_entries:
        messages.append({"role": "assistant", "tool_calls": tool_call_entries})
        messages.extend(tool_messages)

    return messages
