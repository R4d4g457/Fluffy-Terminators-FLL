import pygame
import sys
from math import cos, sin, acos, atan2, degrees, radians

# Arm parameters (now variables)
ARM1 = 120
ARM2 = 125

ORIGIN = (300, 300)


def inverse_kinematics(x, y, arm1, arm2):
    dx = x - ORIGIN[0]
    dy = y - ORIGIN[1]
    r2 = dx**2 + dy**2
    # Law of cosines for θ2
    cos_theta2 = (r2 - arm1**2 - arm2**2) / (2 * arm1 * arm2)
    if abs(cos_theta2) > 1:
        return None  # Unreachable
    theta2a = acos(cos_theta2)
    theta2b = -acos(cos_theta2)

    # θ1 for each θ2
    def theta1(theta2):
        k1 = arm1 + arm2 * cos(theta2)
        k2 = arm2 * sin(theta2)
        return atan2(dy, dx) - atan2(k2, k1)

    return [(theta1(theta2a), theta2a), (theta1(theta2b), theta2b)]


def get_joint_positions(theta1, theta2, arm1, arm2):
    x1 = ORIGIN[0] + arm1 * cos(theta1)
    y1 = ORIGIN[1] + arm1 * sin(theta1)
    x2 = x1 + arm2 * cos(theta1 + theta2)
    y2 = y1 + arm2 * sin(theta1 + theta2)
    return (x1, y1), (x2, y2)


def draw_cartesian_plane(surface, origin, width, height, spacing=25, font=None):
    # Draw grid
    for x in range(origin[0], width, spacing):
        pygame.draw.line(surface, (220, 220, 220), (x, 0), (x, height))
    for x in range(origin[0], -1, -spacing):
        pygame.draw.line(surface, (220, 220, 220), (x, 0), (x, height))
    for y in range(origin[1], height, spacing):
        pygame.draw.line(surface, (220, 220, 220), (0, y), (width, y))
    for y in range(origin[1], -1, -spacing):
        pygame.draw.line(surface, (220, 220, 220), (0, y), (width, y))
    # Draw axes
    pygame.draw.line(surface, (0, 0, 0), (origin[0], 0), (origin[0], height), 2)
    pygame.draw.line(surface, (0, 0, 0), (0, origin[1]), (width, origin[1]), 2)
    # Draw axis numbering every 50 units
    if font:
        label_spacing = 50
        # X axis (right of origin)
        for x in range(origin[0], width, spacing):
            label_val = x - origin[0]
            if label_val == 0 or label_val % label_spacing != 0:
                continue
            label = font.render(str(label_val), True, (0, 0, 0))
            surface.blit(label, (x + 2, origin[1] + 5))
        # X axis (left of origin)
        for x in range(origin[0], -1, -spacing):
            label_val = x - origin[0]
            if label_val == 0 or label_val % label_spacing != 0:
                continue
            label = font.render(str(label_val), True, (0, 0, 0))
            surface.blit(label, (x + 2, origin[1] + 5))
        # Y axis (above origin)
        for y in range(origin[1], -1, -spacing):
            label_val = origin[1] - y
            if label_val == 0 or label_val % label_spacing != 0:
                continue
            label = font.render(str(label_val), True, (0, 0, 0))
            surface.blit(label, (origin[0] + 5, y - 18))
        # Y axis (below origin)
        for y in range(origin[1], height, spacing):
            label_val = origin[1] - y
            if label_val == 0 or label_val % label_spacing != 0:
                continue
            label = font.render(str(label_val), True, (0, 0, 0))
            surface.blit(label, (origin[0] + 5, y - 18))


def lerp(a, b, t):
    return a + (b - a) * t


def animate_arm(start_angles, end_angles, steps):
    for i in range(steps + 1):
        t = i / steps
        theta1 = lerp(start_angles[0], end_angles[0], t)
        theta2 = lerp(start_angles[1], end_angles[1], t)
        yield (theta1, theta2)


def parse_coords(text):
    # Accepts "100,100" or "(100,100)" or " 100 , 100 "
    text = text.strip().replace("(", "").replace(")", "")
    parts = text.split(",")
    if len(parts) != 2:
        raise ValueError("Invalid coordinate format")
    # Interpret as relative to origin
    rel_x, rel_y = map(int, [p.strip() for p in parts])
    # Convert to screen coordinates
    return (ORIGIN[0] + rel_x, ORIGIN[1] - rel_y)


def animate_coords(start_pos, end_pos, steps):
    for i in range(steps + 1):
        t = i / steps
        x = int(lerp(start_pos[0], end_pos[0], t))
        y = int(lerp(start_pos[1], end_pos[1], t))
        yield (x, y)


pygame.init()
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Double Jointed RR Arm Simulator")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Times New Roman", 24)

