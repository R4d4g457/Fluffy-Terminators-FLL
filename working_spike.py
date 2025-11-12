# LEGO slot:8 autostart
import color
import color_sensor
import motor
import motor_pair
import utime
from hub import port, motion_sensor, button
import math.copysign


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
    """Read yaw from gyro and convert from decidegrees to degrees."""
    try:
        dd_yaw = motion_sensor.tilt_angles()[0]  # decidegrees
        return normalize_angle(float(dd_yaw) / 10.0)
    except Exception:
        return 0.0


def shortest_error(target, current):
    """Signed shortest angular error (target - current), in [-180, 180]."""
    return normalize_angle(float(target) - float(current))


# ---------------- motor/encoder wrappers ----------------

COLLISION_SENSOR = port.F
COLOUR_SENSOR = port.E
LEFT_ACTUATOR = port.C
RIGHT_ACTUATOR = port.D
LEFT = port.A
RIGHT = port.B
PAIR_ID = motor_pair.PAIR_1

MAX_DPS = 1100  # map %-speed to deg/sec for motor.run / motor_pair.move

DEBUG = False


def init():
    motor_pair.pair(PAIR_ID, LEFT, RIGHT)
    motor.reset_relative_position(RIGHT, 0)
    motor.reset_relative_position(LEFT, 0)
    motor.reset_relative_position(RIGHT_ACTUATOR, 0)
    motor.reset_relative_position(LEFT_ACTUATOR, 0)
    utime.sleep_ms(500)
    motion_sensor.reset_yaw(0)
    utime.sleep_ms(500)


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


# ---------------- motion functions ----------------


def line_follow(speed, gain, target=50, lineside=1, distance=None, condition=None):
    """
    Line Follow - Speed, Gain, Target, LineSide (1 = light on right),
    Port for color sensor.
    Uses individual motor.run(...) (deg/sec) to drive.
    """
    n_Error = 0.0

    while True:
        reflect_v = get_reflected_light(COLOUR_SENSOR, default=50)

        if lineside == 1:
            n_Error = float(target - reflect_v) * gain
        else:
            n_Error = float(reflect_v - target) * gain

        left_pct = clamp(-(speed + n_Error), -100, 100)
        right_pct = clamp((speed - n_Error), -100, 100)

        motor.run(LEFT, pct_to_dps(left_pct))
        motor.run(RIGHT, pct_to_dps(right_pct))

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

    motor_pair.stop(PAIR_ID)


def gyro_turn(heading, speed=20):
    """
    Turn to an absolute heading using shortest path.
    Positive = clockwise, Negative = anticlockwise.
    Includes smooth ramp-down curve for precision stopping.
    """
    target = normalize_angle(heading)
    Kp = 2.2
    MIN_SPD = 10
    MAX_SPD = abs(speed)
    DECAY = 35  # Higher = slower drop in speed (tune between 25–45)
    TOL = 1.0
    global DEBUG

    while True:
        current = yaw_deg()
        error = shortest_error(target, current)

        if abs(error) <= TOL:
            break

        # Inverted direction fix — corrects spin direction
        turn_dir = -copysign(1, error)

        # Non-linear ramp for smooth deceleration
        base_speed = MIN_SPD + (MAX_SPD - MIN_SPD) * (1 - exp(-abs(error) / DECAY))
        turn_speed = clamp(base_speed, MIN_SPD, MAX_SPD)

        steering = int(turn_dir * 100)

        if DEBUG:
            print(
                f"[TURN] yaw={current:.1f}, target={target:.1f}, err={error:.1f}, spd={turn_speed:.1f}"
            )

        motor_pair.move(PAIR_ID, steering, velocity=pct_to_dps(turn_speed))
        utime.sleep_ms(20)

    motor_pair.stop(PAIR_ID)
    utime.sleep_ms(100)


def gyro_follow(heading, gain=0.2, speed=30, distance=None, condition=None):
    """
    Gyro Follow — corrected to match new turn direction.
    heading: target heading
    gain: proportional gain
    speed: forward % speed
    distance: wheel degrees
    condition: optional function to break early
    """
    n_TargetHeading = normalize_angle(heading)

    motor.reset_relative_position(RIGHT, 0)
    motor.reset_relative_position(LEFT, 0)

    while True:
        n_CurrentHeading = yaw_deg()
        n_Error = shortest_error(n_TargetHeading, n_CurrentHeading)

        steering_cmd = int(clamp(-n_Error * gain, -100, 100))
        motor_pair.move(PAIR_ID, steering_cmd, velocity=pct_to_dps(speed))

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
    utime.sleep_ms(100)


# ---------------- missions ----------------


