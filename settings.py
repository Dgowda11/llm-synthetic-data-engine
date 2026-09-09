import os 
from dotenv import load_dotenv
load_dotenv()


def get_required_env(var_name: str) -> str:
    """Get the Environment variable or raise an Exception."""
    value  = os.getenv(var_name)
    if value is None or value.strip() == "":
        raise ValueError(f"Environment variable '{var_name}' is required but not set.")
    return value.strip()


def get_env(var_name: str, default: str) -> str:
    """Get a cleaned environment value or return its default."""
    value = os.getenv(var_name)
    if value is None or not value.strip():
        return default
    return value.strip()

