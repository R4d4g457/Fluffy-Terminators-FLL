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
    """Normalize to (-180, 180)."""
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

COLLISION_SENSOR = port.F
COLOUR_SENSOR = port.E
LEFT_ACTUATOR = port.D
RIGHT_ACTUATOR = port.C
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


def line_follow(
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


def gyro_turn(steering, heading, speed):
    """
    steering (Left -100 to Right 100),
    heading (Left 180 to Right -180),
    speed (deg/sec),
    \nGyro Turn - run with steering until yaw reaches heading (wrap-aware),
    using motor_pair.move
    """

    target_v = normalize_angle(heading)

    motor_pair.move(PAIR_ID, steering, velocity=pct_to_dps(speed))

    # TOL of 1 degree
    TOL = 1.0
    wait_until(lambda: abs(shortest_error(target_v, yaw_deg())) <= TOL)

    motor_pair.stop(PAIR_ID)


def gyro_follow(heading, gain, speed, distance, condition=None):
    """
    heading (Left 180 to Right -180),
    gain (Adjusted for each Robot),
    speed (deg/sec),
    distance (Wheel degrees),
    condition (End Condition)
    \nGyro Follow - keep heading using proportional steering until distance
    reached or condition True.
    Uses motor_pair.move(...) with proportional steering; distance checked
    on RIGHT motor degrees.
    """

    n_Error = 0.0

    n_TargetHeading = normalize_angle(heading)

    # Reset encoder used for distance
    motor.reset_relative_position(RIGHT, 0)
    motor.reset_relative_position(LEFT, 0)
    done = False

    while not done:
        n_CurrentHeading = yaw_deg()
        n_Error = shortest_error(n_TargetHeading, n_CurrentHeading) * gain

        steering_cmd = int(clamp(n_Error, -100, 100))
        motor_pair.move(PAIR_ID, steering_cmd, velocity=pct_to_dps(speed))

        # Exit conditions
        if distance is not None:
            if distance > 0:
                if abs(motor.relative_position(RIGHT)) >= float(distance):
                    done = True
            else:
                if motor.relative_position(RIGHT) <= float(distance):
                    done = True

        if condition is not None and condition():
            done = True

    motor_pair.stop(PAIR_ID)


# ---------------- main ----------------


def Taretare_Sauce_1_main():
    GAIN = 0.2
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(100)

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=42,
        distance=1440,
    )

    gyro_turn(
        steering=-100,
        heading=45,
        speed=15,
    )

    gyro_follow(
        heading=45,
        gain=-GAIN,
        speed=-30,
        distance=-50,
    )

    motor.reset_relative_position(port.D, 0)
    utime.sleep_ms(100)
    motor.run_for_degrees(port.D, 1500, 1100)
    utime.sleep_ms(1100)
    motor.run_for_degrees(port.D, -900, 1100)
    utime.sleep_ms(1100)

    utime.sleep_ms(100)

    gyro_turn(
        steering=-100,
        heading=25,
        speed=-10,
    )

    gyro_follow(
        heading=25,
        gain=GAIN,
        speed=30,
        distance=90,
    )

    gyro_turn(
        steering=100,
        heading=-10,
        speed=15,
    )

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-27,
        distance=-50,
    )

    gyro_turn(
        steering=-100,
        heading=0,
        speed=15,
    )

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-30,
        distance=-65,
    )

    gyro_turn(
        steering=100,
        heading=-90,
        speed=15,
    )

    gyro_follow(
        heading=-90,
        gain=GAIN,
        speed=30,
        distance=600,
    )

    gyro_follow(
        heading=-90,
        gain=-GAIN,
        speed=-30,
        distance=-500,
    )

    gyro_turn(
        steering=100,
        heading=-135,
        speed=15,
    )

    gyro_follow(
        heading=-135,
        gain=-GAIN,
        speed=-30,
        distance=-220,
    )

    gyro_turn(
        steering=-100,
        heading=-90,
        speed=15,
    )

    gyro_follow(
        heading=-90,
        gain=-GAIN,
        speed=-30,
        distance=-225,
    )

    gyro_turn(
        steering=100,
        heading=-90,
        speed=15,
    )

    gyro_follow(
        heading=-90,
        gain=-GAIN,
        speed=-30,
        distance=-500,
    )

    motor.reset_relative_position(port.C, 0)
    motor.run_for_degrees(port.C, 120, 80)
    utime.sleep_ms(1000)
    motor.run_for_degrees(port.C, -120, 80)
    utime.sleep_ms(1000)

    gyro_follow(
        heading=-90,
        gain=-GAIN,
        speed=-30,
        distance=-50,
    )

    gyro_turn(
        steering=-100,
        heading=90,
        speed=15,
    )

    motor.reset_relative_position(port.C, 0)
    motor.run_for_degrees(port.C, 120, 80)
    utime.sleep_ms(1000)
    motor.run_for_degrees(port.C, -120, 80)
    utime.sleep_ms(1000)

    gyro_follow(
        heading=90,
        gain=-GAIN,
        speed=-30,
        distance=-400,
    )

    gyro_follow(
        heading=60,
        gain=-GAIN,
        speed=-30,
        distance=-100,
    )

    gyro_turn(
        steering=100,
        heading=90,
        speed=25,
    )

    gyro_follow(
        heading=90,
        gain=GAIN,
        speed=30,
        distance=600,
    )

    gyro_turn(
        steering=-100,
        heading=180,
        speed=25,
    )

    gyro_follow(
        heading=180,
        gain=GAIN,
        speed=30,
        distance=1200,
    )

    # print("done")


