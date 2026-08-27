from pathlib import Path

import settings
from azure.connection import AzureDevOpsClient
from azure.uploader import AzureProjectUploader
from azure.workitems import AzureWorkItemUploader
from generator.exporter import save_dataset, save_json
from generator.llm import LLMClient
from generator.pipeline import SyntheticDataEngine
from utils.helpers import require_string


OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "output"


def run(domain: str) -> dict[str, object]:
	organization_url = settings.get_required_env("AZURE_DEVOPS_ORG")
	azure_pat = settings.get_required_env("AZURE_DEVOPS_PAT")
	process_template_id = settings.get_required_env(
		"AZURE_DEVOPS_PROCESS_TEMPLATE_ID"
	)
	llm_client = LLMClient()
	dataset = SyntheticDataEngine(llm_client).generate(domain)
	saved_paths = save_dataset(dataset, OUTPUT_DIRECTORY)

	project = dataset.get("project")
	if not isinstance(project, dict):
		raise ValueError("Generated dataset does not contain a project object.")
	project_name = require_string(project, "name", "Project")

	azure_client = AzureDevOpsClient(
		organization_url=organization_url,
		pat=azure_pat,
	)
	project_uploader = AzureProjectUploader(
		azure_client,
		process_template_id=process_template_id,
	)
	project_operation = project_uploader.create_project(project)
	upload_path = OUTPUT_DIRECTORY / "azure_upload.json"

	def save_upload_progress(progress: dict[str, object]) -> None:
		save_json(
			{
				"project_operation": project_operation,
				"work_item_upload": progress,
			},
			upload_path,
		)

	work_item_upload = AzureWorkItemUploader(
		azure_client,
		project_name,
		progress_callback=save_upload_progress,
	).upload(dataset)
	work_item_upload["status"] = "succeeded"
	save_upload_progress(work_item_upload)
	return {
		"dataset": dataset,
		"saved_paths": {
			name: str(path) for name, path in saved_paths.items()
		},
		"azure_operation": project_operation,
		"work_item_upload": work_item_upload,
		"azure_upload_path": str(upload_path),
	}


if __name__ == "__main__":
	business_domain = input("Enter business domain: ").strip()
	result = run(business_domain)
	dataset = result["dataset"]
	project = dataset["project"]
	project_name = project["name"]
	work_item_count = result["work_item_upload"]["count"]
	print(f"Saved generated data to {OUTPUT_DIRECTORY}")
	print(f"Created Azure DevOps project: {project_name}")
	print(f"Created {work_item_count} linked Azure DevOps work items")
