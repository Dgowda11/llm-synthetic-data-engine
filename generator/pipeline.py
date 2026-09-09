from typing import cast

from generator.bug_generator import BugGenerator
from generator.epic_generator import EpicGenerator
from generator.feature_generator import FeatureGenerator
from generator.llm import LLMClient
from generator.project_generator import ProjectGenerator
from generator.story_generator import StoryGenerator
from generator.testcase_generator import TestCaseGenerator
from models import SyntheticDataset
from utils.helpers import require_string


class SyntheticDataEngine:
    def __init__(
        self,
        llm_client: LLMClient,
        epic_count: int = 2,
        features_per_epic: int = 2,
        stories_per_feature: int = 2,
        test_cases_per_story: int = 3,
        bug_sources_per_story: int = 1,
        bugs_per_source: int = 1,
    ) -> None:
        counts = {
            "epic_count": epic_count,
            "features_per_epic": features_per_epic,
            "stories_per_feature": stories_per_feature,
            "test_cases_per_story": test_cases_per_story,
            "bugs_per_source": bugs_per_source,
        }
        if any(value <= 0 for value in counts.values()):
            raise ValueError("Artifact counts must be greater than zero.")
        if bug_sources_per_story < 0:
            raise ValueError("Bug sources per story cannot be negative.")
        self.project_generator = ProjectGenerator(llm_client)
        self.epic_generator = EpicGenerator(llm_client)
        self.feature_generator = FeatureGenerator(llm_client)
        self.story_generator = StoryGenerator(llm_client)
        self.test_case_generator = TestCaseGenerator(llm_client)
        self.bug_generator = BugGenerator(llm_client)
        self.epic_count = epic_count
        self.features_per_epic = features_per_epic
        self.stories_per_feature = stories_per_feature
        self.test_cases_per_story = test_cases_per_story
        self.bug_sources_per_story = bug_sources_per_story
        self.bugs_per_source = bugs_per_source

    def generate(self, domain: str) -> dict[str, object]:
        project = self.project_generator.generate(domain)
        epics = _get_collection(
            self.epic_generator.generate(project, count=self.epic_count), "epics"
        )

        features: list[dict[str, object]] = []
        stories: list[dict[str, object]] = []
        acceptance_criteria: list[dict[str, object]] = []
        test_cases: list[dict[str, object]] = []
        bugs: list[dict[str, object]] = []

        next_feature_id = 1
        next_story_id = 1
        next_criterion_id = 1
        next_test_case_id = 1
        next_bug_id = 1

        for epic in epics:
            generated_features = _get_collection(
                self.feature_generator.generate(
                    project,
                    epic,
                    start_index=next_feature_id,
                    count=self.features_per_epic,
                ),
                "features",
            )
            next_feature_id += len(generated_features)
            features.extend(generated_features)

            for feature in generated_features:
                generated_stories = _get_collection(
                    self.story_generator.generate(
                        project,
                        epic,
                        feature,
                        start_index=next_story_id,
                        count=self.stories_per_feature,
                    ),
                    "stories",
                )
                next_story_id += len(generated_stories)
                stories.extend(generated_stories)

                for story in generated_stories:
                    criterion_ids = self._add_acceptance_criteria(
                        story,
                        acceptance_criteria,
                        next_criterion_id,
                    )
                    next_criterion_id += len(criterion_ids)

                    generated_test_cases = _get_collection(
                        self.test_case_generator.generate(
                            project,
                            story,
                            start_index=next_test_case_id,
                            count=self.test_cases_per_story,
                        ),
                        "test_cases",
                    )
                    next_test_case_id += len(generated_test_cases)
                    self._link_test_cases_to_criteria(
                        story,
                        generated_test_cases,
                        acceptance_criteria,
                    )
                    test_cases.extend(generated_test_cases)

                    for test_case in generated_test_cases[
                        : self.bug_sources_per_story
                    ]:
                        expected_result = require_string(
                            test_case, "expected_result", "Test case"
                        )
                        actual_result = (
                            "The action failed and did not produce the expected "
                            f"result: {expected_result}"
                        )
                        generated_bugs = _get_collection(
                            self.bug_generator.generate(
                                project,
                                story,
                                test_case,
                                actual_result,
                                start_index=next_bug_id,
                                count=self.bugs_per_source,
                            ),
                            "bugs",
                        )
                        next_bug_id += len(generated_bugs)
                        bugs.extend(generated_bugs)

        traceability = _build_traceability(
            epics,
            features,
            stories,
            acceptance_criteria,
            test_cases,
            bugs,
        )
        dataset = {
            "project": project,
            "epics": epics,
            "features": features,
            "stories": stories,
            "acceptance_criteria": acceptance_criteria,
            "test_cases": test_cases,
            "bugs": bugs,
            "traceability": traceability,
        }
        return SyntheticDataset.model_validate(dataset).model_dump()

    @staticmethod
    def _add_acceptance_criteria(
        story: dict[str, object],
        all_criteria: list[dict[str, object]],
        start_index: int,
    ) -> list[str]:
        story_id = require_string(story, "id", "Story")
        values = story.get("acceptance_criteria")
        if not isinstance(values, list):
            raise ValueError("Story acceptance criteria must be an array.")

        ids: list[str] = []
        for offset, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Acceptance criteria must contain only text.")
            criterion_id = f"AC-{start_index + offset:03d}"
            all_criteria.append(
                {
                    "id": criterion_id,
                    "story_id": story_id,
                    "text": value.strip(),
                }
            )
            ids.append(criterion_id)
        story["acceptance_criteria_ids"] = ids
        return ids

    @staticmethod
    def _link_test_cases_to_criteria(
        story: dict[str, object],
        test_cases: list[dict[str, object]],
        all_criteria: list[dict[str, object]],
    ) -> None:
        story_id = require_string(story, "id", "Story")
        criterion_by_text = {
            require_string(criterion, "text", "Acceptance criterion").casefold():
            require_string(criterion, "id", "Acceptance criterion")
            for criterion in all_criteria
            if criterion.get("story_id") == story_id
        }
        for test_case in test_cases:
            criterion_text = require_string(
                test_case, "acceptance_criteria", "Test case"
            )
            criterion_id = criterion_by_text.get(criterion_text.casefold())
            if criterion_id is None:
                raise ValueError(
                    "A test case could not be linked to an acceptance criterion."
                )
            test_case["acceptance_criteria_id"] = criterion_id


