
from typing import Awaitable, Final
"""SPIKE Prime motor module."""

READY: Final[int]  # motor ready for commands
RUNNING: Final[int]  # a command is currently running
STALLED: Final[int]  # stalled condition detected
CANCELED: Final[int]  # command canceled
ERROR: Final[int]  # motor error
DISCONNECTED: Final[int]  # no motor detected on port

COAST: Final[int]  # stop action: let motor coast
BRAKE: Final[int]  # stop action: electrical brake
HOLD: Final[int]   # stop action: hold position (servo)

CONTINUE: Final[int]
SMART_COAST: Final[int]
SMART_BRAKE: Final[int]

CLOCKWISE: Final[int]
COUNTERCLOCKWISE: Final[int]
SHORTEST_PATH: Final[int]
LONGEST_PATH: Final[int]

def absolute_position(port: int) -> int:
    """Return absolute shaft angle on *port* (0..359 degrees).""" ...
def relative_position(port: int) -> int:
    """Return relative position since last reset, in degrees.""" ...
def reset_relative_position(port: int, position: int) -> None:
    """Set the relative position counter on *port* to *position* (usually 0).""" ...
def run(port: int, velocity: int) -> None:
    """Run continuously at *velocity* (deg/sec). Positive rotates clockwise.""" ...
def run_for_degrees(port: int, degrees: int, velocity: int, *, stop: int = BRAKE) -> Awaitable[None]:
    """Rotate by *degrees* at *velocity* (deg/sec). Optionally specify *stop* behavior.""" ...
def run_for_time(port: int, duration: int, velocity: int, *, stop: int = BRAKE, acceleration: int = ..., deceleration: int = ...) -> Awaitable[None]:
    """Run for *duration* milliseconds at *velocity* (deg/sec).""" ...
def run_to_absolute_position(port: int, position: int, velocity: int, *, direction: int = SHORTEST_PATH) -> Awaitable[None]:
    """Rotate to absolute *position* (0..359) at *velocity*. Path depends on *direction*.""" ...
def run_to_relative_position(port: int, position: int, velocity: int) -> Awaitable[None]:
    """Rotate by relative *position* (deg) at *velocity*.""" ...
def set_duty_cycle(port: int, duty_cycle: int) -> None:
    """Drive motor with raw PWM duty cycle *duty_cycle* (-100..100).""" ...
def stop(port: int, *, stop: int = BRAKE) -> None:
    """Stop the motor on *port* (default stop action is BRAKE).""" ...
def velocity(port: int) -> int:
    """Return measured velocity (deg/sec) for motor on *port*.""" ...
