import motor 
import motor_pair
import color_sensor as CS
import force_sensor as FS
from App import display
from hub import motion_sensor as gyro
from hub import port
import runloop.until as Wait_Until
import runloop.sleep_ms as Wait

motor_pair = motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)

# --- helpers ---

def clamp(v, lo, hi):
    if v < lo: return lo
    if v > hi: return hi
    return v

def _to_float(x):
    if x is None: return 0.0
    try:
        return float(x)# handles str/int/float
    except Exception:
        return 0.0

def normalize_angle(a):
    """Normalize to (-180, 180]."""
    a = float(a)
    while a <= -180.0: a += 360.0
    while a >180.0: a -= 360.0
    return a

def yaw():
    # SPIKE PrimeHub yaw angle
    try:
        val = gyro.get_yaw_face()
        if val is None:# defensive
            return 0.0
        return normalize_angle(float(val))
    except Exception:
        # Fallback if running off-device
        return 0.0

def shortest_error(target, current):
    """Signed shortest angular error (target - current), in [-180, 180]."""
    return normalize_angle(float(target) - float(current))

# --- Variables used in blocks --- (annotated to satisfy type checkers)
n_Error = 0.0
n_TargetHeading = 0.0
n_CurrentHeading = 0.0

# --- My Blocks (custom procedures) ---

def line_follow_speed_gain_target_lineside_port(speed, gain, target, lineside, port):
    """Line Follow - Speed, Gain, Target, LineSide (1 = light on right of line, else opposite), Port (color sensor)."""
    global n_Error
    # Coerce inputs to safe numeric values
    speed_v = _to_float(speed) if speed not in (None, "") else 50.0
    gain_v = _to_float(gain) if gain not in (None, "") else 1.0
    target_v = _to_float(target) if target not in (None, "") else 50.0
    lineside_v = int(_to_float(lineside)) if lineside not in (None, "") else 1

    cs = CS.reflection(port.A)

    # get_reflected_light() should return a number; coerce defensively
    try:
        reflect_raw = cs
    except Exception:
        reflect_raw = 50# safe default if off-hub
    reflect_v = _to_float(reflect_raw)

    # Compute error depending on which side of the line we're following
    if lineside_v == 1:
        # error = (Target - reflect) * Gain
        n_Error = float(target_v - reflect_v) * gain_v
    else:
        # error = (reflect - Target) * Gain
        n_Error = float(reflect_v - target_v) * gain_v

    left_power= int(clamp(-(speed_v + n_Error), -100, 100))
    right_power = int(clamp( (speed_v - n_Error), -100, 100))

    motor.set_duty_cycle(port.A, left_power)
    motor.set_duty_cycle(port.B, right_power)

def gyro_turn_steering_heading_speed(steering, heading, speed):
    """Gyro Turn - start moving with steering until yaw reaches heading (wrap-aware)."""
    steering_v = int(_to_float(steering)) if steering not in (None, "") else 0
    target_v = normalize_angle(_to_float(heading) if heading not in (None, "") else 0.0)
    speed_v = int(_to_float(speed)) if speed not in (None, "") else 50

    motor_pair.move(PAIR_1, steering=steering_v, speed_v, 1000)

    # Drive until within a small tolerance of target heading, considering wrap.
    TOL = 2.0# degrees
    Wait_Until(lambda: abs(shortest_error(target_v, yaw())) <= TOL)

    motor_pair.stop(motor_pair.PAIR_1)

def gyro_follow_heading_gain_speed_distance_condition(heading, gain, speed, distance, condition):

    global n_TargetHeading, n_CurrentHeading, n_Error
    target_v = normalize_angle(_to_float(heading) if heading not in (None, "") else 0.0)
    kP = _to_float(gain) if gain not in (None, "") else 1.0
    speed_v = int(_to_float(speed)) if speed not in (None, "") else 50

    # Normalize/record target
    n_TargetHeading = target_v

    # Reset a wheel encoder used for distance, default to right (B), per project block
    try:
        motor.reset_relative_position(port.B, 0)
    except Exception:
        pass

    motor_pair.set_default_speed(speed_v)

    # Condition function
    cond_fn = (condition if callable(condition) else (lambda: False))

    # Optional distance (interpreted as motor degrees on port B in this translation)
    dist_degs = None
    if distance not in (None, ""):
        d = _to_float(distance)
        dist_degs = d

    # Follow loop
    while True:
        n_CurrentHeading = yaw()
        # Basic wrap handling
        err = shortest_error(n_TargetHeading, n_CurrentHeading)# in [-180,180]
        n_Error = err * kP

        steering_cmd = int(clamp(n_Error, -100, 100))
        motor_pair.start(steering=steering_cmd)

        # Exit conditions: optional distance reached OR external condition satisfied
        done = False
        if dist_degs is not None:
            if abs(motor.relative_position(port.B)) >= float(dist_degs):
                done = True

        try:
            if cond_fn():
                done = True
        except Exception:
            # If the condition crashes, ignore it rather than stopping the robot unexpectedly
            pass

        if done:
            break

    motor_pair.stop()

# --- Main program (when program starts) ---

def main():
    # Movement pair set to AB by default above

    # Call: Gyro Follow - Heading: 0, Gain: 2, Speed: 75, Distance: '', Condition: Force(C) released

    def cond():# 'released'
        try:
            return not bool(FS.pressed(port.C))
        except Exception:
            return False

    gyro_follow_heading_gain_speed_distance_condition(0, 2, 20, 200, cond)


if __name__ == '__main__':
    main()
