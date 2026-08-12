import os 
from dotenv import load_dotenv
load_dotenv()


def get_required_env(var_name: str) -> str:
    """Get the Environment variable or raise an Exception."""
    value  = os.getenv(var_name)
    if value is None or value.strip() == "":
        raise ValueError(f"Environment variable '{var_name}' is required but not set.")
    return value.strip()

