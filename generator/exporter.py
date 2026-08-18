import json
from pathlib import Path


def save_json(data: dict[str, object], output_path: Path) -> Path:
    """
    Save the provided data as a JSON file at the specified output path """
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
    return output_path