from generator.llm import LLMClient
from utils.prompt_loader import load_prompt
from utils.helpers import parse_json_object, require_string, require_string_list

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
        response = self.llm_client.generate(prompt_template, json_output=True)
        project = parse_json_object(response, "project")
        require_string(project, "name", "Project")
        require_string(project, "description", "Project")
        require_string_list(project, "objectives", "Project")
        require_string_list(project, "success_criteria", "Project")
        project["domain"] = cleaned_domain
        return project
            

if __name__ == "__main__":
    call_client = LLMClient()
    p1 = ProjectGenerator(call_client)
    print(p1.generate("Finance"))
    