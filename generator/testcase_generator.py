import json
from typing import cast

from generator.llm import LLMClient
from utils.helpers import (
	parse_collection_response,
	require_string,
	require_string_list,
)
from utils.prompt_loader import load_prompt


class TestCaseGenerator:
	def __init__(self, llm_client: LLMClient) -> None:
		self.llm_client = llm_client

	def generate(
		self,
		project: dict[str, object],
		story: dict[str, object],
		start_index: int = 1,
		count: int = 3,
	) -> dict[str, object]:
		if start_index <= 0:
			raise ValueError("Test-case start index must be greater than zero.")
		if count <= 0:
			raise ValueError("Test-case count must be greater than zero.")

		story_id = require_string(story, "id", "Story")
		acceptance_criteria = require_string_list(
			story, "acceptance_criteria", "Story"
		)
		requested_count = max(count, len(acceptance_criteria))
		prompt = load_prompt(
			"test_case",
			project_name=require_string(project, "name", "Project"),
			story_id=story_id,
			story_title=require_string(story, "title", "Story"),
			story_description=require_string(story, "description", "Story"),
			acceptance_criteria=json.dumps(
				acceptance_criteria, indent=2, ensure_ascii=False
			),
			test_case_count=str(requested_count),
		)
		response = self.llm_client.generate(prompt, json_output=True)
		test_cases = parse_collection_response(
			response,
			"test_cases",
			{
				"id",
				"story_id",
				"title",
				"preconditions",
				"steps",
				"expected_result",
				"acceptance_criteria",
				"priority",
				"test_type",
			},
		)
		if len(test_cases) != requested_count:
			raise ValueError(
				"Expected "
				f"{requested_count} test cases, but the LLM returned "
				f"{len(test_cases)}."
			)
		criteria_lookup = {
			criterion.casefold(): criterion for criterion in acceptance_criteria
		}
		covered_criteria: set[str] = set()

		for offset, test_case in enumerate(test_cases):
			test_case["id"] = f"TC-{start_index + offset:03d}"
			test_case["story_id"] = story_id
			require_string(test_case, "title", "Test case")
			_validate_optional_string_list(test_case, "preconditions")
			_validate_steps(test_case)
			require_string(test_case, "expected_result", "Test case")
			criterion = require_string(
				test_case, "acceptance_criteria", "Test case"
			)
			canonical_criterion = criteria_lookup.get(criterion.casefold())
			if canonical_criterion is None:
				raise ValueError(
					"A test case references an unknown acceptance criterion."
				)
			test_case["acceptance_criteria"] = canonical_criterion
			covered_criteria.add(canonical_criterion)

			priority = require_string(test_case, "priority", "Test case").title()
			if priority not in {"High", "Medium", "Low"}:
				raise ValueError("Test-case priority must be High, Medium, or Low.")
			test_case["priority"] = priority
			test_type = require_string(test_case, "test_type", "Test case").title()
			if test_type not in {"Positive", "Negative", "Boundary"}:
				raise ValueError(
					"Test type must be Positive, Negative, or Boundary."
				)
			test_case["test_type"] = test_type

		if covered_criteria != set(acceptance_criteria):
			raise ValueError("The generated test cases do not cover every criterion.")
		return {"test_cases": test_cases}


def _validate_optional_string_list(
	artifact: dict[str, object], field_name: str
) -> None:
	values = artifact.get(field_name)
	if not isinstance(values, list):
		raise ValueError(f"Test case '{field_name}' must be an array.")
	if any(not isinstance(value, str) or not value.strip() for value in values):
		raise ValueError(f"Every test case '{field_name}' value must be text.")
	artifact[field_name] = [cast(str, value).strip() for value in values]


def _validate_steps(test_case: dict[str, object]) -> None:
	steps = test_case.get("steps")
	if not isinstance(steps, list) or not steps:
		raise ValueError("A test case must contain at least one step.")
	for index, step in enumerate(steps, start=1):
		if not isinstance(step, dict):
			raise ValueError("Every test step must be a JSON object.")
		step["step_number"] = index
		require_string(step, "action", "Test step")
		require_string(step, "expected_result", "Test step")
