import json
from pathlib import Path


def save_json(data: dict[str, object], output_path: Path) -> Path:
    """Save a dictionary as formatted UTF-8 JSON."""
    if not isinstance(data, dict):
        raise TypeError("JSON export data must be a dictionary.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")

    return output_path


def save_dataset(
    dataset: dict[str, object], output_directory: Path
) -> dict[str, Path]:
    """Save every generated artifact collection to its own JSON file."""
    project = dataset.get("project")
    if not isinstance(project, dict):
        raise ValueError("Dataset must contain a project object.")

    payloads: dict[str, dict[str, object]] = {
        "project": project,
        "epics": {"epics": _require_list(dataset, "epics")},
        "features": {"features": _require_list(dataset, "features")},
        "stories": {"stories": _require_list(dataset, "stories")},
        "acceptance_criteria": {
            "acceptance_criteria": _require_list(dataset, "acceptance_criteria")
        },
        "testcases": {"test_cases": _require_list(dataset, "test_cases")},
        "bugs": {"bugs": _require_list(dataset, "bugs")},
    }
    traceability = dataset.get("traceability")
    if not isinstance(traceability, dict):
        raise ValueError("Dataset must contain a traceability object.")
    payloads["traceability"] = traceability

    return {
        name: save_json(payload, output_directory / f"{name}.json")
        for name, payload in payloads.items()
    }


def _require_list(dataset: dict[str, object], field_name: str) -> list[object]:
    value = dataset.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"Dataset must contain a '{field_name}' array.")
    return value