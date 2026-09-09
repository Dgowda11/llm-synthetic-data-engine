import json

from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import TestCasesResponse
from utils.helpers import require_string, require_string_list
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
		validated = generate_validated(
			self.llm_client,
			prompt,
			TestCasesResponse,
			"test cases",
			semantic_validator=lambda response: _validate_response(
				response, requested_count, acceptance_criteria
			),
		)
		test_cases = [test_case.model_dump() for test_case in validated.test_cases]
		criteria_lookup = {
			criterion.casefold(): criterion for criterion in acceptance_criteria
		}

		for offset, test_case in enumerate(test_cases):
			test_case["id"] = f"TC-{start_index + offset:03d}"
			test_case["story_id"] = story_id
			criterion = require_string(
				test_case, "acceptance_criteria", "Test case"
			)
			test_case["acceptance_criteria"] = criteria_lookup[criterion.casefold()]
			for index, step in enumerate(test_case["steps"], start=1):
				step["step_number"] = index
		return {"test_cases": test_cases}


def _validate_response(
	response: TestCasesResponse,
	expected_count: int,
	acceptance_criteria: list[str],
) -> None:
	require_exact_count(response, "test_cases", expected_count, "test cases")
	valid_criteria = {criterion.casefold() for criterion in acceptance_criteria}
	covered_criteria = {
		test_case.acceptance_criteria.casefold()
		for test_case in response.test_cases
	}
	unknown_criteria = covered_criteria.difference(valid_criteria)
	if unknown_criteria:
		raise ValueError(
			"Every test case must copy one supplied acceptance criterion exactly."
		)
	if covered_criteria != valid_criteria:
		raise ValueError("The test cases must cover every acceptance criterion.")
