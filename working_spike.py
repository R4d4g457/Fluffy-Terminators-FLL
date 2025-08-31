# LEGO slot:1 autostart

import color
import color_sensor
import force_sensor
import motor
import motor_pair
import utime
from hub import port, motion_sensor


def wait_until(pred, timeout=None, poll_ms=10):
    """Poll until pred() is True. Optional timeout (sec)."""
    start_ms = utime.ticks_ms()
    while True:
        try:
            if pred():
                return True
        except Exception:
            pass
        if timeout is not None:
            if utime.ticks_diff(utime.ticks_ms(), start_ms) >= int(
                float(timeout) * 1000.0
            ):
                return False
        utime.sleep_ms(int(poll_ms))


# ---------------- helpers ----------------


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _to_float(x):
    if x is None:
        return 0.0
    try:
        return float(x)
    except Exception:
        return 0.0


def normalize_angle(a):
    """Normalize to (-180, 180]."""
    a = float(a)
    while a <= -180.0:
        a += 360.0
    while a > 180.0:
        a -= 360.0
    return a


def yaw_deg():
    """
    SPIKE lessons API: use motion_sensor.tilt_angles()
    The first value of the tuple is yaw in 0.1° (decidegrees) and
    sign-inverted vs app.
    Multiply by -0.1 to match the app/blocks convention.
    """
    try:
        # tuple = (yaw, pitch, roll) in 0.1°
        dd_yaw = motion_sensor.tilt_angles()[0]  # decidegrees
        return normalize_angle(float(dd_yaw) * -0.1)
    except Exception:
        return 0.0


def shortest_error(target, current):
    """Signed shortest angular error (target - current), in [-180, 180]."""
    return normalize_angle(float(target) - float(current))


# ---------------- motor/encoder wrappers ----------------

LEFT = port.A
RIGHT = port.B

DEFAULT_SPEED_PCT = 50  # your "percent" notion
MAX_DPS = 1000  # map %-speed to deg/sec for motor.run / motor_pair.move


def pct_to_dps(pct):
    pct_i = clamp(_to_float(pct), -100, 100)
    return int(pct_i * MAX_DPS / 100.0)


def run_motor_pct(p, pct):
    """Drive motor at approx 'pct' [-100..100] by mapping to deg/sec."""
    motor.run(p, pct_to_dps(pct))


def degrees_counted_safe(p):
    """Use relative_position as 'degrees counted'."""
    try:
        return float(motor.relative_position(p) or 0.0)
    except Exception:
        return 0.0


def reset_degrees(p):
    """This API requires (port, position)."""
    try:
        motor.reset_relative_position(p, 0)
    except Exception:
        pass


# Motor-pair setup (matches lessons API)
PAIR_ID = motor_pair.PAIR_1


def pair_setup():
    # pair A+B as the driving base
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)


def pair_move_steering(steering, speed_pct):
    """
    steering: -100..100 (positive => turn right)
    speed_pct: -100..100 mapped to velocity (deg/sec)
    """
    st = int(clamp(_to_float(steering), -100, 100))
    vel = pct_to_dps(speed_pct)
    # lessons API: motor_pair.move(pair_id, steering, velocity=...)
    motor_pair.move(PAIR_ID, st, velocity=vel)


def pair_stop():
    motor_pair.stop(PAIR_ID)


# ---------------- sensor helpers ----------------


def get_reflected_light(p, default=50):
    """Reflected light 0..100% from Color Sensor (lessons API)."""
    try:
        val = color_sensor.reflection(p)
        return float(val if val is not None else default)
    except Exception:
        return float(default)


# ---------------- variables used in blocks ----------------

n_Error = 0.0
n_TargetHeading = 0.0
n_CurrentHeading = 0.0

# ---------------- My Blocks (custom procedures) ----------------


