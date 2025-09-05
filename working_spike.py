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


def normalize_angle(a):
    """Normalize to (-180, 180]."""
    a = float(a)
    while a <= -180.0:
        a += 360.0
    while a > 180.0:
        a -= 360.0
    return a


def yaw_deg():
    try:
        dd_yaw = motion_sensor.tilt_angles()[0]  # decidegrees
        return normalize_angle(float(dd_yaw) / 10.0)  # <-- divide by 10 for degrees
    except Exception:
        return 0.0


def shortest_error(target, current):
    """Signed shortest angular error (target - current), in [-180, 180]."""
    return normalize_angle(float(target) - float(current))


# ---------------- motor/encoder wrappers ----------------

LEFT = port.A
RIGHT = port.B
PAIR_ID = motor_pair.PAIR_1

MAX_DPS = 1000  # map %-speed to deg/sec for motor.run / motor_pair.move


def pct_to_dps(pct):
    pct_i = clamp(pct, -100, 100)
    return int(pct_i * MAX_DPS / 100.0)


# ---------------- sensor helpers ----------------


def get_reflected_light(p, default=50):
    """Reflected light 0..100% from Color Sensor (lessons API)."""
    try:
        val = color_sensor.reflection(p)
        return float(val if val is not None else default)
    except Exception:
        return float(default)


# ---------------- My Blocks (custom procedures) ----------------


def line_follow_speed_gain_target_lineside_port(
    speed, gain, target=50, lineside=1, color_port=port.C, distance=None, condition=None
):
    """
    Line Follow - Speed, Gain, Target, LineSide (1 = light on right),
    Port for color sensor.
    Uses individual motor.run(...) (deg/sec) to drive.
    """
    n_Error = 0.0
    cs_port = color_port if color_port not in (None, "") else port.C

    while True:
        reflect_v = get_reflected_light(cs_port, default=50)

        # Compute error depending on side of the line
        if lineside == 1:
            n_Error = float(target - reflect_v) * gain
        else:
            n_Error = float(reflect_v - target) * gain

        # Left power= -1 * (Speed + n_Error)
        # Right power =    (Speed - n_Error)
        left_pct = clamp(-(speed + n_Error), -100, 100)
        right_pct = clamp((speed - n_Error), -100, 100)

        motor.run(LEFT, pct_to_dps(left_pct))
        motor.run(RIGHT, pct_to_dps(right_pct))

        # Exit conditions
        done = False
        if distance is not None:
            if distance > 0:
                if abs(motor.relative_position(RIGHT)) >= float(distance):
                    done = True
            else:
                if motor.relative_position(LEFT) <= float(distance):
                    done = True

        try:
            if condition is not None and condition():
                done = True
        except Exception:
            pass

        if done:
            break

        utime.sleep_ms(10)


def gyro_turn_steering_heading_speed(steering, heading, speed):
    """
    Gyro Turn - run with steering until yaw reaches heading (wrap-aware),
    using motor_pair.move(...) API from the lessons.
    """

    target_v = normalize_angle(heading)

    motor_pair.move(PAIR_ID, steering, velocity=speed)

    # TOL of 1 degree
    TOL = 1.0
    wait_until(lambda: abs(shortest_error(target_v, yaw_deg())) <= TOL)

    motor_pair.stop(PAIR_ID)


def gyro_follow_heading_gain_speed_distance_condition(
    heading, gain, speed, distance, condition=None
):
    """
    Gyro Follow - keep heading using proportional steering until distance
    reached or condition True.
    Uses motor_pair.move(...) with proportional steering; distance checked
    on RIGHT motor degrees.
    """

    n_Error = 0.0

    n_TargetHeading = normalize_angle(heading)

    # Reset encoder used for distance
    motor.reset_relative_position(RIGHT, 0)
    motor.reset_relative_position(LEFT, 0)

    # Follow loop
    while True:
        n_CurrentHeading = yaw_deg()
        n_Error = shortest_error(n_TargetHeading, n_CurrentHeading) * gain

        steering_cmd = int(clamp(n_Error, -100, 100))
        motor_pair.move(PAIR_ID, steering_cmd, velocity=speed)

        # Exit conditions
        done = False
        if distance is not None:
            if distance > 0:
                if abs(motor.relative_position(RIGHT)) >= float(distance):
                    done = True
            else:
                if motor.relative_position(LEFT) <= float(distance):
                    done = True

        try:
            if condition is not None and condition():
                done = True
        except Exception:
            pass

        if done:
            break

        utime.sleep_ms(10)

    motor_pair.stop(PAIR_ID)


# ---------------- main ----------------


def William_main():
    GAIN = 2
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, RIGHT, LEFT)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=700,
        distance=1150,
        # condition=lambda: color_sensor.color(port.E) == color.BLACK,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=45,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=45,
        gain=GAIN,
        speed=700,
        distance=300,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=90,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=90,
        gain=GAIN,
        speed=700,
        distance=750,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=0,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=650,
        distance=None,
        condition=lambda: color_sensor.color(port.F) == color.YELLOW,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=-GAIN,
        speed=-700,
        distance=-250,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=-15,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=-15,
        gain=-GAIN,
        speed=-700,
        distance=-1000,
    )

    print("done")


def Tara_main():
    GAIN = 0.2
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, RIGHT, LEFT)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=700,
        distance=1200,
        # condition=lambda: color_sensor.color(port.E) == color.BLACK,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=45,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=45,
        gain=GAIN,
        speed=700,
        distance=300,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=80,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=80,
        gain=GAIN,
        speed=700,
        distance=750,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=0,
        speed=300,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=1100,
        distance=None,
        condition=lambda: force_sensor.force(port.C) == 0,
    )

    motor_pair.move_for_time(PAIR_ID, 0, 200)
    utime.sleep_ms(20)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(20)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=-GAIN,
        speed=-700,
        distance=-1150,
    )

    print("done")


if __name__ == "__main__":
    Tara_main()
