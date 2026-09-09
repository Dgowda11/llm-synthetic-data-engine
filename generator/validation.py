from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from generator.llm import LLMClient


ModelType = TypeVar("ModelType", bound=BaseModel)


def generate_validated(
    llm_client: LLMClient,
    prompt: str,
    model_type: type[ModelType],
    artifact_name: str,
    *,
    semantic_validator: Callable[[ModelType], None] | None = None,
    attempts: int = 3,
) -> ModelType:
    """Generate and validate structured output, retrying correctable failures."""
    if attempts <= 0:
        raise ValueError("Validation attempts must be greater than zero.")

    current_prompt = prompt
    last_error: Exception | None = None
    last_summary = "unknown validation failure"

    for attempt in range(1, attempts + 1):
        try:
            response = llm_client.generate(current_prompt, json_output=True)
            validated = model_type.model_validate_json(response)
            if semantic_validator is not None:
                semantic_validator(validated)
            return validated
        except (ValidationError, ValueError) as error:
            last_error = error
            last_summary = _summarize_error(error)
            if attempt == attempts:
                break
            current_prompt = _correction_prompt(prompt, last_summary)

    raise ValueError(
        f"The LLM failed {artifact_name} validation after {attempts} attempts: "
        f"{last_summary}"
    ) from last_error


def require_exact_count(
    response: BaseModel,
    field_name: str,
    expected_count: int,
    artifact_name: str,
) -> None:
    """Validate a dynamic collection count after Pydantic field validation."""
    items = getattr(response, field_name, None)
    if not isinstance(items, list):
        raise ValueError(f"{artifact_name} response has no '{field_name}' list.")
    if len(items) != expected_count:
        raise ValueError(
            f"Expected exactly {expected_count} {artifact_name}, "
            f"but received {len(items)}."
        )


def _summarize_error(error: Exception) -> str:
    if not isinstance(error, ValidationError):
        return str(error)

    messages: list[str] = []
    for issue in error.errors(include_url=False, include_input=False)[:8]:
        location = ".".join(str(part) for part in issue["loc"])
        messages.append(f"{location}: {issue['msg']}")
    return "; ".join(messages)


def _correction_prompt(original_prompt: str, error_summary: str) -> str:
    return (
        f"{original_prompt}\n\n"
        "# Correction Required\n\n"
        "Your previous JSON response failed validation for these reasons:\n"
        f"{error_summary}\n\n"
        "Generate the complete response again. Follow the original JSON schema and "
        "requested item count exactly. Return JSON only."
    )