import csv
import io
import uuid
from typing import Any


class DataStore:
    def __init__(self) -> None:
        self._datasets: dict[str, dict[str, Any]] = {}

    def add_data(self, csv_text: str, data_name: str | None = None) -> str:
        data = _parse_csv(csv_text)
        data_id = f"data-{uuid.uuid4().hex}"
        columns = list(data[0].keys()) if data else []
        meta: dict[str, Any] = {"columns": columns}
        if data_name:
            meta["data_name"] = data_name
        self._datasets[data_id] = {"data": data, "meta": meta}
        return data_id

    def get_data(self, data_id: str) -> dict[str, Any] | None:
        return self._datasets.get(data_id)

    def set_schema(self, data_id: str, schema_info: dict[str, Any]) -> None:
        dataset = self._datasets.get(data_id)
        if not dataset:
            return
        dataset["meta"].update(schema_info)


def _parse_csv(csv_text: str) -> list[dict[str, Any]]:
    if not csv_text or not csv_text.strip():
        raise ValueError("No CSV data provided.")

    csv_text = csv_text.strip()
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV header row is missing or invalid.")

    fieldnames = [_clean_header(name) for name in reader.fieldnames]
    reader.fieldnames = fieldnames

    rows: list[dict[str, Any]] = []
    for row in reader:
        cleaned = {key: _clean_value(value) for key, value in row.items()}
        rows.append(cleaned)

    if not rows:
        raise ValueError("CSV data has no rows.")

    return rows


def _clean_header(name: str | None) -> str:
    if not name:
        return ""
    name = name.strip()
    if name.startswith("\ufeff"):
        name = name.lstrip("\ufeff")
    return name


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value