def Taretare_Sauce_1_main():
    GAIN = 0.19

    # Travel to & Turn parallel with Forge
    gyro_follow(heading=0, gain=GAIN, speed=45, distance=1450)
    gyro_turn(heading=41, speed=15)
    gyro_follow(heading=41, gain=-GAIN, speed=-30, distance=-75)

    # Pick up Millstone
    utime.sleep_ms(100)
    motor.run_for_degrees(RIGHT_ACTUATOR, 1800, 1100)
    utime.sleep_ms(1250)
    motor.run_for_degrees(RIGHT_ACTUATOR, -1000, 1100)
    utime.sleep_ms(1100)

    utime.sleep_ms(100)
    gyro_turn(heading=30, speed=-10)
    gyro_follow(heading=30, gain=GAIN, speed=30, distance=120)

    # Loose Forge
    gyro_turn(heading=-15, speed=15)
    gyro_follow(heading=-15, gain=-GAIN, speed=-27, distance=-75)
    gyro_turn(heading=0, speed=15)
    gyro_follow(heading=0, gain=-GAIN, speed=-30, distance=-65)

    # Push Rocks
    gyro_turn(heading=-86, speed=15)
    gyro_follow(heading=-86, gain=GAIN, speed=30, distance=600)
    gyro_follow(heading=-90, gain=-GAIN, speed=-30, distance=-500)

    # Scoring Scale
    gyro_turn(heading=-135, speed=15)
    gyro_follow(heading=-135, gain=-GAIN, speed=-30, distance=-190)
    gyro_turn(heading=-90, speed=15)

    # Travel
    gyro_follow(heading=-90, gain=-GAIN, speed=-30, distance=-225)
    gyro_turn(heading=-90, speed=15)
    gyro_follow(heading=-90, gain=-GAIN, speed=-40, distance=-500)

    # Score Flag
    motor.reset_relative_position(LEFT_ACTUATOR, 0)
    motor.run_for_degrees(LEFT_ACTUATOR, 170, 120)
    utime.sleep_ms(1500)
    motor.run_for_degrees(LEFT_ACTUATOR, -150, 150)
    utime.sleep_ms(750)

    gyro_follow(heading=-90, gain=-GAIN, speed=-30, distance=-135)
    gyro_turn(heading=88, speed=15)

    # Score Basket
    motor.reset_relative_position(LEFT_ACTUATOR, 0)
    motor.run_for_degrees(LEFT_ACTUATOR, 190, 150)
    utime.sleep_ms(750)
    motor.run_for_degrees(LEFT_ACTUATOR, -140, 150)
    utime.sleep_ms(750)

    # Return to Blue Home
    gyro_turn(heading=87, speed=25)
    gyro_follow(heading=87, gain=-GAIN, speed=-30, distance=-900)
    gyro_turn(heading=25, speed=20)
    gyro_follow(heading=25, gain=-GAIN, speed=-100, distance=-1450)


def Stonks_2_main():

    # Travel
    gyro_follow(heading=0, gain=0.2, speed=35, distance=815)

    # Turn to align with silo
    gyro_turn(heading=-12, speed=15)

    # Push Silo lever 4 times
    for i in range(4):
        motor.run_for_degrees(RIGHT_ACTUATOR, 560, 350)
        utime.sleep_ms(750)
        motor.run_for_degrees(RIGHT_ACTUATOR, -560, 350)
        utime.sleep_ms(750)

    # Return to Blue Home
    gyro_follow(heading=15, gain=-0.2, speed=-60, distance=-850)


def Anneuryysm_3_main():
    GAIN = 0.2
    # Travel
    gyro_follow(heading=0, gain=GAIN, speed=40, distance=620)
    gyro_turn(heading=33, speed=12)
    gyro_follow(heading=33, gain=GAIN, speed=40, distance=280)

    # Score Market
    gyro_turn(heading=120, speed=12)
    gyro_follow(heading=120, gain=GAIN, speed=40, distance=375)
    gyro_turn(heading=125, speed=12)

    # Travel
    gyro_follow(heading=125, gain=-GAIN, speed=-55, distance=-100)
    gyro_turn(heading=150, speed=20)
    gyro_follow(heading=150, gain=GAIN, speed=55, distance=100)
    gyro_turn(heading=45, speed=20)

    # Score Roof
    gyro_follow(heading=45, gain=GAIN, speed=55, distance=75)
    motor.run_for_degrees(RIGHT_ACTUATOR, 400, 360)
    utime.sleep_ms(1500)
    gyro_follow(heading=45, gain=-GAIN, speed=-50, distance=-350)
    gyro_follow(heading=45, gain=GAIN, speed=50, distance=200)
    motor.run_for_degrees(RIGHT_ACTUATOR, -400, 360)
    utime.sleep_ms(500)
    gyro_follow(heading=45, gain=-GAIN, speed=-50, distance=-200)

    # Travel
    gyro_turn(heading=90, speed=20)
    motor.run_for_degrees(LEFT_ACTUATOR, -540, 360)
    utime.sleep_ms(200)
    gyro_follow(heading=90, gain=GAIN, speed=50, distance=580)

    # Collect sample
    gyro_turn(heading=0, speed=20)
    gyro_follow(heading=0, gain=GAIN, speed=50, distance=200)
    motor.run_for_degrees(LEFT_ACTUATOR, 180, 360)
    gyro_follow(heading=0, gain=-GAIN, speed=-50, distance=-400)
    motor.run_for_degrees(LEFT_ACTUATOR, 360, 360)

    # Travel
    gyro_turn(heading=90, speed=20)
    gyro_follow(heading=90, gain=GAIN, speed=50, distance=600)
    gyro_turn(heading=45, speed=20)
    gyro_follow(heading=45, gain=GAIN, speed=50, distance=275)
    gyro_turn(heading=90, speed=20)
    gyro_follow(heading=90, gain=GAIN, speed=50, distance=400)
    gyro_turn(heading=-40, speed=20)

    # Statue
    motor.run_for_degrees(RIGHT_ACTUATOR, 400, 360)
    utime.sleep_ms(1000)
    gyro_turn(heading=0, speed=20)
    motor.run_for_degrees(RIGHT_ACTUATOR, -400, 360)
    utime.sleep_ms(2000)
    gyro_follow(heading=0, gain=-GAIN, speed=-50, distance=-150)

    # Travel
    gyro_turn(heading=45, speed=20)
    gyro_follow(heading=45, gain=GAIN, speed=50, distance=1100)
    gyro_turn(heading=-50, speed=20)

    # Lift Minecart
    motor.run_for_degrees(RIGHT_ACTUATOR, 400, 360)
    utime.sleep_ms(200)
    gyro_follow(heading=-50, gain=GAIN, speed=50, distance=500)
    motor.run_for_degrees(RIGHT_ACTUATOR, -400, 360)
    utime.sleep_ms(2000)

    # Return to Red Home
    gyro_follow(heading=-50, gain=-GAIN, speed=-50, distance=-800)
    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-75,
        distance=None,
        condition=lambda: color_sensor.color(COLOUR_SENSOR) == color.GREEN,
    )


