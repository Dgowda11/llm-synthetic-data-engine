import settings 
from openai import OpenAI

from openai import(
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

class LLMClient:
    def __init__(self,
                 temperature:float=1,
                 max_tokens:int=1000,) -> None:
        self.model = settings.get_required_env('OPENROUTER_MODEL')
        if not self.model:
            raise ValueError("Model name cannot be empty.")
        self.temperature = temperature
        if temperature < 0 or temperature > 2:
            raise ValueError("Temperature must be between 0 and 2.")
        self.max_tokens = max_tokens
        if max_tokens <= 0:
            raise ValueError("Max tokens must be a positive integer.")
        self.client = OpenAI(api_key=settings.get_required_env('OPENROUTER_API_KEY'), base_url='https://openrouter.ai/api/v1', timeout=30)
        

    def generate(self,prompt: str) -> str:
        """
        Generate text using the LLM model """
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise ValueError("Prompt cannot be empty.")
        # Get the API key from the config module
        gpt = self.client
        try:
            response = gpt.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": cleaned_prompt}],)
        except AuthenticationError as e:
            raise RuntimeError(f"Authentication error: {e}") from e

        except RateLimitError as e:
            raise RuntimeError(f"Rate limit error: {e}") from e

        except APITimeoutError as e:
            raise RuntimeError(f"API timeout error: {e}") from e

        except APIConnectionError as e:
            raise RuntimeError(f"API connection error: {e}") from e

        except APIStatusError as e:
            raise RuntimeError(
                f"API status error ({e.status_code}): {e}"
            ) from e
        response_text =  response.choices[0].message.content
        if response_text is None or response_text.strip() == "":
            raise ValueError("The model returned an empty response.")
        return response_text.strip()

