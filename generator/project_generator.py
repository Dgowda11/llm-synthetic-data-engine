import json
from json import JSONDecodeError
from generator.llm import LLMClient 
from utils.prompt_loader import load_prompt
import settings 



class ProjectGenerator:
    def __init__(self, LLMClient)-> str: 
        self.LLMClient = LLMClient

    def generate_project(self, domain: str) -> dict:
        """
        Generate a project structure based on the provided project name and description.
        """
        prompt_template = load_prompt("project", domain=domain)
        project_client = self.LLMClient(model=settings.get_required_env('OPENROUTER_MODEL'))
        try:
            response = project_client.generate(prompt_template)
            print(response)
            return json.loads(response) 
        except Exception as e:
            print(f"Error generating response: {e}")



p1 = ProjectGenerator(LLMClient)
print(p1.generate_project("Banking"))
    