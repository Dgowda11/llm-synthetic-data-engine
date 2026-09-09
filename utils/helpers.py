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
