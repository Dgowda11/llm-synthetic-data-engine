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


def get_positive_float_env(var_name: str, default: float) -> float:
    """Get a positive floating-point environment setting."""
    raw_value = get_env(var_name, str(default))
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"Environment variable '{var_name}' must be a number.") from error
    if value <= 0:
        raise ValueError(f"Environment variable '{var_name}' must be greater than zero.")
    return value


def get_non_negative_int_env(var_name: str, default: int) -> int:
    """Get a non-negative integer environment setting."""
    raw_value = get_env(var_name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"Environment variable '{var_name}' must be an integer.") from error
    if value < 0:
        raise ValueError(f"Environment variable '{var_name}' cannot be negative.")
    return value

