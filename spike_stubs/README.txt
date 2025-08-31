SPIKE Prime (SPIKE 3) MicroPython Type Stubs (v6)
-------------------------------------------------

Place this 'spike_stubs' folder in your workspace and add it to
'python.analysis.extraPaths' in VS Code to silence import warnings
for SPIKE modules (motor, motor_pair, color_sensor, etc.).

These stubs follow the SPIKE 3 docs (early 2024) and include:
- Modules: app (sound/music), color, color_matrix, color_sensor, device,
           distance_sensor, force_sensor, hub (button/light/light_matrix/
           motion_sensor/port/sound), motor, motor_pair, orientation, runloop
- MicroPython shims: time/utime, ujson, uos, urandom, ustruct, usbinascii
- Convenience: status_light, light, wait

Note: Awaitable functions (e.g., motor.run_for_time, motor_pair.move_for_degrees)
are typed as Awaitable to match 'await ...' usage under runloop.
