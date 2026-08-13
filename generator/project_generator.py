import json
from json import JSONDecodeError
from generator.llm import LLMClient 
from utils.prompt_loader import load_prompt




class ProjectGenerator:
    def __init__(self,llm_client: LLMClient)-> None: 
        self.llmclient = llm_client

    def generate_project(self, domain: str) -> dict:
        """
        Generate a project structure based on the provided project name and description.
        """
        prompt_template = load_prompt("project", domain=domain)
        
        try:
            response = self.llmclient.generate(prompt_template)
            return json.loads(response)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}") from e
            print(f"Invalid JSON from LLM: {e}")
            print("Raw response:")
            print(response)
            raise

call_client = LLMClient()
p1 = ProjectGenerator(call_client)
print(p1.generate_project("Banking"))
    