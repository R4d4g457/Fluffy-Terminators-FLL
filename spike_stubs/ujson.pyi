
from typing import Any
"""MicroPython JSON subset."""
def dumps(obj: Any) -> str:
    """Serialize *obj* to a JSON-formatted string.""" ...
def loads(s: str) -> Any:
    """Deserialize JSON document *s* to a Python object.""" ...