def line_follow_speed_gain_target_lineside_port(
    speed, gain, target, lineside, color_port
):
    """
    Line Follow - Speed, Gain, Target, LineSide (1 = light on right),
    Port for color sensor.
    Uses individual motor.run(...) (deg/sec) to drive.
    """
    global n_Error
    speed_v = _to_float(speed) if speed not in (None, "") else 50.0
    gain_v = _to_float(gain) if gain not in (None, "") else 1.0
    target_v = _to_float(target) if target not in (None, "") else 50.0
    lineside_v = int(_to_float(lineside)) if lineside not in (None, "") else 1
    cs_port = color_port if color_port not in (None, "") else port.C

    reflect_v = get_reflected_light(cs_port, default=50)

    # Compute error depending on side of the line
    if lineside_v == 1:
        n_Error = float(target_v - reflect_v) * gain_v
    else:
        n_Error = float(reflect_v - target_v) * gain_v

    # Left power= -1 * (Speed + n_Error)
    # Right power =    (Speed - n_Error)
    left_pct = int(clamp(-(speed_v + n_Error), -100, 100))
    right_pct = int(clamp((speed_v - n_Error), -100, 100))

    motor.run(LEFT, pct_to_dps(left_pct))
    motor.run(RIGHT, pct_to_dps(right_pct))


def gyro_turn_steering_heading_speed(steering, heading, speed):
    """
    Gyro Turn - run with steering until yaw reaches heading (wrap-aware),
    using motor_pair.move(...) API from the lessons.
    """
    steering_v = int(_to_float(steering)) if steering not in (None, "") else 0
    target_v = normalize_angle(_to_float(heading) if heading not in (None, "") else 0.0)
    speed_v = int(_to_float(speed)) if speed not in (None, "") else DEFAULT_SPEED_PCT

    pair_setup()
    # Reset yaw baseline per lessons guidance
    motion_sensor.reset_yaw(0)

    # Start moving with steering
    pair_move_steering(steering_v, speed_v)

    # TOL of 2 degrees
    TOL = 2.0
    wait_until(lambda: abs(shortest_error(target_v, yaw_deg())) <= TOL)

    pair_stop()


def gyro_follow_heading_gain_speed_distance_condition(
    heading, gain, speed, distance, condition
):
    """
    Gyro Follow - keep heading using proportional steering until distance
    reached or condition True.
    Uses motor_pair.move(...) with proportional steering; distance checked
    on RIGHT motor degrees.
    """
    global n_TargetHeading, n_CurrentHeading, n_Error

    target_v = normalize_angle(_to_float(heading) if heading not in (None, "") else 0.0)
    kP = _to_float(gain) if gain not in (None, "") else 1.0
    speed_v = int(_to_float(speed)) if speed not in (None, "") else DEFAULT_SPEED_PCT

    n_TargetHeading = target_v

    pair_setup()
    # Reset yaw and encoder used for distance (RIGHT)
    motion_sensor.reset_yaw(0)
    reset_degrees(RIGHT)

    cond_fn = condition if callable(condition) else (lambda: False)

    dist_degs = None
    if distance not in (None, ""):
        dist_degs = _to_float(distance)

    # Follow loop
    while True:
        n_CurrentHeading = yaw_deg()
        err = shortest_error(n_TargetHeading, n_CurrentHeading)
        # (in [-180, 180])
        n_Error = err * kP

        steering_cmd = int(clamp(n_Error, -100, 100))
        pair_move_steering(steering_cmd, speed_v)

        # Exit conditions
        done = False
        if dist_degs is not None:
            if abs(degrees_counted_safe(RIGHT)) >= float(dist_degs):
                done = True

        try:
            if cond_fn():
                done = True
        except Exception:
            pass

        if done:
            break

        utime.sleep_ms(10)

    pair_stop()


# ---------------- main ----------------


def main():
    print("yo yo")

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=0.75,
        speed=75,
        distance=13000,
        condition=lambda: color_sensor.color(port.F) == color.GREEN,
    )

    print("done")


if __name__ == "__main__":
    main()
