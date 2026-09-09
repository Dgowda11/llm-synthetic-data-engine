import json
from json import JSONDecodeError

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
                 max_tokens:int=4000,
                 json_attempts: int = 3,) -> None:
        self.provider = settings.get_env("LLM_PROVIDER", "nvidia").lower()
        api_key, base_url, self.model = _load_provider_config(self.provider)
        if not self.model:
            raise ValueError("Model name cannot be empty.")
        self.temperature = temperature
        if temperature < 0 or temperature > 2:
            raise ValueError("Temperature must be between 0 and 2.")
        self.max_tokens = max_tokens
        if max_tokens <= 0:
            raise ValueError("Max tokens must be a positive integer.")
        self.json_attempts = json_attempts
        if json_attempts <= 0:
            raise ValueError("JSON attempts must be a positive integer.")
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
        

    def generate(self, prompt: str, json_output: bool = False) -> str:
        """
        Generate text using the LLM model """
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise ValueError("Prompt cannot be empty.")
        attempts = self.json_attempts if json_output else 1
        last_json_error: JSONDecodeError | None = None
        for _ in range(attempts):
            try:
                response = self._create_completion(cleaned_prompt, json_output)
            except AuthenticationError as error:
                raise RuntimeError(f"Authentication error: {error}") from error
            except RateLimitError as error:
                raise RuntimeError(f"Rate limit error: {error}") from error
            except APITimeoutError as error:
                raise RuntimeError(f"API timeout error: {error}") from error
            except APIConnectionError as error:
                raise RuntimeError(f"API connection error: {error}") from error
            except APIStatusError as error:
                raise RuntimeError(
                    f"API status error ({error.status_code}): {error}"
                ) from error

            if response.choices[0].finish_reason == "length":
                raise RuntimeError(
                    "The model response was truncated because it reached the token limit."
                )
            response_text = response.choices[0].message.content
            if response_text is None or not response_text.strip():
                if json_output:
                    continue
                raise ValueError("The model returned an empty response.")

            cleaned_response = _remove_json_fence(response_text)
            if not json_output:
                return cleaned_response
            try:
                json.loads(cleaned_response)
            except JSONDecodeError as error:
                last_json_error = error
                continue
            return cleaned_response

        raise ValueError(
            f"The model failed to return valid JSON after {attempts} attempts."
        ) from last_json_error

    def _create_completion(self, prompt: str, json_output: bool):
        temperature = min(self.temperature, 0.2) if json_output else self.temperature
        request = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if not json_output:
            return self.client.chat.completions.create(**request)

        try:
            return self.client.chat.completions.create(
                **request,
                response_format={"type": "json_object"},
            )
        except APIStatusError as error:
            if error.status_code not in {400, 422}:
                raise
            return self.client.chat.completions.create(**request)


def _load_provider_config(provider: str) -> tuple[str, str, str]:
    if provider == "nvidia":
        return (
            settings.get_required_env("NVIDIA_API_KEY"),
            settings.get_env(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
            ),
            settings.get_required_env("NVIDIA_MODEL"),
        )
    if provider == "openrouter":
        return (
            settings.get_required_env("OPENROUTER_API_KEY"),
            settings.get_env(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            settings.get_required_env("OPENROUTER_MODEL"),
        )
    raise ValueError(
        "LLM_PROVIDER must be either 'nvidia' or 'openrouter'."
    )


def _remove_json_fence(response: str) -> str:
    cleaned_response = response.strip().lstrip("\ufeff")
    lines = cleaned_response.splitlines()
    if (
        len(lines) >= 3
        and lines[0].strip().lower() in {"```", "```json"}
        and lines[-1].strip() == "```"
    ):
        return "\n".join(lines[1:-1]).strip()
    return cleaned_response

