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
    """Reflected light 0..100% from Color Sensor."""
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

        if condition is not None and condition():
            done = True

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
                if motor.relative_position(RIGHT) <= float(distance):
                    done = True

        if condition is not None and condition():
            done = True

        if done:
            break

        utime.sleep_ms(10)

    motor_pair.stop(PAIR_ID)


# ---------------- main ----------------


def Tara_main():
    GAIN = 1.3
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(500)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=600,
        distance=1525,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=-GAIN,
        speed=-475,
        distance=-40,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=-75,
        speed=200,
    )

    utime.sleep_ms(100)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=-80,
        gain=GAIN,
        speed=400,
        distance=450,
    )

    utime.sleep_ms(100)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=-110,
        gain=-GAIN,
        speed=-300,
        distance=-25,
    )

    motor.reset_relative_position(port.D, 0)
    motor.run_to_relative_position(port.D, -160, 150)
    utime.sleep_ms(1000)
    motor.run_to_relative_position(port.D, 0, -300)
    utime.sleep_ms(500)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=-80,
        gain=-GAIN,
        speed=-300,
        distance=-400,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=-45,
        speed=300,
    )

    utime.sleep_ms(100)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=45,
        gain=GAIN,
        speed=300,
        distance=100,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=90,
        speed=300,
    )

    utime.sleep_ms(100)

    # gyro_follow_heading_gain_speed_distance_condition(
    #     heading=90,
    #     gain=GAIN,
    #     speed=300,
    #     distance=100,
    # )

    # gyro_follow_heading_gain_speed_distance_condition(
    #     heading=80,
    #     gain=-GAIN,
    #     speed=-300,
    #     distance=-100,
    # )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=90,
        gain=GAIN,
        speed=500,
        distance=800,
    )

    motor.reset_relative_position(port.C, 0)
    motor.run_to_relative_position(port.C, 160, 200)
    utime.sleep_ms(1000)
    motor.run_to_relative_position(port.C, 0, -300)
    utime.sleep_ms(500)

    print("done")


def Zaza_main():
    GAIN = 2
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(500)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=600,
        distance=1525,
        condition=lambda: color_sensor.color(port.E) == color.RED,
    )


def Anneuryysm_main():
    GAIN = 1.5
    motor.reset_relative_position(port.D, 0)
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(100)
    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=600,
        distance=1000,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=120,
        speed=200,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=120,
        gain=GAIN,
        speed=600,
        distance=400,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=120,
        gain=-GAIN,
        speed=-600,
        distance=-200,
    )

    gyro_turn_steering_heading_speed(
        steering=100,
        heading=180,
        speed=200,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=180,
        gain=GAIN,
        speed=600,
        distance=400,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=90,
        speed=200,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=90,
        gain=GAIN,
        speed=600,
        distance=550,
    )

    gyro_turn_steering_heading_speed(
        steering=-100,
        heading=0,
        speed=200,
    )

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=GAIN,
        speed=600,
        distance=50,
    )

    utime.sleep_ms(100)
    motor.run_to_relative_position(port.D, -45, 300)
    utime.sleep_ms(100)

    gyro_follow_heading_gain_speed_distance_condition(
        heading=0,
        gain=-GAIN,
        speed=-600,
        distance=-75,
    )

    motor.run_to_relative_position(port.D, -90, 300)
    utime.sleep_ms(100)


def Stonks_main():
    motor.reset_relative_position(port.C, 0)
    motor.reset_relative_position(port.D, 0)
    motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, 833)

    for i in range(6):
        motor.run_for_degrees(port.C, 190, 600)
        motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, -166)
        motor.run_for_degrees(port.C, -190, -600)
        motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, 166)

    motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, -833)


def WillemDafoe_main():
    pass


def Feetpics_main():
    pass


if __name__ == "__main__":
    Stonks_main()
