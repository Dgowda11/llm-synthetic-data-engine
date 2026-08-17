import json
from json import JSONDecodeError
from generator.llm import LLMClient 
from utils.prompt_loader import load_prompt




class ProjectGenerator:
    def __init__(self,llm_client: LLMClient)-> None: 
        self.llm_client = llm_client

    def generate(self, domain: dict[str, object]) -> dict[str, object]:
        """
        Generate a project structure based on the provided project name and description.
        """
        if not domain or not domain.strip():
            raise ValueError("Domain cannot be empty.")
        prompt_template = load_prompt("project", domain=domain)
        
        try:
            response = self.llm_client.generate(prompt_template)
            parsed_response = json.loads(response)
            if not isinstance(parsed_response, dict):
                raise ValueError("The model returned a response that is not a valid JSON object.")  
            return parsed_response

        except JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}") from e
            

if __name__ == "__main__":
    call_client = LLMClient()
    p1 = ProjectGenerator(call_client)
    print(p1.generate("Finance"))
    