ORIGIN = (screen_width // 2, screen_height // 2)

target = ORIGIN
start_coords = ORIGIN
end_coords = ORIGIN
animating = False
animation_gen = None
input_mode = None
input_text = ""
dragging = False
dragging_start = False

animation_speed = 60  # default frames for animation


# Add a variable to control menu visibility
menu_visible = True

# Add arm length input mode
arm_length_mode = None
arm_length_text = ""


def choose_best_solution(start_angles, end_solutions):
    # Choose the solution with minimal joint movement from start_angles
    min_dist = float("inf")
    best = None
    for angles in end_solutions:
        dist = abs(angles[0] - start_angles[0]) + abs(angles[1] - start_angles[1])
        if dist < min_dist:
            min_dist = dist
            best = angles
    return best


def get_angles_for_coords(coords, prefer_angles=None):
    sols = inverse_kinematics(coords[0], coords[1], ARM1, ARM2)
    if sols:
        if prefer_angles is not None:
            dist0 = abs(sols[0][0] - prefer_angles[0]) + abs(
                sols[0][1] - prefer_angles[1]
            )
            dist1 = abs(sols[1][0] - prefer_angles[0]) + abs(
                sols[1][1] - prefer_angles[1]
            )
            return sols[0] if dist0 <= dist1 else sols[1]
        return sols[0]
    return None


def animate_straight_line(start_pos, end_pos, steps, prefer_angles=None):
    # Save the initial configuration index (elbow up/down) at the start
    sols = inverse_kinematics(start_pos[0], start_pos[1], ARM1, ARM2)
    if sols is None:
        initial_index = 0
    else:
        if prefer_angles is not None:
            dist0 = abs(sols[0][0] - prefer_angles[0]) + abs(
                sols[0][1] - prefer_angles[1]
            )
            dist1 = abs(sols[1][0] - prefer_angles[0]) + abs(
                sols[1][1] - prefer_angles[1]
            )
            initial_index = 0 if dist0 <= dist1 else 1
        else:
            initial_index = 0
    for i in range(steps + 1):
        t = i / steps
        x = int(lerp(start_pos[0], end_pos[0], t))
        y = int(lerp(start_pos[1], end_pos[1], t))
        sols = inverse_kinematics(x, y, ARM1, ARM2)
        if sols is None:
            angles = None
        else:
            angles = sols[initial_index]
        yield (angles, (x, y))


def draw_instructions_menu(
    surface, font, ui_text, animation_speed, input_mode, input_text, arm1, arm2
):
    menu_width = 520
    line_height = 36
    extra_space = 90  # More room for arm length controls
    menu_height = len(ui_text) * line_height + extra_space
    menu_x = 0
    menu_y = 0
    # Draw menu background
    pygame.draw.rect(
        surface, (240, 240, 240), (menu_x, menu_y, menu_width, menu_height)
    )
    pygame.draw.rect(surface, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height), 2)
    # Draw instructions
    for i, line in enumerate(ui_text):
        img = font.render(line, True, (0, 0, 0))
        surface.blit(img, (menu_x + 20, menu_y + 20 + i * line_height))
    # Draw animation speed
    speed_text = f"Animation speed: {animation_speed} frames"
    img = font.render(speed_text, True, (0, 0, 128))
    surface.blit(img, (menu_x + 20, menu_y + 20 + len(ui_text) * line_height))
    # Draw arm lengths
    arm_text = f"Arm 1 length: {arm1}   Arm 2 length: {arm2}   (Press 1/2 to edit)"
    img = font.render(arm_text, True, (128, 0, 0))
    surface.blit(img, (menu_x + 20, menu_y + 20 + len(ui_text) * line_height + 30))
    # Draw input mode prompt if needed (only if not arm length mode)
    if input_mode and not arm_length_mode:
        prompt = f"Enter {input_mode} coords (x,y): {input_text}"
        img = font.render(prompt, True, (200, 0, 0))
        surface.blit(img, (menu_x + 20, menu_y + menu_height - 36))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if arm_length_mode:
                if event.key == pygame.K_RETURN:
                    try:
                        val = int(arm_length_text)
                        if arm_length_mode == "arm1":
                            ARM1 = max(10, val)
                        elif arm_length_mode == "arm2":
                            ARM2 = max(10, val)
                        arm_length_mode = None
                        arm_length_text = ""
                    except:
                        arm_length_text = ""
                        arm_length_mode = None
                elif event.key == pygame.K_BACKSPACE:
                    arm_length_text = arm_length_text[:-1]
                else:
                    arm_length_text += event.unicode
            elif input_mode:
                if event.key == pygame.K_RETURN:
                    try:
                        coords = parse_coords(input_text)
                        if input_mode == "start":
                            start_coords = coords
                            target = start_coords
                        elif input_mode == "end":
                            end_coords = coords
                        input_mode = None
                        input_text = ""
                    except:
                        input_text = ""
                        input_mode = None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
            else:
                if event.key == pygame.K_s:
                    input_mode = "start"
                    input_text = ""
                elif event.key == pygame.K_e:
                    input_mode = "end"
                    input_text = ""
                elif event.key == pygame.K_1:
                    arm_length_mode = "arm1"
                    arm_length_text = ""
                elif event.key == pygame.K_2:
                    arm_length_mode = "arm2"
                    arm_length_text = ""
                elif event.key == pygame.K_a and start_coords != end_coords:
                    start_angles = get_angles_for_coords(start_coords)
                    if start_angles:
                        animating = True
                        animation_gen = animate_straight_line(
                            start_coords,
                            end_coords,
                            animation_speed,
                            prefer_angles=start_angles,
                        )
                elif event.key == pygame.K_LEFT:
                    animation_speed = max(10, animation_speed - 10)
                elif event.key == pygame.K_RIGHT:
                    animation_speed = min(300, animation_speed + 10)
                elif event.key == pygame.K_m:
                    menu_visible = not menu_visible
        elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
            # Check if dragging start or end point
            if (
                event.button == 1
                and (
                    (start_coords[0] - event.pos[0]) ** 2
                    + (start_coords[1] - event.pos[1]) ** 2
                )
                < 100
            ):
                dragging_start = True
            elif (
                event.button == 1
                and (
                    (end_coords[0] - event.pos[0]) ** 2
                    + (end_coords[1] - event.pos[1]) ** 2
                )
                < 100
            ):
                dragging = True
            else:
                target = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            dragging_start = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                end_coords = event.pos
                target = end_coords
            elif dragging_start:
                start_coords = event.pos
                target = start_coords

    # Animate arm if needed
    if animating and animation_gen:
        try:
            result = next(animation_gen)
            current_angles, target = result
            chosen_sol = current_angles
        except StopIteration:
            animating = False
            target = end_coords
            chosen_sol = get_angles_for_coords(target, prefer_angles=current_angles)
    else:
        sols = inverse_kinematics(target[0], target[1], ARM1, ARM2)
        chosen_sol = None
        if sols:
            start_angles = get_angles_for_coords(start_coords)
            chosen_sol = (
                get_angles_for_coords(target, prefer_angles=start_angles)
                if start_angles
                else sols[0]
            )

    screen.fill((255, 255, 255))
    draw_cartesian_plane(
        screen, ORIGIN, screen_width, screen_height, spacing=25, font=font
    )
    # Draw origin
    pygame.draw.circle(screen, (0, 0, 0), ORIGIN, 5)
    # Draw start/end points
    pygame.draw.circle(screen, (0, 200, 255), start_coords, 7)
    pygame.draw.circle(screen, (255, 128, 0), end_coords, 7)
    # Draw target
    pygame.draw.circle(screen, (0, 128, 255), target, 5)
    # Draw arm (only one solution)
    if chosen_sol:
        theta1, theta2 = chosen_sol
        joint1, end = get_joint_positions(theta1, theta2, ARM1, ARM2)
        pygame.draw.line(screen, (255, 0, 0), ORIGIN, joint1, 5)
        pygame.draw.line(screen, (255, 0, 0), joint1, end, 5)
        pygame.draw.circle(screen, (255, 0, 0), (int(joint1[0]), int(joint1[1])), 8, 2)
        pygame.draw.circle(screen, (255, 0, 0), (int(end[0]), int(end[1])), 8, 2)
        # Arm labels
        arm1_label = font.render("Arm 1", True, (255, 0, 0))
        arm2_label = font.render("Arm 2", True, (255, 0, 0))
        joint0_label = font.render("Joint 0", True, (0, 0, 0))
        joint1_label = font.render("Joint 1", True, (0, 0, 0))
        end_label = font.render("End", True, (0, 0, 0))
        # Place labels near the arms/joints
        screen.blit(
            arm1_label,
            ((ORIGIN[0] + joint1[0]) // 2, (ORIGIN[1] + joint1[1]) // 2 - 20),
        )
        screen.blit(
            arm2_label,
            ((joint1[0] + end[0]) // 2, (joint1[1] + end[1]) // 2 - 20),
        )
        screen.blit(joint0_label, (ORIGIN[0] - 40, ORIGIN[1] - 20))
        screen.blit(joint1_label, (int(joint1[0]) - 40, int(joint1[1]) - 20))
        screen.blit(end_label, (int(end[0]) + 10, int(end[1]) - 20))
    # Instructions menu
    if menu_visible:
        ui_text = [
            "S: Set start coords (format: x,y) [relative to centre]",
            "E: Set end coords (format: x,y) [relative to centre]",
            "A: Animate arm from start to end",
            "LEFT/RIGHT: Adjust animation speed",
            "1/2: Edit arm lengths",
            "M: Toggle menu visibility",
            "Drag orange dot to move end coords",
            "Click: Set target directly",
        ]
        draw_instructions_menu(
            screen, font, ui_text, animation_speed, input_mode, input_text, ARM1, ARM2
        )
    # Show arm length input as red text outside menu if active
    if arm_length_mode:
        prompt = f"Enter {arm_length_mode.upper()} length: {arm_length_text}"
        img = font.render(prompt, True, (200, 0, 0))
        screen.blit(img, (540, 40))
    pygame.display.flip()
    clock.tick(60)
