
from typing import Optional

def absolute_position(p: object) -> int:
    """Return the absolute position of the motor shaft in degrees (0–359).
    Useful for aligning to a physical index mark independent of power cycles.""" ...

def get_duty_cycle(p: object) -> int:
    """Return current duty cycle (PWM %) applied to the motor (-100..100).""" ...

def relative_position(p: object) -> int:
    """Return the motor's relative position in degrees since last reset.""" ...

def reset_relative_position(p: object, position: int) -> None:
    """Set the motor's relative position counter to *position* (typically 0).""" ...

def run(p: object, dps: int) -> None:
    """Run the motor at *dps* (degrees per second). Positive = clockwise, negative = counter-clockwise.""" ...

def run_for_degrees(p: object, degrees: int, velocity: int) -> None:
    """Run the motor for a fixed *degrees* at given *velocity* (deg/sec). Non-blocking on some firmwares.""" ...

def run_for_time(p: object, ms: int, velocity: int) -> None:
    """Run the motor for *ms* milliseconds at *velocity* (deg/sec).""" ...

def run_to_absolute_position(p: object, position: int, velocity: int) -> None:
    """Rotate to an absolute shaft angle *position* (0–359) at *velocity* (deg/sec).""" ...

def run_to_relative_position(p: object, position: int, velocity: int) -> None:
    """Rotate by *position* degrees relative to current angle at *velocity* (deg/sec).""" ...

def set_duty_cycle(p: object, percent: int) -> None:
    """Drive the motor with raw PWM duty *percent* (-100..100).""" ...

def stop(p: object) -> None:
    """Stop the motor using the system's default action (generally brake).""" ...

def velocity(p: object) -> int:
    """Return current measured velocity (deg/sec).""" ...

# Constants (values provided by firmware)
READY: int  # motor ready
RUNNING: int  # motor running
STALLED: int  # stalled
CANCELED: int  # command canceled
ERROR: int  # error state
DISCONNECTED: int  # no motor detected

COAST: int  # stop action: coast
BRAKE: int  # stop action: brake
HOLD: int   # stop action: hold

CONTINUE: int
SMART_COAST: int
SMART_BRAKE: int

CLOCKWISE: int
COUNTERCLOCKWISE: int
SHORTEST_PATH: int
LONGEST_PATH: int
