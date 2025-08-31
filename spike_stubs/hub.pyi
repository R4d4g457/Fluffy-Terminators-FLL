from typing import Awaitable, Tuple

# Submodule: button
class _button:
    LEFT: int
    RIGHT: int
    def pressed(self, button: int) -> int: ...  # returns ms pressed; 0 if not pressed
button = _button()

# Submodule: light
class _light:
    POWER: int
    CONNECT: int
    def color(self, which: int, color: int) -> None: ...
light = _light()

# Submodule: light_matrix
class _light_matrix:
    # A minimal (but real) subset of images; the API exposes many more (1..67)
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

    def clear(self) -> None: ...
    def get_orientation(self) -> int: ...
    def set_orientation(self, top: int) -> int: ...
    def get_pixel(self, x: int, y: int) -> int: ...
    def set_pixel(self, x: int, y: int, intensity: int) -> None: ...
    def show(self, pixels: list[int]) -> None: ...
    def show_image(self, image: int) -> None: ...
    def write(self, text: str, intensity: int = 100, time_per_character: int = 500) -> Awaitable[None]: ...
light_matrix = _light_matrix()

# Submodule: motion_sensor
class _motion_sensor:
    TOP: int
    LEFT: int
    RIGHT: int
    BOTTOM: int

    def acceleration(self) -> Tuple[int, int, int]: ...
    def angular_velocity(self) -> Tuple[int, int, int]: ...
    def gesture(self) -> int: ...
    def stable(self) -> bool: ...
    def tap_count(self) -> int: ...
    def tilt_angles(self) -> Tuple[int, int, int]: ...
    def up_face(self) -> int: ...
    def reset_yaw(self, angle: int) -> None: ...
    def get_yaw(self) -> int: ...
    def set_yaw(self, yaw: int) -> None: ...
motion_sensor = _motion_sensor()

# Submodule: port
class _port:
    A: int
    B: int
    C: int
    D: int
    E: int
    F: int
port = _port()

# Submodule: sound (Hub-local beeps; distinct from app.sound)
class _sound:
    def beep(self, frequency: int = 440, ms: int = 200) -> Awaitable[None]: ...
    def stop(self) -> None: ...
sound = _sound()
