from math import sin, cos, tan, asin, acos, atan, degrees


def motor1Pos(arm1, arm2, x, y, θ2):
    θ1 = atan(y / x) - atan((arm2 * sin(θ2)) / (arm1 + arm2 * cos(θ2)))
    return degrees(θ1)


def motor2Pos(arm1, arm2, x, y):
    try:
        val = (x**2 + y**2 - arm1**2 - arm2**2) / (2 * arm1 * arm2)
        val = max(min(val, 1), -1)
        θ2 = acos(val)
        return degrees(θ2)
    except ValueError:
        return None


# ---------------- main ----------------


def main():
    arm1 = 120
    arm2 = 125
    x = int(input("X Coordinate:"))
    y = int(input("Y Coordinate:"))
    θ2 = motor2Pos(arm1, arm2, x, y)
    θ1 = motor1Pos(arm1, arm2, x, y, θ2)
    print("Motor 1 Position:", θ1, "\nMotor 2 Position:", θ2)
    print("Ending Coordinates - X:", x, "Y:", y)
    pass


if __name__ == "__main__":
    main()
