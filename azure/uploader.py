import time
from typing import Any

from azure.connection import AzureDevOpsClient


class AzureProjectUploader:
	def __init__(
		self,
		client: AzureDevOpsClient,
		process_template_id: str,
		poll_interval: float = 2,
		max_wait_seconds: float = 600,
	) -> None:
		self.client = client
		self.process_template_id = process_template_id.strip()
		if not self.process_template_id:
			raise ValueError("Azure DevOps process template ID cannot be empty.")
		if poll_interval <= 0 or max_wait_seconds <= 0:
			raise ValueError("Polling values must be greater than zero.")
		self.poll_interval = poll_interval
		self.max_wait_seconds = max_wait_seconds

	def create_project(self, project: dict[str, object]) -> dict[str, Any]:
		name = project.get("name")
		description = project.get("description")
		if not isinstance(name, str) or not name.strip():
			raise ValueError("Project JSON must contain a non-empty name.")
		if not isinstance(description, str) or not description.strip():
			raise ValueError("Project JSON must contain a non-empty description.")

		body = {
			"name": name.strip(),
			"description": description.strip(),
			"visibility": "private",
			"capabilities": {
				"versioncontrol": {"sourceControlType": "Git"},
				"processTemplate": {
					"templateTypeId": self.process_template_id,
				},
			},
		}
		operation = self.client.request(
			"POST",
			"/_apis/projects",
			params={"api-version": "7.1"},
			json_body=body,
		)
		return self._wait_for_operation(operation)

	def _wait_for_operation(
		self,
		operation: dict[str, Any],
	) -> dict[str, Any]:
		operation_url = operation.get("url")
		if not isinstance(operation_url, str) or not operation_url:
			raise RuntimeError("Azure DevOps did not return an operation URL.")

		deadline = time.monotonic() + self.max_wait_seconds
		current_operation = operation
		while time.monotonic() < deadline:
			status = current_operation.get("status")
			if status == "succeeded":
				return current_operation
			if status in {"failed", "cancelled"}:
				message = current_operation.get("resultMessage", "No details provided.")
				raise RuntimeError(f"Azure project creation {status}: {message}")

			time.sleep(self.poll_interval)
			current_operation = self.client.request(
				"GET",
				operation_url,
				params={"api-version": "7.1"},
			)

		raise TimeoutError("Azure project creation did not finish in time.")
