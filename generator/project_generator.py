import json
from json import JSONDecodeError
from generator.llm import LLM 
from utils.prompt_loader import PromptLoader



class ProjectGenerator:
    def __init__(self, llm: LLM, prompt_loader: PromptLoader)-> str: 
        self.llm = llm
        self.prompt_loader = prompt_loader
    