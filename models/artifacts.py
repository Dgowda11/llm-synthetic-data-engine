from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
Priority = Literal["High", "Medium", "Low"]
Severity = Literal["Critical", "High", "Medium", "Low"]
TestType = Literal["Positive", "Negative", "Boundary"]


class ArtifactModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class PrioritizedModel(ArtifactModel):
    priority: Priority

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: object) -> object:
        return value.strip().title() if isinstance(value, str) else value


class Project(ArtifactModel):
    name: NonEmptyString
    description: NonEmptyString
    domain: NonEmptyString
    objectives: list[NonEmptyString] = Field(min_length=4, max_length=6)
    success_criteria: list[NonEmptyString] = Field(min_length=4, max_length=6)


class Epic(PrioritizedModel):
    id: NonEmptyString
    title: NonEmptyString
    description: NonEmptyString
    business_value: NonEmptyString


class EpicsResponse(ArtifactModel):
    epics: list[Epic] = Field(min_length=1)


class Feature(PrioritizedModel):
    id: NonEmptyString
    epic_id: NonEmptyString
    title: NonEmptyString
    description: NonEmptyString


class FeaturesResponse(ArtifactModel):
    features: list[Feature] = Field(min_length=1)


class Story(PrioritizedModel):
    id: NonEmptyString
    feature_id: NonEmptyString
    title: NonEmptyString
    description: NonEmptyString
    acceptance_criteria: list[NonEmptyString] = Field(min_length=1)
    acceptance_criteria_ids: list[NonEmptyString] = Field(default_factory=list)
    story_points: int = Field(gt=0)


class StoriesResponse(ArtifactModel):
    stories: list[Story] = Field(min_length=1)


class AcceptanceCriterion(ArtifactModel):
    id: NonEmptyString
    story_id: NonEmptyString
    text: NonEmptyString


class TestStep(ArtifactModel):
    step_number: int = Field(gt=0)
    action: NonEmptyString
    expected_result: NonEmptyString


class TestCase(PrioritizedModel):
    id: NonEmptyString
    story_id: NonEmptyString
    title: NonEmptyString
    preconditions: list[NonEmptyString]
    steps: list[TestStep] = Field(min_length=1)
    expected_result: NonEmptyString
    acceptance_criteria: NonEmptyString
    acceptance_criteria_id: NonEmptyString | None = None
    test_type: TestType

    @field_validator("test_type", mode="before")
    @classmethod
    def normalize_test_type(cls, value: object) -> object:
        return value.strip().title() if isinstance(value, str) else value


class TestCasesResponse(ArtifactModel):
    test_cases: list[TestCase] = Field(min_length=1)


class Bug(PrioritizedModel):
    id: NonEmptyString
    story_id: NonEmptyString
    test_case_id: NonEmptyString
    title: NonEmptyString
    description: NonEmptyString
    steps_to_reproduce: list[NonEmptyString] = Field(min_length=1)
    expected_result: NonEmptyString
    actual_result: NonEmptyString
    severity: Severity

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: object) -> object:
        return value.strip().title() if isinstance(value, str) else value


class BugsResponse(ArtifactModel):
    bugs: list[Bug] = Field(min_length=1)


class BugLink(ArtifactModel):
    bug_id: NonEmptyString
    test_case_id: NonEmptyString


class TraceabilityEntry(ArtifactModel):
    epic_id: NonEmptyString
    feature_id: NonEmptyString
    story_id: NonEmptyString
    acceptance_criteria_ids: list[NonEmptyString]
    test_case_ids: list[NonEmptyString]
    bug_links: list[BugLink]


class TraceabilityResult(ArtifactModel):
    traceability: list[TraceabilityEntry]
    unresolved_references: list[NonEmptyString]


