from html import escape
from collections.abc import Callable
from typing import Any, cast
from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, tostring

from azure.connection import AzureDevOpsClient
from utils.helpers import require_string, require_string_list


class AzureWorkItemUploader:
	def __init__(
		self,
		client: AzureDevOpsClient,
		project_name: str,
		progress_callback: Callable[[dict[str, object]], None] | None = None,
	) -> None:
		self.client = client
		self.project_name = project_name.strip()
		if not self.project_name:
			raise ValueError("Azure DevOps project name cannot be empty.")
		self.progress_callback = progress_callback

	def upload(self, dataset: dict[str, object]) -> dict[str, object]:
		epics = _get_collection(dataset, "epics")
		features = _get_collection(dataset, "features")
		stories = _get_collection(dataset, "stories")
		test_cases = _get_collection(dataset, "test_cases")
		bugs = _get_collection(dataset, "bugs")

		created: dict[str, dict[str, object]] = {}
		records: list[dict[str, object]] = []

		for epic in epics:
			synthetic_id = require_string(epic, "id", "Epic")
			item = self._create_epic(epic)
			_record_created_item(created, records, synthetic_id, "Epic", item)
			self._report_progress(records)

		for feature in features:
			synthetic_id = require_string(feature, "id", "Feature")
			parent_url = _require_created_url(
				created, require_string(feature, "epic_id", "Feature")
			)
			item = self._create_feature(feature, parent_url)
			_record_created_item(created, records, synthetic_id, "Feature", item)
			self._report_progress(records)

		for story in stories:
			synthetic_id = require_string(story, "id", "Story")
			parent_url = _require_created_url(
				created, require_string(story, "feature_id", "Story")
			)
			item = self._create_story(story, parent_url)
			_record_created_item(created, records, synthetic_id, "User Story", item)
			self._report_progress(records)

		for test_case in test_cases:
			synthetic_id = require_string(test_case, "id", "Test case")
			story_id = require_string(test_case, "story_id", "Test case")
			story_url = _require_created_url(created, story_id)
			item = self._create_test_case(test_case, story_url)
			_record_created_item(created, records, synthetic_id, "Test Case", item)
			self._report_progress(records)

		for bug in bugs:
			synthetic_id = require_string(bug, "id", "Bug")
			test_case_url = _require_created_url(
				created, require_string(bug, "test_case_id", "Bug")
			)
			story_url = _require_created_url(
				created, require_string(bug, "story_id", "Bug")
			)
			item = self._create_bug(bug, test_case_url, story_url)
			_record_created_item(created, records, synthetic_id, "Bug", item)
			self._report_progress(records)

		return {
			"project": self.project_name,
			"count": len(records),
			"work_items": records,
		}

	def _report_progress(self, records: list[dict[str, object]]) -> None:
		if self.progress_callback is None:
			return
		self.progress_callback(
			{
				"project": self.project_name,
				"count": len(records),
				"status": "in_progress",
				"work_items": list(records),
			}
		)

	def _create_epic(self, epic: dict[str, object]) -> dict[str, Any]:
		description = (
			f"<p>{escape(require_string(epic, 'description', 'Epic'))}</p>"
			"<h3>Business value</h3>"
			f"<p>{escape(require_string(epic, 'business_value', 'Epic'))}</p>"
		)
		return self._create_work_item(
			"Epic",
			require_string(epic, "id", "Epic"),
			{
				"System.Title": require_string(epic, "title", "Epic"),
				"System.Description": description,
				"Microsoft.VSTS.Common.Priority": _priority_number(epic),
			},
		)

	def _create_feature(
		self, feature: dict[str, object], parent_url: str
	) -> dict[str, Any]:
		return self._create_work_item(
			"Feature",
			require_string(feature, "id", "Feature"),
			{
				"System.Title": require_string(feature, "title", "Feature"),
				"System.Description": _paragraph(
					require_string(feature, "description", "Feature")
				),
				"Microsoft.VSTS.Common.Priority": _priority_number(feature),
			},
			parent_url=parent_url,
		)

	def _create_story(
		self, story: dict[str, object], parent_url: str
	) -> dict[str, Any]:
		criteria = require_string_list(story, "acceptance_criteria", "Story")
		story_points = story.get("story_points")
		if not isinstance(story_points, int) or isinstance(story_points, bool):
			raise ValueError("Story points must be an integer.")
		return self._create_work_item(
			"User Story",
			require_string(story, "id", "Story"),
			{
				"System.Title": require_string(story, "title", "Story"),
				"System.Description": _paragraph(
					require_string(story, "description", "Story")
				),
				"Microsoft.VSTS.Common.AcceptanceCriteria": _html_list(criteria),
				"Microsoft.VSTS.Scheduling.StoryPoints": story_points,
				"Microsoft.VSTS.Common.Priority": _priority_number(story),
			},
			parent_url=parent_url,
		)

	def _create_test_case(
		self, test_case: dict[str, object], story_url: str
	) -> dict[str, Any]:
		preconditions = test_case.get("preconditions")
		if not isinstance(preconditions, list):
			raise ValueError("Test-case preconditions must be an array.")
		clean_preconditions = [
			value.strip()
			for value in preconditions
			if isinstance(value, str) and value.strip()
		]
		description = (
			"<h3>Preconditions</h3>"
			f"{_html_list(clean_preconditions)}"
			"<h3>Covered acceptance criterion</h3>"
			f"{_paragraph(require_string(test_case, 'acceptance_criteria', 'Test case'))}"
			"<h3>Overall expected result</h3>"
			f"{_paragraph(require_string(test_case, 'expected_result', 'Test case'))}"
		)
		return self._create_work_item(
			"Test Case",
			require_string(test_case, "id", "Test case"),
			{
				"System.Title": require_string(test_case, "title", "Test case"),
				"System.Description": description,
				"Microsoft.VSTS.TCM.Steps": _test_steps_xml(test_case),
				"Microsoft.VSTS.Common.Priority": _priority_number(test_case),
			},
			parent_url=story_url,
			additional_relations=[
				{
					"rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
					"url": story_url,
					"attributes": {"comment": "Synthetic test coverage"},
				}
			],
		)

	def _create_bug(
		self,
		bug: dict[str, object],
		test_case_url: str,
		story_url: str,
	) -> dict[str, Any]:
		reproduction = (
			"<h3>Steps to reproduce</h3>"
			f"{_html_list(require_string_list(bug, 'steps_to_reproduce', 'Bug'))}"
			"<h3>Expected result</h3>"
			f"{_paragraph(require_string(bug, 'expected_result', 'Bug'))}"
			"<h3>Actual result</h3>"
			f"{_paragraph(require_string(bug, 'actual_result', 'Bug'))}"
		)
		return self._create_work_item(
			"Bug",
			require_string(bug, "id", "Bug"),
			{
				"System.Title": require_string(bug, "title", "Bug"),
				"System.Description": _paragraph(
					require_string(bug, "description", "Bug")
				),
				"Microsoft.VSTS.TCM.ReproSteps": reproduction,
				"Microsoft.VSTS.Common.Severity": _severity_value(bug),
				"Microsoft.VSTS.Common.Priority": _priority_number(bug),
			},
			parent_url=test_case_url,
			additional_relations=[
				{
					"rel": "System.LinkTypes.Related",
					"url": story_url,
					"attributes": {"comment": "Source user story"},
				}
			],
		)

	def _create_work_item(
		self,
		work_item_type: str,
		synthetic_id: str,
		fields: dict[str, object],
		*,
		parent_url: str | None = None,
		additional_relations: list[dict[str, object]] | None = None,
	) -> dict[str, Any]:
		fields["System.Tags"] = f"SyntheticData; {synthetic_id}"
		operations: list[dict[str, object]] = [
			{"op": "add", "path": f"/fields/{name}", "value": value}
			for name, value in fields.items()
		]
		if parent_url:
			operations.append(
				{
					"op": "add",
					"path": "/relations/-",
					"value": {
						"rel": "System.LinkTypes.Hierarchy-Reverse",
						"url": parent_url,
						"attributes": {"comment": "Synthetic parent"},
					},
				}
			)
		for relation in additional_relations or []:
			operations.append(
				{"op": "add", "path": "/relations/-", "value": relation}
			)

		project = quote(self.project_name, safe="")
		item_type = quote(work_item_type, safe="")
		return self.client.request(
			"POST",
			f"/{project}/_apis/wit/workitems/${item_type}",
			params={"api-version": "7.1", "$expand": "relations"},
			json_body=operations,
			headers={"Content-Type": "application/json-patch+json"},
		)


