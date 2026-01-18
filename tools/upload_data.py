from typing import Any

from flux_analysis_agent.core import schema_inference
from flux_analysis_agent.core.data_store import DataStore
from flux_analysis_agent.core.llm_manager import LLMManager

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "csv_data": {
            "type": "string",
            "description": "The dataset content in CSV format (including header row).",
        },
        "data_name": {
            "type": "string",
            "description": "Optional name/label for the dataset for reference.",
            "examples": ["Q1 Financials", "Sales Data 2025"],
        },
    },
    "required": ["csv_data"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "data_id": {
            "type": "string",
            "description": "Identifier to use for referencing this dataset in subsequent calls.",
        },
        "columns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of column names detected from the header.",
        },
        "schema_summary": {
            "type": "string",
            "description": "Optional natural language summary of the dataset schema or contents.",
        },
    },
    "required": ["data_id", "columns"],
}


async def handle(
    csv_data: str,
    data_name: str | None,
    store: DataStore,
    llm: LLMManager | None,
) -> dict[str, Any]:
    try:
        data_id = store.add_data(csv_data, data_name=data_name)
        dataset = store.get_data(data_id)
        if not dataset:
            return {"error": {"message": "Failed to store dataset."}}

        meta = dataset.get("meta", {})
        columns = meta.get("columns", [])

        schema_summary = None
        if llm:
            schema_info = schema_inference.infer_schema(columns, dataset["data"][:5], llm)
            store.set_schema(data_id, {
                "schema_description": schema_info.get("description"),
                "column_types": schema_info.get("column_types"),
            })
            schema_summary = schema_info.get("description")

        result: dict[str, Any] = {"data_id": data_id, "columns": columns}
        if schema_summary:
            result["schema_summary"] = schema_summary
        return result
    except Exception as exc:
        return {"error": {"message": f"Failed to upload data: {exc}"}}