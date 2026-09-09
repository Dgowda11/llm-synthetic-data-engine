from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import FeaturesResponse
from utils.helpers import require_string
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
		validated = generate_validated(
			self.llm_client,
			prompt,
			FeaturesResponse,
			"features",
			semantic_validator=lambda response: require_exact_count(
				response, "features", count, "features"
			),
		)
		features = [feature.model_dump() for feature in validated.features]

		for offset, feature in enumerate(features):
			feature["id"] = f"FEATURE-{start_index + offset:03d}"
			feature["epic_id"] = epic_id
		return {"features": features}