def Zaza_6_main():
    GAIN = 0.2
    motor.reset_relative_position(port.D, 0)
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(500)

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=55,
        distance=800,
    )

    gyro_follow(heading=0, gain=GAIN, speed=-20, distance=150)

    gyro_turn(steering=-100, heading=45, speed=30)

    gyro_follow(heading=45, gain=GAIN, speed=40, distance=500)

    gyro_turn(steering=100, heading=10, speed=30)

    motor_pair.move(PAIR_ID, 0, velocity=pct_to_dps(40))
    wait_until(lambda: color_sensor.color(COLOUR_SENSOR) == color.WHITE)
    wait_until(lambda: color_sensor.color(COLOUR_SENSOR) == color.BLACK)
    motor_pair.stop(PAIR_ID)


def Anneuryysm_3_main():
    GAIN = 0.2
    motor.reset_relative_position(port.D, 0)
    print("yo yo yo")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(100)

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=55,
        distance=500,
    )

    gyro_turn(
        steering=-100,
        heading=15,
        speed=20,
    )
    print("yr")
    gyro_follow(
        heading=15,
        gain=GAIN,
        speed=55,
        distance=600,
    )

    gyro_follow(
        heading=120,
        gain=-GAIN,
        speed=-55,
        distance=-450,
    )

    gyro_follow(
        heading=180,
        gain=GAIN,
        speed=55,
        distance=400,
    )
    utime.sleep_ms(500)
    gyro_follow(
        heading=180,
        gain=-GAIN,
        speed=-55,
        distance=-600,
    )

    gyro_turn(
        steering=-100,
        heading=90,
        speed=20,
    )

    utime.sleep_ms(9999999)

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=54.5454545455,
        distance=80,
    )

    utime.sleep_ms(300)
    motor.run_for_degrees(port.D, -60, 300)
    utime.sleep_ms(100)

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-55,
        distance=-75,
    )

    motor.run_to_relative_position(port.D, -140, 300)
    utime.sleep_ms(100)


def Stonks_2_main():
    motor.reset_relative_position(port.C, 0)
    motor.reset_relative_position(port.D, 0)
    motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, 833)

    for i in range(6):
        motor.run_for_degrees(port.C, 190, 600)
        motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, -166)
        motor.run_for_degrees(port.C, -190, -600)
        motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, 166)

    motor_pair.move_for_degrees(motor_pair.PAIR_1, 0, -833)


def WillemDafoe_4_main():
    GAIN = 0.2
    print("willy")
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motion_sensor.reset_yaw(0)
    motor.run_to_absolute_position(LEFT_ACTUATOR, 0, 200)
    utime.sleep_ms(100)
    motor.reset_relative_position(LEFT_ACTUATOR, 0)
    utime.sleep_ms(100)

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=36,
        distance=1000,
    )

    gyro_turn(
        steering=-100,
        heading=9,
        speed=18,
    )

    gyro_follow(
        heading=9,
        gain=GAIN,
        speed=27,
        distance=400,
    )

    gyro_follow(
        heading=4,
        gain=-GAIN,
        speed=-18,
        distance=-100,
    )

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-18,
        distance=-200,
    )

    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=18,
        distance=115,
    )

    gyro_turn(
        steering=100,
        heading=-10,
        speed=9,
    )

    motor.run_for_degrees(LEFT_ACTUATOR, -250, 200)
    utime.sleep_ms(500)

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-27,
        distance=0,
        condition=lambda: (color_sensor.color(port.E)) == color.GREEN,
    )

    motor.run_for_degrees(port.D, 300, 200)
    utime.sleep_ms(1000)


def Feetpics_5_main():
    pass


if __name__ == "__main__":
    Zaza_6_main()
