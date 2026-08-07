import config
from openai import OpenAI

from openai import(
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)


def generate_text(prompt: str) -> str:
    """
    Generate text using the LLM model """
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("Prompt cannot be empty.")
    # Get the API key from the config module
    api_key = config.get_required_env('OPENROUTER_API_KEY')
    base_url = 'https://openrouter.ai/api/v1'
    gpt = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
    try:
        response = gpt.chat.completions.create(
        model=config.get_required_env('OPENROUTER_MODEL'),
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

    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}") from e
    response_text =  response.choices[0].message.content
    if response_text is None or response_text.strip() == "":
        raise ValueError("The model returned an empty response.")
    return response_text.strip()

if __name__ == "__main__":
    prompt = "Hey there! Can you tell me a joke?"
    generated_text = generate_text(prompt)
    print(generated_text)