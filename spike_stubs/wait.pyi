
from typing import Callable

def for_seconds(sec: float) -> None:
    """Block for *sec* seconds (fractional allowed).""" ...

def until(predicate: Callable[[], bool]) -> None:
    """Block until *predicate()* returns True, polling periodically.""" ...
