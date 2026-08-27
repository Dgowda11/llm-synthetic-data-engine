import json

from generator.llm import LLMClient
from utils.helpers import (
	parse_collection_response,
	require_string,
	require_string_list,
)
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
		response = self.llm_client.generate(prompt, json_output=True)
		epics = parse_collection_response(
			response,
			"epics",
			{"id", "title", "description", "business_value", "priority"},
		)
		if len(epics) != count:
			raise ValueError(f"Expected {count} epics, but the LLM returned {len(epics)}.")

		for index, epic in enumerate(epics, start=1):
			epic["id"] = f"EPIC-{index:03d}"
			require_string(epic, "title", "Epic")
			require_string(epic, "description", "Epic")
			require_string(epic, "business_value", "Epic")
			_validate_priority(epic, "Epic")
		return {"epics": epics}


def _validate_priority(artifact: dict[str, object], artifact_name: str) -> None:
	priority = require_string(artifact, "priority", artifact_name).title()
	if priority not in {"High", "Medium", "Low"}:
		raise ValueError(f"{artifact_name} priority must be High, Medium, or Low.")
	artifact["priority"] = priority
