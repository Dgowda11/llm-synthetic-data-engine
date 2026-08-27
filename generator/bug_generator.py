import json

from generator.llm import LLMClient
from utils.helpers import (
	parse_collection_response,
	require_string,
	require_string_list,
)
from utils.prompt_loader import load_prompt


class BugGenerator:
	def __init__(self, llm_client: LLMClient) -> None:
		self.llm_client = llm_client

	def generate(
		self,
		project: dict[str, object],
		story: dict[str, object],
		test_case: dict[str, object],
		actual_result: str,
		start_index: int = 1,
		count: int = 1,
	) -> dict[str, object]:
		if start_index <= 0:
			raise ValueError("Bug start index must be greater than zero.")
		if not actual_result.strip():
			raise ValueError("Actual result cannot be empty.")
		if count <= 0:
			raise ValueError("Bug count must be greater than zero.")

		story_id = require_string(story, "id", "Story")
		test_case_id = require_string(test_case, "id", "Test case")
		test_steps = test_case.get("steps")
		if not isinstance(test_steps, list) or not test_steps:
			raise ValueError("Test case must contain steps before generating bugs.")
		prompt = load_prompt(
			"bug",
			project_name=require_string(project, "name", "Project"),
			story_id=story_id,
			test_case_id=test_case_id,
			test_case_title=require_string(test_case, "title", "Test case"),
			test_steps=json.dumps(test_steps, indent=2, ensure_ascii=False),
			expected_result=require_string(
				test_case, "expected_result", "Test case"
			),
			actual_result=actual_result.strip(),
			bug_count=str(count),
		)
		response = self.llm_client.generate(prompt, json_output=True)
		bugs = parse_collection_response(
			response,
			"bugs",
			{
				"id",
				"story_id",
				"test_case_id",
				"title",
				"description",
				"steps_to_reproduce",
				"expected_result",
				"actual_result",
				"severity",
				"priority",
			},
		)
		if len(bugs) != count:
			raise ValueError(
				f"Expected {count} bugs, but the LLM returned {len(bugs)}."
			)

		for offset, bug in enumerate(bugs):
			bug["id"] = f"BUG-{start_index + offset:03d}"
			bug["story_id"] = story_id
			bug["test_case_id"] = test_case_id
			require_string(bug, "title", "Bug")
			require_string(bug, "description", "Bug")
			bug["steps_to_reproduce"] = require_string_list(
				bug, "steps_to_reproduce", "Bug"
			)
			require_string(bug, "expected_result", "Bug")
			require_string(bug, "actual_result", "Bug")
			severity = require_string(bug, "severity", "Bug").title()
			if severity not in {"Critical", "High", "Medium", "Low"}:
				raise ValueError("Bug severity is invalid.")
			bug["severity"] = severity
			priority = require_string(bug, "priority", "Bug").title()
			if priority not in {"High", "Medium", "Low"}:
				raise ValueError("Bug priority is invalid.")
			bug["priority"] = priority
		return {"bugs": bugs}
