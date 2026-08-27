from generator.llm import LLMClient
from utils.helpers import (
	parse_collection_response,
	require_string,
	require_string_list,
)
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
		response = self.llm_client.generate(prompt, json_output=True)
		stories = parse_collection_response(
			response,
			"stories",
			{
				"id",
				"feature_id",
				"title",
				"description",
				"acceptance_criteria",
				"priority",
				"story_points",
			},
		)
		if len(stories) != count:
			raise ValueError(
				f"Expected {count} stories, but the LLM returned {len(stories)}."
			)

		for offset, story in enumerate(stories):
			story["id"] = f"US-{start_index + offset:03d}"
			story["feature_id"] = feature_id
			require_string(story, "title", "Story")
			require_string(story, "description", "Story")
			story["acceptance_criteria"] = require_string_list(
				story, "acceptance_criteria", "Story"
			)
			priority = require_string(story, "priority", "Story").title()
			if priority not in {"High", "Medium", "Low"}:
				raise ValueError("Story priority must be High, Medium, or Low.")
			story["priority"] = priority
			story_points = story.get("story_points")
			if (
				not isinstance(story_points, int)
				or isinstance(story_points, bool)
				or story_points <= 0
			):
				raise ValueError("Story points must be a positive integer.")
		return {"stories": stories}