def _get_collection(
	dataset: dict[str, object], collection_name: str
) -> list[dict[str, object]]:
	value = dataset.get(collection_name)
	if not isinstance(value, list):
		raise ValueError(f"Dataset must contain a '{collection_name}' array.")
	return cast(list[dict[str, object]], value)


def _record_created_item(
	created: dict[str, dict[str, object]],
	records: list[dict[str, object]],
	synthetic_id: str,
	work_item_type: str,
	item: dict[str, Any],
) -> None:
	azure_id = item.get("id")
	url = item.get("url")
	if not isinstance(azure_id, int) or not isinstance(url, str) or not url:
		raise RuntimeError("Azure DevOps returned an incomplete work item.")
	record: dict[str, object] = {
		"synthetic_id": synthetic_id,
		"azure_id": azure_id,
		"work_item_type": work_item_type,
		"url": url,
	}
	created[synthetic_id] = record
	records.append(record)


def _require_created_url(
	created: dict[str, dict[str, object]], synthetic_id: str
) -> str:
	record = created.get(synthetic_id)
	if record is None:
		raise ValueError(f"Parent '{synthetic_id}' has not been uploaded.")
	url = record.get("url")
	if not isinstance(url, str) or not url:
		raise RuntimeError(f"Parent '{synthetic_id}' has no Azure URL.")
	return url


