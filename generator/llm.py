import config
from openai import OpenAI




def generate_text(prompt: str) -> str:
    """
    Generate text using the LLM model """
    # Get the API key from the config module
    api_key = config.get_required_env('OPENROUTER_API_KEY')
    base_url = 'https://openrouter.ai/api/v1'
    gpt = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
    response = gpt.chat.completions.create(
    model=config.get_required_env('OPENROUTER_MODEL'),
    messages=[{"role": "user", "content": prompt}],)
    return response.choices[0].message.content


if __name__ == "__main__":
    prompt = "Write a short story about a robot learning to love."
    generated_text = generate_text(prompt)
    print(generated_text)