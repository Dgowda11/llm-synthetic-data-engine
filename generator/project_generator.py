from generator.llm import LLMClient
from generator.validation import generate_validated
from models import Project
from utils.prompt_loader import load_prompt

class ProjectGenerator:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate(self, domain: str) -> dict[str, object]:
        """
        Generate a project structure based on the provided project name and description.
        """
        cleaned_domain = domain.strip()
        if not cleaned_domain:
            raise ValueError("Domain cannot be empty.")
        prompt_template = load_prompt("project", domain=cleaned_domain)
        validated = generate_validated(
            self.llm_client,
            prompt_template,
            Project,
            "project",
            semantic_validator=lambda project: _validate_domain(
                project, cleaned_domain
            ),
        )
        project = validated.model_dump()
        project["domain"] = cleaned_domain
        return project


def _validate_domain(project: Project, expected_domain: str) -> None:
    if project.domain.casefold() != expected_domain.casefold():
        raise ValueError(
            f"Project domain must exactly match '{expected_domain}'."
        )
            

if __name__ == "__main__":
    call_client = LLMClient()
    p1 = ProjectGenerator(call_client)
    print(p1.generate("Finance"))
    