import copy
import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from azure.connection import AzureDevOpsClient
from azure.workitems import AzureWorkItemUploader
from generator.exporter import save_dataset
from generator.pipeline import SyntheticDataEngine
from models import SyntheticDataset


class FakeLLMClient:
    def __init__(self) -> None:
        criteria = ["Criterion A", "Criterion B", "Criterion C", "Criterion D"]
        self.prompts: list[str] = []
        self.responses = [
            {
                "name": "Banking Portal",
                "description": "A digital banking portal.",
                "domain": "Banking",
                "objectives": ["O1", "O2", "O3", "O4"],
                "success_criteria": ["S1", "S2", "S3", "S4"],
            },
            {
                "epics": [
                    {
                        "id": "raw",
                        "title": "Account Access",
                        "description": "Manage secure account access.",
                        "business_value": "Protect customer accounts.",
                        "priority": "high",
                    }
                ]
            },
            {
                "features": [
                    {
                        "id": "raw",
                        "epic_id": "raw",
                        "title": "Sign In",
                        "description": "Allow secure sign in.",
                        "priority": "high",
                    }
                ]
            },
            {
                "stories": [
                    {
                        "id": "raw",
                        "feature_id": "raw",
                        "title": "Customer sign in",
                        "description": "As a customer, I want to sign in securely.",
                        "acceptance_criteria": criteria,
                        "priority": "high",
                        "story_points": 3,
                    }
                ]
            },
            {
                "test_cases": [
                    self._test_case(1, criteria[0], "Positive"),
                    self._test_case(2, criteria[0], "Positive"),
                ]
            },
            {"test_cases": [self._test_case(1, criteria[0], "Positive")]},
            {"test_cases": [self._test_case(2, criteria[1], "Negative")]},
            {"test_cases": [self._test_case(3, criteria[2], "Boundary")]},
            {"test_cases": [self._test_case(4, criteria[3], "Positive")]},
            {
                "bugs": [
                    {
                        "id": "raw",
                        "story_id": "raw",
                        "test_case_id": "raw",
                        "title": "Sign in fails",
                        "description": "Valid sign in does not complete.",
                        "steps_to_reproduce": ["Submit valid credentials"],
                        "expected_result": "Access is granted",
                        "actual_result": "An error is displayed",
                        "severity": "high",
                        "priority": "high",
                    }
                ]
            },
        ]

    @staticmethod
    def _test_case(
        number: int, criterion: str, test_type: str
    ) -> dict[str, object]:
        return {
            "id": f"raw-{number}",
            "story_id": "raw",
            "title": f"Test {number}",
            "preconditions": [],
            "steps": [
                {
                    "step_number": 1,
                    "action": "Submit credentials",
                    "expected_result": "Access is granted",
                }
            ],
            "expected_result": "Access is granted",
            "acceptance_criteria": criterion,
            "priority": "high",
            "test_type": test_type,
        }

    def generate(self, prompt: str, json_output: bool = False) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.responses.pop(0))


class FakeAzureClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, **kwargs: object) -> dict[str, object]:
        item_id = len(self.calls) + 101
        self.calls.append((method, path, kwargs))
        return {
            "id": item_id,
            "url": f"https://example.invalid/workItems/{item_id}",
        }


class GenerationPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.llm_client = FakeLLMClient()
        self.dataset = SyntheticDataEngine(
            self.llm_client,
            epic_count=1,
            features_per_epic=1,
            stories_per_feature=1,
            test_cases_per_story=3,
            bugs_per_source=1,
        ).generate("Banking")

    def test_pipeline_retries_count_mismatch_and_preserves_hierarchy(self) -> None:
        self.assertEqual(4, len(self.dataset["test_cases"]))
        self.assertIn("Expected exactly 1 test cases", self.llm_client.prompts[5])
        self.assertEqual(
            {"Criterion A", "Criterion B", "Criterion C", "Criterion D"},
            {
                test_case["acceptance_criteria"]
                for test_case in self.dataset["test_cases"]
            },
        )
        self.assertEqual("EPIC-001", self.dataset["features"][0]["epic_id"])
        self.assertEqual("FEATURE-001", self.dataset["stories"][0]["feature_id"])
        self.assertEqual("US-001", self.dataset["test_cases"][0]["story_id"])
        self.assertEqual("TC-001", self.dataset["bugs"][0]["test_case_id"])
        self.assertEqual([], self.dataset["traceability"]["unresolved_references"])

    def test_free_tier_defaults_and_caps(self) -> None:
        engine = SyntheticDataEngine(self.llm_client)
        self.assertEqual(1, engine.epic_count)
        self.assertEqual(1, engine.features_per_epic)
        self.assertEqual(1, engine.stories_per_feature)
        self.assertEqual(3, engine.test_cases_per_story)
        self.assertEqual(1, engine.bug_sources_per_story)
        self.assertEqual(1, engine.bugs_per_source)

        with self.assertRaisesRegex(ValueError, "Test Cases per Story"):
            SyntheticDataEngine(self.llm_client, test_cases_per_story=6)
        with self.assertRaisesRegex(ValueError, "Total Bugs per Story"):
            SyntheticDataEngine(
                self.llm_client,
                bug_sources_per_story=3,
                bugs_per_source=2,
            )

    def test_dataset_rejects_missing_parent(self) -> None:
        corrupted = copy.deepcopy(self.dataset)
        corrupted["features"][0]["epic_id"] = "EPIC-999"
        with self.assertRaises(ValidationError):
            SyntheticDataset.model_validate(corrupted)

    def test_export_writes_every_artifact_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = save_dataset(self.dataset, Path(directory))
            self.assertEqual(
                {
                    "project",
                    "epics",
                    "features",
                    "stories",
                    "acceptance_criteria",
                    "testcases",
                    "bugs",
                    "traceability",
                },
                set(paths),
            )
            self.assertTrue(all(path.exists() for path in paths.values()))

    def test_azure_upload_uses_ordered_parent_relations(self) -> None:
        client = FakeAzureClient()
        result = AzureWorkItemUploader(client, "Demo Project").upload(self.dataset)
        self.assertEqual(8, result["count"])
        self.assertEqual(
            [
                "/Demo%20Project/_apis/wit/workitems/$Epic",
                "/Demo%20Project/_apis/wit/workitems/$Feature",
                "/Demo%20Project/_apis/wit/workitems/$User%20Story",
                "/Demo%20Project/_apis/wit/workitems/$Test%20Case",
                "/Demo%20Project/_apis/wit/workitems/$Test%20Case",
                "/Demo%20Project/_apis/wit/workitems/$Test%20Case",
                "/Demo%20Project/_apis/wit/workitems/$Test%20Case",
                "/Demo%20Project/_apis/wit/workitems/$Bug",
            ],
            [call[1] for call in client.calls],
        )

    def test_project_scoped_organization_url_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "organization root"):
            AzureDevOpsClient(
                "https://dev.azure.com/example/existing-project",
                "test-pat",
            )


if __name__ == "__main__":
    unittest.main()