def _get_collection(
    response: dict[str, object], collection_name: str
) -> list[dict[str, object]]:
    items = response.get(collection_name)
    if not isinstance(items, list):
        raise ValueError(f"Missing '{collection_name}' collection.")
    return cast(list[dict[str, object]], items)


def _build_traceability(
    epics: list[dict[str, object]],
    features: list[dict[str, object]],
    stories: list[dict[str, object]],
    acceptance_criteria: list[dict[str, object]],
    test_cases: list[dict[str, object]],
    bugs: list[dict[str, object]],
) -> dict[str, object]:
    epic_ids = {require_string(epic, "id", "Epic") for epic in epics}
    feature_parent = {
        require_string(feature, "id", "Feature"):
        require_string(feature, "epic_id", "Feature")
        for feature in features
    }
    criteria_by_story: dict[str, list[str]] = {}
    for criterion in acceptance_criteria:
        criteria_by_story.setdefault(
            require_string(criterion, "story_id", "Acceptance criterion"), []
        ).append(require_string(criterion, "id", "Acceptance criterion"))
    tests_by_story: dict[str, list[str]] = {}
    for test_case in test_cases:
        tests_by_story.setdefault(
            require_string(test_case, "story_id", "Test case"), []
        ).append(require_string(test_case, "id", "Test case"))
    bugs_by_test: dict[str, list[str]] = {}
    for bug in bugs:
        bugs_by_test.setdefault(
            require_string(bug, "test_case_id", "Bug"), []
        ).append(require_string(bug, "id", "Bug"))

    mappings: list[dict[str, object]] = []
    unresolved: list[str] = []
    for story in stories:
        story_id = require_string(story, "id", "Story")
        feature_id = require_string(story, "feature_id", "Story")
        epic_id = feature_parent.get(feature_id)
        if epic_id is None or epic_id not in epic_ids:
            unresolved.append(story_id)
            continue
        story_test_ids = tests_by_story.get(story_id, [])
        bug_links = [
            {"bug_id": bug_id, "test_case_id": test_case_id}
            for test_case_id in story_test_ids
            for bug_id in bugs_by_test.get(test_case_id, [])
        ]
        mappings.append(
            {
                "epic_id": epic_id,
                "feature_id": feature_id,
                "story_id": story_id,
                "acceptance_criteria_ids": criteria_by_story.get(story_id, []),
                "test_case_ids": story_test_ids,
                "bug_links": bug_links,
            }
        )
    return {
        "traceability": mappings,
        "unresolved_references": unresolved,
    }