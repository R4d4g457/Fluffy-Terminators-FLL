
from typing import Any, Tuple
"""MicroPython struct subset for packing and unpacking binary data."""
def pack(fmt: str, *values: Any) -> bytes:
    """Pack *values* according to struct *fmt*, returning a new bytes object.""" ...
def unpack(fmt: str, data: bytes) -> Tuple[Any, ...]:
    """Unpack *data* according to struct *fmt*, returning a tuple of values.""" ...
