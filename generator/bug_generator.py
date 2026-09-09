import json

from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import BugsResponse
from utils.helpers import require_string
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
		validated = generate_validated(
			self.llm_client,
			prompt,
			BugsResponse,
			"bugs",
			semantic_validator=lambda response: require_exact_count(
				response, "bugs", count, "bugs"
			),
		)
		bugs = [bug.model_dump() for bug in validated.bugs]

		for offset, bug in enumerate(bugs):
			bug["id"] = f"BUG-{start_index + offset:03d}"
			bug["story_id"] = story_id
			bug["test_case_id"] = test_case_id
		return {"bugs": bugs}
