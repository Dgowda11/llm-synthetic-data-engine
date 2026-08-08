from pathlib import Path
from string import Template


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PROMPT_FILES = {
    "project": "project_prompt.md",
    "epic": "epic_prompt.md",
    "feature": "feature_prompt.md",
    "story": "story_prompt.md",
    "test_case": "testcase_prompt.md",
    "bug": "bug_prompt.md",
    "traceability": "traceability_prompt.md",


}


def load_prompt(prompt_name: str, **variables: str) -> str:
    """Load a named prompt and substitute its required variables."""
    try:
        filename = PROMPT_FILES[prompt_name]
    except KeyError:
        raise ValueError(f"Unknown prompt name: '{prompt_name}'.") from None

    prompt_path = PROMPTS_DIR / filename
    template = Template(prompt_path.read_text(encoding="utf-8"))

    try:
        return template.substitute(**variables)
    except KeyError as error:
        missing_variable = error.args[0]
        raise ValueError(
            f"Prompt '{prompt_name}' requires variable '{missing_variable}'."
        ) from None



