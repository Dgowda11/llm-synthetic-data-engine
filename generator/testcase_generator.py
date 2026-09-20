import json
from collections import Counter

from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import TestCasesResponse
from utils.helpers import require_string, require_string_list
from utils.prompt_loader import load_prompt


MAX_TEST_CASES_PER_STORY = 5


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
		if count > MAX_TEST_CASES_PER_STORY:
			raise ValueError(
				f"Test-case count cannot exceed {MAX_TEST_CASES_PER_STORY}."
			)

		story_id = require_string(story, "id", "Story")
		acceptance_criteria = require_string_list(
			story, "acceptance_criteria", "Story"
		)
		requested_count = max(count, len(acceptance_criteria))
		if requested_count > MAX_TEST_CASES_PER_STORY:
			raise ValueError(
				"A Story cannot require more than "
				f"{MAX_TEST_CASES_PER_STORY} Test Cases."
			)
		case_counts = _allocate_case_counts(
			requested_count, len(acceptance_criteria)
		)
		test_cases: list[dict[str, object]] = []

		for criterion, batch_count in zip(
			acceptance_criteria, case_counts, strict=True
		):
			test_types = _test_type_sequence(len(test_cases), batch_count)
			prompt = load_prompt(
				"test_case",
				project_name=require_string(project, "name", "Project"),
				story_id=story_id,
				story_title=require_string(story, "title", "Story"),
				story_description=require_string(story, "description", "Story"),
				acceptance_criteria=json.dumps(
					[criterion], indent=2, ensure_ascii=False
				),
				test_case_count=str(batch_count),
				test_type_sequence=json.dumps(test_types),
			)
			validated = generate_validated(
				self.llm_client,
				prompt,
				TestCasesResponse,
				"test cases",
				semantic_validator=lambda response, expected_count=batch_count,
				expected_criterion=criterion, expected_types=test_types:
				_validate_batch(
					response,
					expected_count,
					expected_criterion,
					expected_types,
				),
			)
			for test_case_model in validated.test_cases:
				test_case = test_case_model.model_dump()
				test_case["id"] = f"TC-{start_index + len(test_cases):03d}"
				test_case["story_id"] = story_id
				test_case["acceptance_criteria"] = criterion
				for index, step in enumerate(test_case["steps"], start=1):
					step["step_number"] = index
				test_cases.append(test_case)
		return {"test_cases": test_cases}


def _validate_batch(
	response: TestCasesResponse,
	expected_count: int,
	expected_criterion: str,
	expected_types: list[str],
) -> None:
	require_exact_count(response, "test_cases", expected_count, "test cases")
	if any(
		test_case.acceptance_criteria.casefold()
		!= expected_criterion.casefold()
		for test_case in response.test_cases
	):
		raise ValueError(
			"Every test case must copy the supplied acceptance criterion exactly."
		)
	actual_types = [test_case.test_type for test_case in response.test_cases]
	if Counter(actual_types) != Counter(expected_types):
		raise ValueError(
			f"Test case types must match this sequence: {expected_types}."
		)


def _allocate_case_counts(total_count: int, criterion_count: int) -> list[int]:
	base_count, remainder = divmod(total_count, criterion_count)
	return [
		base_count + (1 if index < remainder else 0)
		for index in range(criterion_count)
	]


def _test_type_sequence(start_index: int, count: int) -> list[str]:
	test_types = ["Positive", "Negative", "Boundary"]
	return [
		test_types[(start_index + offset) % len(test_types)]
		for offset in range(count)
	]
