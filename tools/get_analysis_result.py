from typing import Any

from flux_analysis_agent.core import analysis_engine
from flux_analysis_agent.core.data_store import DataStore
from flux_analysis_agent import config

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "data_id": {
            "type": "string",
            "description": "The identifier of the dataset to analyze (as returned by upload_data).",
        },
        "only_significant": {
            "type": "boolean",
            "description": "If true, only include variances that exceed the defined threshold in the results.",
            "default": False,
        },
    },
    "required": ["data_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "variances": {
            "type": "array",
            "description": "List of variance analysis results for each record (e.g. each account).",
            "items": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string"},
                    "account_name": {"type": "string"},
                    "category": {"type": "string"},
                    "current_period_amount": {"type": "number"},
                    "prior_period_amount": {"type": "number"},
                    "change_amount": {
                        "type": "number",
                        "description": "Difference = current - prior",
                    },
                    "change_percent": {
                        "type": "number",
                        "description": "Percentage change from prior to current",
                        "nullable": True,
                    },
                    "exceeds_threshold": {
                        "type": "boolean",
                        "description": "True if the change meets/exceeds the significance threshold",
                    },
                    "je_details": {
                        "type": "string",
                        "description": "Any journal entry details or notes",
                        "nullable": True,
                    },
                    "operational_drivers": {
                        "type": "string",
                        "description": "Any provided drivers/explanations for the change",
                        "nullable": True,
                    },
                },
                "required": [
                    "account_id",
                    "current_period_amount",
                    "prior_period_amount",
                    "change_amount",
                    "exceeds_threshold",
                ],
            },
        }
    },
    "required": ["variances"],
}


async def handle(
    data_id: str,
    only_significant: bool,
    store: DataStore,
) -> dict[str, Any]:
    try:
        dataset = store.get_data(data_id)
        if not dataset:
            return {"error": {"message": "No dataset found for the given data_id."}}

        variances = analysis_engine.compute_flux(
            dataset["data"],
            {
                "only_significant": only_significant,
                "default_threshold_percent": config.DEFAULT_THRESHOLD_PERCENT,
            },
        )
        return {"variances": variances}
    except Exception as exc:
        return {"error": {"message": f"Failed to compute analysis: {exc}"}}