def WillemDafoe_4_main():
    GAIN = 2
    print("willy")

    gyro_follow(heading=0, gain=GAIN, speed=10, distance=100) #slow start
    gyro_follow(heading=0, gain=GAIN, speed=35, distance=978) #continue
    gyro_turn(heading=9, speed=18) #turn 
    gyro_follow(heading=8, gain=GAIN, speed=27, distance=430) #forward to do all the stuff
    gyro_follow(heading=4, gain=-GAIN, speed=-18, distance=-300) #back maybe
    gyro_turn(heading=0, speed=8) #recenter
    gyro_follow(heading=0, gain=-GAIN, speed=-18, distance=-350) #back more i think
    gyro_turn(heading=8, speed=12) #turn to brush
    gyro_follow(heading=8, gain=GAIN, speed=18, distance=80) #forard for brush
    gyro_turn(heading=-10, speed=4) #hook brush turn

    motor.run_for_degrees(LEFT_ACTUATOR, -250, 200)
    utime.sleep_ms(500)

    gyro_follow(
        heading=0,
        gain=-GAIN,
        speed=-27,
        distance=0,
        condition=lambda: (color_sensor.color(COLOUR_SENSOR)) == color.GREEN,
    )

    motor.run_for_degrees(RIGHT_ACTUATOR, 300, 200)
    utime.sleep_ms(1000)


def Feetpics_5_main():
    gain = 0.2
    gyro_follow(heading=0, gain=gain, speed=75, distance=1100)
    gyro_follow(heading=0, gain=-gain, speed=-75, distance=-1050)


def Zaza_6_main():
    GAIN = 0.2

    # Uncover Boat
    gyro_follow(heading=0, gain=GAIN, speed=40, distance=810)
    gyro_follow(heading=0, gain=-GAIN, speed=-25, distance=-100)

    # Travel
    gyro_turn(heading=75, speed=15)
    utime.sleep_ms(100)
    gyro_follow(heading=75, gain=GAIN, speed=30, distance=400)
    utime.sleep_ms(100)
    gyro_turn(heading=0, speed=-15)
    gyro_follow(
        heading=0,
        gain=GAIN,
        speed=27,
        distance=625,
    )

    # Raise Crane
    gyro_turn(heading=-85, speed=10)
    utime.sleep_ms(100)
    gyro_follow(heading=-85, gain=GAIN, speed=27, distance=253)
    gyro_turn(heading=-85, speed=10)
    motor.run_for_degrees(LEFT_ACTUATOR, -800, -200)
    utime.sleep_ms(2500)

    gyro_follow(heading=-90, gain=-GAIN, speed=-27, distance=-170)
    gyro_turn(heading=180, speed=15)
    gyro_follow(heading=180, gain=GAIN, speed=40, distance=475)
    gyro_turn(heading=-90, speed=15)
    gyro_follow(heading=-90, gain=GAIN, speed=27, distance=100)
    gyro_turn(heading=0, speed=15)
    gyro_follow(heading=0, gain=GAIN, speed=40, distance=250)
    gyro_follow(heading=0, gain=-GAIN, speed=-27, distance=-25)
    motor.run_for_degrees(RIGHT_ACTUATOR, 90, 120)
    gyro_follow(heading=-10, gain=-GAIN, speed=-27, distance=-400)
    print("done")


def Mercy_Dash():
    gyro_follow(heading=0, gain=0.2, speed=75, distance=3700)


if __name__ == "__main__":
    init()
    Mercy_Dash()
