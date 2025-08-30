
from typing import Optional

PAIR_1: int
PAIR_2: int
PAIR_3: int

def pair(pair_id: int, left_port: object, right_port: object) -> None:
    """Bind two motor ports into a controllable pair identified by *pair_id*.""" ...

def move(pair_id: int, steering: int, *, velocity: int) -> None:
    """Run the paired motors with *steering* (-100..100) and forward *velocity* (deg/sec).
    Positive steering turns right (left faster, right slower).""" ...

def move_for_degrees(pair_id: int, steering: int, degrees: int, *, velocity: int) -> None:
    """Move the pair for *degrees* of rotation (measured on right motor) with *steering* at *velocity*.""" ...

def move_for_time(pair_id: int, steering: int, ms: int, *, velocity: int) -> None:
    """Move the pair for *ms* milliseconds with *steering* at *velocity*.""" ...

def stop(pair_id: int) -> None:
    """Stop the paired motors.""" ...
