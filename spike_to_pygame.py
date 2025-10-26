"""
Parse a working_spike.py file and emit a simple instruction list for a pygame sim.

Usage:
    python spike_to_pygame.py path/to/working_spike.py --out instructions.json
Options:
    --wheel-radius   wheel radius in mm (default 24)
    --wheel-base     wheel base in mm (default 120)
    --pixel-scale    mm -> pixels scale for visualization (default 1.0)
"""

import ast
import json
import math
import sys
from pathlib import Path
import argparse
import threading

KNOWN_FUNCS = {
    "gyro_follow": "gyro_follow",
    "gyro_turn": "gyro_turn",
    "motor.run_for_degrees": "motor_run_for_degrees",
    "motor.run_to_relative_position": "motor_run_to_rel",
    "motor_pair.move_for_degrees": "motor_pair_move_for_degrees",
}


def deg_to_mm(deg, wheel_radius_mm):
    return float(deg) * (2.0 * math.pi * float(wheel_radius_mm) / 360.0)


def node_name(n):
    # return dotted name for ast.Call.func (Name or Attribute)
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        parts = []
        cur = n
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def eval_node(n):
    # try to extract literal numeric or string values; otherwise None
    try:
        return ast.literal_eval(n)
    except Exception:
        return None


def extract_calls_from_func(func_node):
    calls = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            name = node_name(node.func)
            if name is None:
                continue
            # collect keywords and positional literals
            kw = {}
            for k in node.keywords:
                kw[k.arg] = eval_node(k.value)
            # also collect simple positional args (by index)
            pos = [eval_node(a) for a in node.args]
            calls.append((name, pos, kw, node.lineno))
    return calls


