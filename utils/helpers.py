import json
from json import JSONDecodeError
from typing import cast


def parse_json_object(response: str, artifact_name: str) -> dict[str, object]:
	"""Parse an LLM response and require one top-level JSON object."""
	try:
		parsed = json.loads(response)
	except JSONDecodeError as error:
		raise ValueError(f"The LLM returned invalid {artifact_name} JSON.") from error

	if not isinstance(parsed, dict):
		raise ValueError(f"The {artifact_name} response must be a JSON object.")
	return cast(dict[str, object], parsed)


def parse_collection_response(
	response: str,
	collection_name: str,
	required_fields: set[str],
	*,
	allow_empty: bool = False,
) -> list[dict[str, object]]:
	"""Parse a response containing a named list of artifact objects."""
	parsed = parse_json_object(response, collection_name)
	items = parsed.get(collection_name)
	if not isinstance(items, list):
		raise ValueError(
			f"The LLM response must contain a '{collection_name}' array."
		)
	if not items and not allow_empty:
		raise ValueError(f"The LLM returned no {collection_name}.")

	validated_items: list[dict[str, object]] = []
	for index, item in enumerate(items, start=1):
		if not isinstance(item, dict):
			raise ValueError(
				f"Item {index} in '{collection_name}' must be a JSON object."
			)
		missing_fields = required_fields.difference(item)
		if missing_fields:
			missing = ", ".join(sorted(missing_fields))
			raise ValueError(
				f"Item {index} in '{collection_name}' is missing: {missing}."
			)
		validated_items.append(cast(dict[str, object], item))
	return validated_items


def require_string(
	data: dict[str, object],
	field_name: str,
	artifact_name: str,
) -> str:
	"""Read a required non-empty string field from an artifact."""
	value = data.get(field_name)
	if not isinstance(value, str) or not value.strip():
		raise ValueError(
			f"{artifact_name} must contain a non-empty '{field_name}' string."
		)
	return value.strip()


def require_string_list(
	data: dict[str, object],
	field_name: str,
	artifact_name: str,
) -> list[str]:
	"""Read a required non-empty list of non-empty strings."""
	value = data.get(field_name)
	if not isinstance(value, list) or not value:
		raise ValueError(
			f"{artifact_name} must contain a non-empty '{field_name}' array."
		)

	cleaned_values: list[str] = []
	for item in value:
		if not isinstance(item, str) or not item.strip():
			raise ValueError(
				f"Every value in {artifact_name}.{field_name} must be text."
			)
		cleaned_values.append(item.strip())
	return cleaned_values
