import json

from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import EpicsResponse
from utils.helpers import require_string, require_string_list
from utils.prompt_loader import load_prompt


class EpicGenerator:
	def __init__(self, llm_client: LLMClient) -> None:
		self.llm_client = llm_client

	def generate(
		self, project: dict[str, object], count: int = 2
	) -> dict[str, object]:
		if count <= 0:
			raise ValueError("Epic count must be greater than zero.")
		project_name = require_string(project, "name", "Project")
		project_description = require_string(project, "description", "Project")
		domain = require_string(project, "domain", "Project")
		objectives = require_string_list(project, "objectives", "Project")
		prompt = load_prompt(
			"epic",
			project_name=project_name,
			project_description=project_description,
			domain=domain,
			objectives=json.dumps(objectives, indent=2, ensure_ascii=False),
			epic_count=str(count),
		)
		validated = generate_validated(
			self.llm_client,
			prompt,
			EpicsResponse,
			"epics",
			semantic_validator=lambda response: require_exact_count(
				response, "epics", count, "epics"
			),
		)
		epics = [epic.model_dump() for epic in validated.epics]

		for index, epic in enumerate(epics, start=1):
			epic["id"] = f"EPIC-{index:03d}"
		return {"epics": epics}