def parse_spike_file(path, wheel_radius_mm=24.0, wheel_base_mm=120.0, pixel_scale=2):
    src = Path(path).read_text()
    tree = ast.parse(src, filename=str(path))
    instructions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.endswith("_main"):
            calls = extract_calls_from_func(node)
            for name, pos, kw, lineno in calls:
                entry = {"source_func": node.name, "lineno": lineno, "call": name}
                if name.endswith("gyro_follow") or name == "gyro_follow":
                    heading = kw.get("heading", pos[0] if len(pos) > 0 else None)
                    gain = kw.get("gain", None)
                    speed = kw.get("speed", None)
                    distance_deg = kw.get("distance", None)
                    condition = kw.get("condition", None)
                    distance_mm = None
                    pix = None
                    if distance_deg is not None:
                        distance_mm = deg_to_mm(float(distance_deg), wheel_radius_mm)
                        pix = distance_mm * float(pixel_scale)
                    entry.update(
                        {
                            "type": "gyro_follow",
                            "heading": heading,
                            "gain": gain,
                            "speed": speed,
                            "distance_deg": distance_deg,
                            "distance_mm": distance_mm,
                            "distance_px": pix,
                            "condition": None if condition is None else str(condition),
                        }
                    )
                elif name.endswith("gyro_turn") or name == "gyro_turn":
                    steering = kw.get("steering", pos[0] if len(pos) > 0 else None)
                    heading = kw.get("heading", None)
                    speed = kw.get("speed", None)
                    entry.update(
                        {
                            "type": "gyro_turn",
                            "steering": steering,
                            "heading": heading,
                            "speed": speed,
                        }
                    )
                elif name.endswith("run_for_degrees") or name.endswith(
                    "run_for_degrees"
                ):
                    # motor.run_for_degrees(port, degrees, speed)
                    degrees = None
                    port = None
                    speed = None
                    if len(pos) >= 2:
                        port = pos[0]
                        degrees = pos[1]
                    if len(pos) >= 3:
                        speed = pos[2]
                    # also check keywords
                    degrees = kw.get("degrees", degrees)
                    speed = kw.get("speed", speed)
                    entry.update(
                        {
                            "type": "motor_run_for_degrees",
                            "port": port,
                            "degrees": degrees,
                            "mm": (
                                None
                                if degrees is None
                                else deg_to_mm(float(degrees), wheel_radius_mm)
                            ),
                            "speed": speed,
                        }
                    )
                elif name.endswith("run_to_relative_position"):
                    port = pos[0] if len(pos) >= 1 else None
                    position = pos[1] if len(pos) >= 2 else None
                    if "position" in kw:
                        position = kw["position"]
                    entry.update(
                        {
                            "type": "motor_run_to_rel",
                            "port": port,
                            "position_deg": position,
                            "position_mm": (
                                None
                                if position is None
                                else deg_to_mm(float(position), wheel_radius_mm)
                            ),
                        }
                    )
                elif name.endswith("move_for_degrees"):
                    # motor_pair.move_for_degrees(pair, steering, degrees)
                    steering = None
                    degrees = None
                    if len(pos) >= 2:
                        steering = pos[0]
                        degrees = pos[1]
                    steering = kw.get("steering", steering)
                    degrees = kw.get("degrees", degrees)
                    entry.update(
                        {
                            "type": "motor_pair_move_for_degrees",
                            "steering": steering,
                            "degrees": degrees,
                            "mm": (
                                None
                                if degrees is None
                                else deg_to_mm(float(degrees), wheel_radius_mm)
                            ),
                        }
                    )
                else:
                    # unknown call -- record name and raw args
                    entry.update({"type": "call", "args_pos": pos, "args_kw": kw})
                instructions.append(entry)
    return instructions


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(
        "spike_file",
        nargs="?",
        default="working_spike.py",
        help="path to working_spike.py (default: working_spike.py in current folder)",
    )
    p.add_argument("--wheel-radius", type=float, default=24.0, help="wheel radius mm")
    p.add_argument("--wheel-base", type=float, default=120.0, help="wheel base mm")
    p.add_argument("--pixel-scale", type=float, default=1.0, help="mm -> pixels scale")
    p.add_argument(
        "--board-image",
        default="FLL 2025-2026 Board.png",
        help="path to board background image (optional) (default: FLL 2025-2026 Board.png)",
    )
    p.add_argument("--width", type=int, default=900, help="window width (pixels)")
    p.add_argument("--height", type=int, default=600, help="window height (pixels)")
    p.add_argument(
        "--robot-x", type=float, default=200.0, help="initial robot x (pixels)"
    )
    p.add_argument(
        "--robot-y", type=float, default=200.0, help="initial robot y (pixels)"
    )
    p.add_argument(
        "--speed-scale",
        type=float,
        default=1.0,
        help="global multiplier for simulated speeds (use >1.0 to increase)",
    )
    p.add_argument(
        "--run-speed-mult",
        type=float,
        default=3.0,
        help="multiplier applied to speeds during instruction playback (gyro/motor runs)",
    )
    p.add_argument(
        "--out", default=None, help="optional: write instructions JSON to this file"
    )
    args = p.parse_args(argv[1:])

    if args.spike_file == "working_spike.py":
        print("No spike_file provided — defaulting to ./working_spike.py")

    instr = parse_spike_file(
        args.spike_file,
        wheel_radius_mm=args.wheel_radius,
        wheel_base_mm=args.wheel_base,
        pixel_scale=args.pixel_scale,
    )

    # optional: still write instructions json if requested
    if args.out:
        outp = Path(args.out)
        outp.write_text(json.dumps(instr, indent=2))
        print(f"Wrote {len(instr)} instructions to {outp.resolve()}")

    # Group instructions by source function (each *_main)
    mains = {}
    for e in instr:
        mains.setdefault(e["source_func"], []).append(e)

    # Try to import pygame
    try:
        import pygame
    except Exception as e:
        print("pygame not available:", e)
        return 1

    pygame.init()
    font = pygame.font.SysFont(None, 18)
    clock = pygame.time.Clock()

    # draw layout constants (used for scaling board and panel)
    pad = 4
    bw = 180
    panel_width = bw + pad

    # load board image and compute virtual (logical) board size, but scale the display to fit the screen
    board_img = None
    board_rect_virtual = None
    board_rect_display = None
    board_img_display = None
    if args.board_image:
        try:
            img = pygame.image.load(args.board_image)
            iw, ih = img.get_size()
            if iw == 0 or ih == 0:
                raise Exception("invalid image size")

            # virtual (logical) board size = original * (pixel_scale * 1.0) -> smaller board
            virt_scale = float(args.pixel_scale) * 1.0
            virt_w = max(1, int(iw * virt_scale))
            virt_h = max(1, int(ih * virt_scale))

            # desired display size tries to show full virtual board but may be downscaled to fit the screen
            desired_w = virt_w
            desired_h = virt_h
            desired_window_w = desired_w + panel_width + pad
            desired_window_h = desired_h

            # screen limits
            info = pygame.display.Info()
            max_w = max(800, info.current_w - 50)
            max_h = max(600, info.current_h - 50)

            # compute display_scale so board+menu fit on screen; never upscale above 1.0
            display_scale = min(
                1.0, max_w / float(desired_window_w), max_h / float(desired_window_h)
            )
            display_w = max(1, int(virt_w * display_scale))
            display_h = max(1, int(virt_h * display_scale))

            window_w = display_w + panel_width + pad
            window_h = display_h

            # create window sized to show scaled board + menu
            screen = pygame.display.set_mode((window_w, window_h))
            pygame.display.set_caption("Spike -> Pygame FLL Sim")

            # prepare images/rects
            board_img_display = pygame.transform.smoothscale(
                img, (display_w, display_h)
            )
            board_rect_display = pygame.Rect(0, 0, display_w, display_h)
            board_rect_virtual = pygame.Rect(0, 0, virt_w, virt_h)

            # remember scale for rendering conversions
            render_scale = display_scale
            # update args so UI layout uses actual window size
            args.width = window_w
            args.height = window_h
        except Exception as e:
            print("Failed to load board image:", e)
            screen = pygame.display.set_mode((args.width, args.height))
            pygame.display.set_caption("Spike -> Pygame FLL Sim")
            board_rect_virtual = pygame.Rect(
                0, 0, args.width - panel_width - pad, args.height
            )
            board_rect_display = board_rect_virtual.copy()
            board_img_display = None
            render_scale = 1.0
    else:
        screen = pygame.display.set_mode((args.width, args.height))
        pygame.display.set_caption("Spike -> Pygame FLL Sim")
        board_rect_virtual = pygame.Rect(
            0, 0, args.width - panel_width - pad, args.height
        )
        board_rect_display = board_rect_virtual.copy()
        board_img_display = None
        render_scale = 1.0

    # simulation state (include status so run thread and UI share it)
    robot = {
        "x": float(args.robot_x),
        "y": float(args.robot_y),
        "heading": 0.0,
        "status": "Idle",
    }
    # clamp initial robot into virtual board area
    robot["x"] = max(board_rect_virtual.left, min(robot["x"], board_rect_virtual.right))
    robot["y"] = max(board_rect_virtual.top, min(robot["y"], board_rect_virtual.bottom))

    # keyboard/manual control state
    control = {"forward": False, "back": False, "left": False, "right": False}

    sim_lock = threading.Lock()
    running_instr_thread = None
    stop_flag = threading.Event()

    # helper: convert deg/sec wheel speed to mm/sec linear speed (approx)
    def wheel_deg_s_to_linear_mm_s(deg_s):
        return deg_to_mm(deg_s, args.wheel_radius)

    # animator for a list of instructions
    def run_instructions(instr_list):
        stop_flag.clear()
        for e in instr_list:
            if stop_flag.is_set():
                break
            typ = e.get("type")
            if typ == "gyro_turn":
                target = e.get("heading")
                if target is None:
                    continue
                # animate rotation
                speed_deg_s = e.get("speed") or 90.0  # default rotation speed deg/s
                # if negative speed used in code, take magnitude; apply global & run multipliers
                rot_speed = (
                    abs(float(speed_deg_s))
                    * float(args.speed_scale)
                    * float(args.run_speed_mult)
                )
                while True:
                    if stop_flag.is_set():
                        break
                    with sim_lock:
                        cur = robot["heading"]
                    err = (float(target) - float(cur) + 180) % 360 - 180
                    if abs(err) <= 1.0:
                        with sim_lock:
                            robot["heading"] = float(target)
                        break
                    step = math.copysign(min(abs(err), rot_speed / 30.0), err)
                    with sim_lock:
                        robot["heading"] = (robot["heading"] + step) % 360
                    clock.tick(60)
            elif typ == "gyro_follow":
                dist_mm = e.get("distance_mm") or 0.0
                if dist_mm == 0.0:
                    continue
                speed_deg_s = e.get("speed")
                if speed_deg_s:
                    v_mm_s = wheel_deg_s_to_linear_mm_s(float(speed_deg_s))
                    # apply global speed scaling
                    v_mm_s *= float(args.speed_scale) * float(args.run_speed_mult)
                    if v_mm_s <= 0:
                        v_mm_s = (
                            50.0 * float(args.speed_scale) * float(args.run_speed_mult)
                        )
                else:
                    v_mm_s = 50.0 * float(args.speed_scale) * float(args.run_speed_mult)
                duration = abs(float(dist_mm)) / v_mm_s if v_mm_s > 0 else 0.0
                steps = max(1, int(duration * 60))
                dx_mm = float(dist_mm) / steps
                for _ in range(steps):
                    if stop_flag.is_set():
                        break
                    with sim_lock:
                        rad = math.radians(robot["heading"])
                        robot["x"] += dx_mm * args.pixel_scale * math.cos(rad)
                        robot["y"] += dx_mm * args.pixel_scale * math.sin(rad)
                        # Check bounds and stop if we leave the virtual board area
                        if (
                            robot["x"] < board_rect_virtual.left
                            or robot["x"] > board_rect_virtual.right
                            or robot["y"] < board_rect_virtual.top
                            or robot["y"] > board_rect_virtual.bottom
                        ):
                            # clamp to virtual board edge, set status and request stop
                            robot["x"] = max(
                                board_rect_virtual.left,
                                min(robot["x"], board_rect_virtual.right),
                            )
                            robot["y"] = max(
                                board_rect_virtual.top,
                                min(robot["y"], board_rect_virtual.bottom),
                            )
                            robot["status"] = "Out of bounds"
                            stop_flag.set()
                            break
                    clock.tick(60)
            elif typ == "motor_run_for_degrees" or typ == "motor_pair_move_for_degrees":
                degrees = e.get("degrees") or 0.0
                mm = e.get("mm") or 0.0
                # move forward by mm (simple)
                dist_mm = float(mm)
                # use default speed
                v_mm_s = 50.0 * float(args.speed_scale) * float(args.run_speed_mult)
                duration = abs(dist_mm) / v_mm_s if v_mm_s > 0 else 0.0
                steps = max(1, int(duration * 60))
                dx_mm = float(dist_mm) / steps
                for _ in range(steps):
                    if stop_flag.is_set():
                        break
                    with sim_lock:
                        rad = math.radians(robot["heading"])
                        robot["x"] += dx_mm * args.pixel_scale * math.cos(rad)
                        robot["y"] += dx_mm * args.pixel_scale * math.sin(rad)
                        if (
                            robot["x"] < board_rect_virtual.left
                            or robot["x"] > board_rect_virtual.right
                            or robot["y"] < board_rect_virtual.top
                            or robot["y"] > board_rect_virtual.bottom
                        ):
                            robot["x"] = max(
                                board_rect_virtual.left,
                                min(robot["x"], board_rect_virtual.right),
                            )
                            robot["y"] = max(
                                board_rect_virtual.top,
                                min(robot["y"], board_rect_virtual.bottom),
                            )
                            robot["status"] = "Out of bounds"
                            stop_flag.set()
                            break
                    clock.tick(60)
            else:
                # unknown: skip
                continue
        return

    # build UI buttons for each main
    button_rects = []
    pad = 4
    bw = 180
    # place the menu immediately to the right of the board display (no visible gap)
    x0 = board_rect_display.right
    y0 = pad
    for idx, name in enumerate(sorted(mains.keys())):
        rect = pygame.Rect(x0, y0 + idx * 36, bw, 30)
        button_rects.append((rect, name))

    stop_rect = pygame.Rect(x0, args.height - 50, bw, 34)

    while True:
        # event handling (mouse/buttons + keyboard)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                stop_flag.set()
                if running_instr_thread and running_instr_thread.is_alive():
                    running_instr_thread.join(timeout=0.5)
                pygame.quit()
                return 0
            elif ev.type == pygame.KEYDOWN:
                # manual control keys: arrows or WASD
                if ev.key in (pygame.K_UP, pygame.K_w):
                    control["forward"] = True
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    control["back"] = True
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    control["left"] = True
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    control["right"] = True
                # when starting manual control, stop any playback
                if any(control.values()):
                    stop_flag.set()
                    if running_instr_thread and running_instr_thread.is_alive():
                        running_instr_thread.join(timeout=0.2)
                    with sim_lock:
                        robot["status"] = "Manual"
            elif ev.type == pygame.KEYUP:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    control["forward"] = False
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    control["back"] = False
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    control["left"] = False
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    control["right"] = False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for rect, name in button_rects:
                    if rect.collidepoint(mx, my):
                        # start instructions for this main
                        if running_instr_thread and running_instr_thread.is_alive():
                            stop_flag.set()
                            running_instr_thread.join(timeout=0.2)
                        stop_flag.clear()
                        instr_list = mains.get(name, [])
                        with sim_lock:
                            robot["status"] = f"Running {name}"
                        running_instr_thread = threading.Thread(
                            target=run_instructions, args=(instr_list,), daemon=True
                        )
                        running_instr_thread.start()
                if stop_rect.collidepoint(mx, my):
                    stop_flag.set()
                    with sim_lock:
                        robot["status"] = "Stopped"

        # manual control movement (applies every frame if keys held)
        # use a reasonable default dt (frame time)
        dt = max(1.0 / 60.0, clock.get_time() / 1000.0)
        if any(control.values()):
            # stop running instructions if manual control active
            stop_flag.set()
            if running_instr_thread and running_instr_thread.is_alive():
                running_instr_thread.join(timeout=0.2)
            # forward/back speed in mm/s (adjust as needed)
            move_speed_mm_s = 200.0 * float(args.speed_scale)
            rot_speed_deg_s = 120.0 * float(args.speed_scale)
            with sim_lock:
                # rotation
                if control["left"]:
                    robot["heading"] = (robot["heading"] - rot_speed_deg_s * dt) % 360.0
                if control["right"]:
                    robot["heading"] = (robot["heading"] + rot_speed_deg_s * dt) % 360.0
                # translation
                if control["forward"] or control["back"]:
                    dir_mult = 1.0 if control["forward"] else -1.0
                    dist_mm = move_speed_mm_s * dt * dir_mult
                    rad = math.radians(robot["heading"])
                    robot["x"] += dist_mm * args.pixel_scale * math.cos(rad)
                    robot["y"] += dist_mm * args.pixel_scale * math.sin(rad)
                    # clamp to virtual board
                    robot["x"] = max(
                        board_rect_virtual.left,
                        min(robot["x"], board_rect_virtual.right),
                    )
                    robot["y"] = max(
                        board_rect_virtual.top,
                        min(robot["y"], board_rect_virtual.bottom),
                    )

        # draw
        screen.fill((200, 200, 200))
        if board_img_display:
            screen.blit(board_img_display, board_rect_display.topleft)
        else:
            # fill the board area (no border)
            screen.fill((200, 200, 200), board_rect_display)

        # compute robot display position from virtual coords
        with sim_lock:
            rx_disp = int(
                board_rect_display.left
                + (robot["x"] - board_rect_virtual.left) * render_scale
            )
            ry_disp = int(
                board_rect_display.top
                + (robot["y"] - board_rect_virtual.top) * render_scale
            )
            rh = robot["heading"]
            status_text = robot.get("status", "Idle")
        # robot is a light blue rotated rectangle (robot-centric orientation)
        ROBOT_SCALE = 0.75
        ui_scale = max(1.0, 1.0 / max(render_scale, 0.2))
        rect_w = max(8, int(32 * ROBOT_SCALE * ui_scale))
        rect_h = max(6, int(20 * ROBOT_SCALE * ui_scale))
        robot_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        robot_color = (173, 216, 230)  # light blue
        robot_surf.fill(robot_color)
        # draw a darker nose marker
        pygame.draw.rect(
            robot_surf,
            (120, 160, 180),
            (
                rect_w - max(4, int(6 * ROBOT_SCALE)),
                0,
                max(4, int(6 * ROBOT_SCALE)),
                rect_h,
            ),
        )
        rot_surf = pygame.transform.rotate(robot_surf, -rh)
        rs_rect = rot_surf.get_rect(center=(rx_disp, ry_disp))
        screen.blit(rot_surf, rs_rect.topleft)

        # draw buttons panel directly adjacent to the board (no extra gap)
        pygame.draw.rect(screen, (220, 220, 220), (x0, 0, bw, args.height))
        for rect, name in button_rects:
            pygame.draw.rect(screen, (200, 200, 200), rect)
            txt = font.render(name, True, (0, 0, 0))
            screen.blit(txt, (rect.x + 6, rect.y + 6))
        pygame.draw.rect(screen, (200, 80, 80), stop_rect)
        stop_txt = font.render("Stop", True, (255, 255, 255))
        screen.blit(stop_txt, (stop_rect.x + 8, stop_rect.y + 8))

        status_surf = font.render(status_text, True, (0, 0, 0))
        screen.blit(status_surf, (args.width - bw - pad + 6, args.height - 24))

        pygame.display.flip()
        clock.tick(60)

    # unreachable
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
