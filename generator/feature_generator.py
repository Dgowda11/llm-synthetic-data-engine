from generator.llm import LLMClient
from utils.helpers import parse_collection_response, require_string
from utils.prompt_loader import load_prompt


class FeatureGenerator:
	def __init__(self, llm_client: LLMClient) -> None:
		self.llm_client = llm_client

	def generate(
		self,
		project: dict[str, object],
		epic: dict[str, object],
		start_index: int = 1,
		count: int = 2,
	) -> dict[str, object]:
		if start_index <= 0:
			raise ValueError("Feature start index must be greater than zero.")
		if count <= 0:
			raise ValueError("Feature count must be greater than zero.")

		epic_id = require_string(epic, "id", "Epic")
		prompt = load_prompt(
			"feature",
			project_name=require_string(project, "name", "Project"),
			domain=require_string(project, "domain", "Project"),
			epic_id=epic_id,
			epic_title=require_string(epic, "title", "Epic"),
			epic_description=require_string(epic, "description", "Epic"),
			feature_count=str(count),
		)
		response = self.llm_client.generate(prompt, json_output=True)
		features = parse_collection_response(
			response,
			"features",
			{"id", "epic_id", "title", "description", "priority"},
		)
		if len(features) != count:
			raise ValueError(
				f"Expected {count} features, but the LLM returned {len(features)}."
			)

		for offset, feature in enumerate(features):
			feature["id"] = f"FEATURE-{start_index + offset:03d}"
			feature["epic_id"] = epic_id
			require_string(feature, "title", "Feature")
			require_string(feature, "description", "Feature")
			priority = require_string(feature, "priority", "Feature").title()
			if priority not in {"High", "Medium", "Low"}:
				raise ValueError("Feature priority must be High, Medium, or Low.")
			feature["priority"] = priority
		return {"features": features}
