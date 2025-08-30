
from typing import Tuple

def color(p: object) -> str:
    """Return the detected color name ('red','green','blue','yellow','magenta','orange','azure','black','white') or '' if unknown.""" ...

def reflection(p: object) -> int:
    """Return reflected light intensity in percent (0..100).""" ...

def rgbi(p: object) -> Tuple[int, int, int, int]:
    """Return a 4-tuple of raw (R,G,B,illuminance) values.""" ...
