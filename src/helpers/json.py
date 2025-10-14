import json
from pathlib import Path
from typing import Any, Dict


def read_json(path: Path) -> Dict[str, Any]:
    """
    Read a JSON file and return its contents as a dictionary.

    Args:
        path (Path): Path to the JSON file.

    Returns:
        dict: Parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Write a dictionary to a JSON file with indentation.

    Args:
        path (Path): Path to the JSON file.
        data (dict): Data to write.
    """
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
