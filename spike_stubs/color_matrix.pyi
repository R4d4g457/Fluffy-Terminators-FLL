
from typing import Tuple, List
"""Color Matrix peripheral API (5x5 LED with per-pixel color+intensity).
Use tuples of ``(color, intensity)`` where:
- ``color`` is a constant from the ``color`` module (e.g. ``color.RED``)
- ``intensity`` is 0..100 (percentage)
The matrix is indexed by ``x`` (0..4, left→right) and ``y`` (0..4, top→bottom).
"""

def clear(port: int) -> None:
    """Turn off all pixels on the matrix connected to *port*.""" ...

def get_pixel(port: int, x: int, y: int) -> Tuple[int, int]:
    """Return the (color, intensity) tuple at pixel (*x*, *y*).""" ...

def set_pixel(port: int, x: int, y: int, pixel: Tuple[int, int]) -> None:
    """Set pixel (*x*, *y*) to *(color, intensity)* where color is from ``color`` and intensity is 0..100.""" ...

def show(port: int, pixels: List[Tuple[int, int]]) -> None:
    """Display a flattened 25-length list of *(color, intensity)* tuples on the 5x5 matrix.
    The list maps row-major: index = y*5 + x.""" ...
