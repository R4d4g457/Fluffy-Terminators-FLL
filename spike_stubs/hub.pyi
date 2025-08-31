
from typing import Awaitable, Tuple, List

"""SPIKE Prime hub module with submodules: button, light, light_matrix, motion_sensor, port, sound."""

# --- Button submodule ---
class _button:
    LEFT: int
    RIGHT: int
    CENTER: int
    def pressed(self, button: int) -> int:
        """Return milliseconds the *button* has been held down (0 if not pressed).""" ...
button = _button()

# --- Light submodule ---
class _light:
    POWER: int
    CONNECT: int
    def color(self, which: int, color: int) -> None:
        """Set hub light *which* (POWER or CONNECT) to the given *color* constant.""" ...
light = _light()

# --- Light Matrix submodule ---
class _light_matrix:

    # Built-in images (subset)
    IMAGE_HEART: int
    IMAGE_HEART_SMALL: int
    IMAGE_HAPPY: int
    IMAGE_SMILE: int
    IMAGE_SAD: int
    IMAGE_CONFUSED: int
    IMAGE_ANGRY: int
    IMAGE_ASLEEP: int
    IMAGE_SURPRISED: int
    IMAGE_SILLY: int
    IMAGE_FABULOUS: int
    IMAGE_MEH: int
    # ... (many more images exist, subset here)

    def clear(self) -> None:
        """Turn off all pixels on the 5x5 matrix.""" ...
    def get_orientation(self) -> int:
        """Return which side of the hub is currently up (orientation constant).""" ...
    def set_orientation(self, top: int) -> int:
        """Define which face of the hub should be considered 'top' for display rotation.""" ...
    def get_pixel(self, x: int, y: int) -> int:
        """Return brightness (0..100) of pixel at (*x*, *y*).""" ...
    def set_pixel(self, x: int, y: int, intensity: int) -> None:
        """Set brightness (0..100) of pixel at (*x*, *y*).""" ...
    def show(self, pixels: List[int]) -> None:
        """Display a 25-length list of brightness values (row-major order).""" ...
    def show_image(self, image: int) -> None:
        """Display a built-in image constant (IMAGE_*).""" ...
    def write(self, text: str, intensity: int = 100, time_per_character: int = 500) -> Awaitable[None]:
        """Scroll *text* across the matrix at given *intensity* and speed.""" ...
light_matrix = _light_matrix()

# --- Motion Sensor submodule ---
class _motion_sensor:
    TOP: int
    FRONT: int
    RIGHT: int
    BOTTOM: int
    BACK: int
    LEFT: int

    def acceleration(self) -> Tuple[int, int, int]:
        """Return acceleration vector (x,y,z) in mG or similar units.""" ...
    def angular_velocity(self) -> Tuple[int, int, int]:
        """Return angular velocity (x,y,z) in deg/sec (scaled).""" ...
    def gesture(self) -> int:
        """Return last detected gesture (tap, shake, etc.).""" ...
    def stable(self) -> bool:
        """Return True if sensor values are stable.""" ...
    def tap_count(self) -> int:
        """Return number of taps detected since last reset.""" ...
    def tilt_angles(self) -> Tuple[int, int, int]:
        """Return (roll, pitch, yaw) angles of the hub (deg or decidegrees).""" ...
    def up_face(self) -> int:
        """Return which face of the hub is pointing up (orientation constant).""" ...
    def reset_yaw(self, angle: int) -> None:
        """Reset yaw reference to *angle*.""" ...
    def get_yaw(self) -> int:
        """Return current yaw angle relative to last reset.""" ...
    def set_yaw(self, yaw: int) -> None:
        """Force yaw reading to *yaw* (manual override).""" ...
motion_sensor = _motion_sensor()

# --- Port submodule ---
class _port:
    A: int
    B: int
    C: int
    D: int
    E: int
    F: int
port = _port()

# --- Sound submodule ---
class _sound:
    def beep(self, frequency: int = 440, ms: int = 200) -> Awaitable[None]:
        """Play a beep at *frequency* Hz for *ms* milliseconds.""" ...
    def stop(self) -> None:
        """Stop any ongoing beep sound.""" ...
sound = _sound()
