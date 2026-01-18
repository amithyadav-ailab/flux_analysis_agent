from typing import Any

from flux_analysis_agent import config


def compute_flux(data: list[dict[str, Any]], options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    only_significant = False
    default_threshold_percent = config.DEFAULT_THRESHOLD_PERCENT
    if options:
        only_significant = bool(options.get("only_significant", False))
        default_threshold_percent = float(
            options.get("default_threshold_percent", default_threshold_percent)
        )

    results: list[dict[str, Any]] = []

    for row in data:
        current = _to_float(row.get("current_period_amount"))
        prior = _to_float(row.get("prior_period_amount"))
        if current is None or prior is None:
            continue

        change_amount = current - prior
        if prior == 0:
            change_percent = None
        else:
            change_percent = (change_amount / prior) * 100.0

        exceeds = _exceeds_threshold(
            change_amount,
            change_percent,
            row.get("threshold_type"),
            row.get("threshold_value"),
            default_threshold_percent,
        )

        result: dict[str, Any] = {
            "account_id": row.get("account_id"),
            "account_name": row.get("account_name"),
            "category": row.get("category"),
            "current_period_amount": current,
            "prior_period_amount": prior,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "exceeds_threshold": exceeds,
        }

        if "je_details" in row:
            result["je_details"] = row.get("je_details")
        if "operational_drivers" in row:
            result["operational_drivers"] = row.get("operational_drivers")

        if only_significant and not exceeds:
            continue
        results.append(result)

    return results


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace(",", "")
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = f"-{cleaned[1:-1]}"
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _exceeds_threshold(
    change_amount: float,
    change_percent: float | None,
    threshold_type: Any,
    threshold_value: Any,
    default_threshold_percent: float,
) -> bool:
    if threshold_type and threshold_value is not None:
        threshold = _to_float(threshold_value)
        if threshold is None:
            return False
        threshold_type_normalized = str(threshold_type).strip().lower()
        if threshold_type_normalized == "percentage" and change_percent is not None:
            return abs(change_percent) >= threshold
        if threshold_type_normalized == "absolute":
            return abs(change_amount) >= threshold
        return False

    if default_threshold_percent <= 0 or change_percent is None:
        return False

    return abs(change_percent) >= default_threshold_percent