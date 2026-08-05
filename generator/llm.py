import config
from openai import OpenAI




def generate_text(prompt: str) -> str:
    """
    Generate text using the LLM model """
    # Get the API key from the config module
    api_key = config.get_required_env('openrouter_api_key')
    base_url = 'https://openrouter.ai/api/v1/chat/completions'
    gpt = OpenAI(api_key=api_key, base_url=base_url)
    response = gpt.chat.completions.create(
    model=config.get_required_env('openrouter_model'),
    messages=[{"role": "user", "content": prompt}],)
    return response.choices[0].message.content


generate_text('Hi Buddy, How are you doing?')