class SyntheticDataset(ArtifactModel):
    project: Project
    epics: list[Epic]
    features: list[Feature]
    stories: list[Story]
    acceptance_criteria: list[AcceptanceCriterion]
    test_cases: list[TestCase]
    bugs: list[Bug]
    traceability: TraceabilityResult

    @model_validator(mode="after")
    def validate_hierarchy(self) -> Self:
        epic_ids = _unique_ids(self.epics, "epics")
        feature_ids = _unique_ids(self.features, "features")
        story_ids = _unique_ids(self.stories, "stories")
        criterion_ids = _unique_ids(
            self.acceptance_criteria, "acceptance criteria"
        )
        test_case_ids = _unique_ids(self.test_cases, "test cases")
        bug_ids = _unique_ids(self.bugs, "bugs")

        feature_by_id = {feature.id: feature for feature in self.features}
        story_by_id = {story.id: story for story in self.stories}
        criterion_by_id = {
            criterion.id: criterion for criterion in self.acceptance_criteria
        }
        test_case_by_id = {test_case.id: test_case for test_case in self.test_cases}

        for feature in self.features:
            _require_reference(feature.epic_id, epic_ids, f"Feature {feature.id}")
        for story in self.stories:
            _require_reference(story.feature_id, feature_ids, f"Story {story.id}")
            story_criteria = {
                criterion.text
                for criterion in self.acceptance_criteria
                if criterion.story_id == story.id
            }
            if story_criteria != set(story.acceptance_criteria):
                raise ValueError(
                    f"Acceptance criteria records are invalid for story {story.id}."
                )
            for criterion_id in story.acceptance_criteria_ids:
                _require_reference(criterion_id, criterion_ids, f"Story {story.id}")
                if criterion_by_id[criterion_id].story_id != story.id:
                    raise ValueError(
                        f"Story {story.id} references another story's criterion."
                    )
        for criterion in self.acceptance_criteria:
            _require_reference(
                criterion.story_id, story_ids, f"Criterion {criterion.id}"
            )
        for test_case in self.test_cases:
            _require_reference(
                test_case.story_id, story_ids, f"Test case {test_case.id}"
            )
            if test_case.acceptance_criteria_id is None:
                raise ValueError(
                    f"Test case {test_case.id} has no acceptance criterion ID."
                )
            _require_reference(
                test_case.acceptance_criteria_id,
                criterion_ids,
                f"Test case {test_case.id}",
            )
            if (
                criterion_by_id[test_case.acceptance_criteria_id].story_id
                != test_case.story_id
            ):
                raise ValueError(
                    f"Test case {test_case.id} references another story's criterion."
                )
        for bug in self.bugs:
            _require_reference(bug.story_id, story_ids, f"Bug {bug.id}")
            _require_reference(
                bug.test_case_id, test_case_ids, f"Bug {bug.id}"
            )
            if test_case_by_id[bug.test_case_id].story_id != bug.story_id:
                raise ValueError(
                    f"Bug {bug.id} story does not match its test case."
                )

        if self.traceability.unresolved_references:
            raise ValueError("Traceability contains unresolved references.")
        trace_story_ids = [entry.story_id for entry in self.traceability.traceability]
        if set(trace_story_ids) != story_ids or len(trace_story_ids) != len(story_ids):
            raise ValueError("Traceability must contain every story exactly once.")
        traced_bug_ids: list[str] = []
        for entry in self.traceability.traceability:
            story = story_by_id[entry.story_id]
            feature = feature_by_id[story.feature_id]
            if entry.feature_id != feature.id or entry.epic_id != feature.epic_id:
                raise ValueError(
                    f"Traceability parents are invalid for story {entry.story_id}."
                )
            if set(entry.acceptance_criteria_ids) != set(
                story.acceptance_criteria_ids
            ):
                raise ValueError(
                    f"Traceability criteria are invalid for story {entry.story_id}."
                )
            expected_tests = {
                test_case.id
                for test_case in self.test_cases
                if test_case.story_id == entry.story_id
            }
            if set(entry.test_case_ids) != expected_tests:
                raise ValueError(
                    f"Traceability tests are invalid for story {entry.story_id}."
                )
            for bug_link in entry.bug_links:
                _require_reference(
                    bug_link.bug_id, bug_ids, f"Traceability {entry.story_id}"
                )
                _require_reference(
                    bug_link.test_case_id,
                    test_case_ids,
                    f"Traceability {entry.story_id}",
                )
                bug = next(bug for bug in self.bugs if bug.id == bug_link.bug_id)
                if (
                    bug.test_case_id != bug_link.test_case_id
                    or bug.story_id != entry.story_id
                ):
                    raise ValueError(
                        f"Traceability bug link is invalid for {bug_link.bug_id}."
                    )
                traced_bug_ids.append(bug_link.bug_id)
        if set(traced_bug_ids) != bug_ids or len(traced_bug_ids) != len(bug_ids):
            raise ValueError("Traceability must contain every bug exactly once.")
        return self


def _unique_ids(items: list[ArtifactModel], collection_name: str) -> set[str]:
    ids = [getattr(item, "id") for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate IDs found in {collection_name}.")
    return set(ids)


def _require_reference(value: str, valid_ids: set[str], source: str) -> None:
    if value not in valid_ids:
        raise ValueError(f"{source} references missing ID '{value}'.")