def _priority_number(artifact: dict[str, object]) -> int:
	value = require_string(artifact, "priority", "Work item").title()
	priorities = {"High": 1, "Medium": 2, "Low": 3}
	if value not in priorities:
		raise ValueError("Priority must be High, Medium, or Low.")
	return priorities[value]


def _severity_value(bug: dict[str, object]) -> str:
	value = require_string(bug, "severity", "Bug").title()
	severities = {
		"Critical": "1 - Critical",
		"High": "2 - High",
		"Medium": "3 - Medium",
		"Low": "4 - Low",
	}
	if value not in severities:
		raise ValueError("Bug severity is invalid.")
	return severities[value]


def _paragraph(value: str) -> str:
	return f"<p>{escape(value)}</p>"


def _html_list(values: list[str]) -> str:
	if not values:
		return "<p>None</p>"
	return "<ul>" + "".join(f"<li>{escape(value)}</li>" for value in values) + "</ul>"


def _test_steps_xml(test_case: dict[str, object]) -> str:
	steps = test_case.get("steps")
	if not isinstance(steps, list) or not steps:
		raise ValueError("Test case must contain at least one step.")

	root = Element("steps", {"id": "0", "last": str(len(steps))})
	for index, step in enumerate(steps, start=1):
		if not isinstance(step, dict):
			raise ValueError("Every test step must be a JSON object.")
		step_element = SubElement(
			root, "step", {"id": str(index), "type": "ValidateStep"}
		)
		action = SubElement(
			step_element, "parameterizedString", {"isformatted": "true"}
		)
		action.text = f"<DIV><P>{require_string(step, 'action', 'Test step')}</P></DIV>"
		expected = SubElement(
			step_element, "parameterizedString", {"isformatted": "true"}
		)
		expected.text = (
			f"<DIV><P>{require_string(step, 'expected_result', 'Test step')}</P></DIV>"
		)
		SubElement(step_element, "description")
	return tostring(root, encoding="unicode")
