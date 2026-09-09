from generator.llm import LLMClient
from generator.validation import generate_validated, require_exact_count
from models import StoriesResponse
from utils.helpers import require_string
from utils.prompt_loader import load_prompt


class StoryGenerator:
	def __init__(self, llm_client: LLMClient) -> None:
		self.llm_client = llm_client

	def generate(
		self,
		project: dict[str, object],
		epic: dict[str, object],
		feature: dict[str, object],
		start_index: int = 1,
		count: int = 2,
	) -> dict[str, object]:
		if start_index <= 0:
			raise ValueError("Story start index must be greater than zero.")
		if count <= 0:
			raise ValueError("Story count must be greater than zero.")

		feature_id = require_string(feature, "id", "Feature")
		prompt = load_prompt(
			"story",
			project_name=require_string(project, "name", "Project"),
			epic_id=require_string(epic, "id", "Epic"),
			feature_id=feature_id,
			feature_title=require_string(feature, "title", "Feature"),
			feature_description=require_string(feature, "description", "Feature"),
			story_count=str(count),
		)
		validated = generate_validated(
			self.llm_client,
			prompt,
			StoriesResponse,
			"stories",
			semantic_validator=lambda response: require_exact_count(
				response, "stories", count, "stories"
			),
		)
		stories = [story.model_dump() for story in validated.stories]

		for offset, story in enumerate(stories):
			story["id"] = f"US-{start_index + offset:03d}"
			story["feature_id"] = feature_id
		return {"stories": stories}
