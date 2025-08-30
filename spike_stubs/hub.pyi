
from typing import Tuple

class _Port:
    """Logical hub ports used when addressing motors/sensors (A..F)."""
    A: object
    B: object
    C: object
    D: object
    E: object
    F: object
port: _Port

class _MotionSensor:
    """Hub motion sensor interface (units are decidegrees for tilt_angles)."""
    def tilt_angles(self) -> Tuple[int, int, int]:
        """Return (yaw, pitch, roll) in 0.1° units (decidegrees).""" ...
    def reset_yaw(self, zero: int) -> None:
        """Reset yaw reference to *zero* (usually 0).""" ...
motion_sensor: _MotionSensor
