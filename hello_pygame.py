import pygame
import sys
import math
import random

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Dodge Game")

WHITE = (0, 0, 0)
GREEN = (0, 255, 0)
BLACK = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 150, 255)

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

# 👉 최고 점수 불러오기
try:
    with open("highscore.txt", "r") as f:
        highscore = int(f.read())
except:
    highscore = 0

def reset_game():
    return {
        "x": 400,
        "y": 300,
        "player_alpha": 255,
        "hit_count": 0,
        "shake_timer": 0,
        "circles": [],
        "rects": [],
        "spawn_timer": 0,
        "rect_spawn_timer": 0,
        "score": 0,
        "time_alive": 0,
        "game_over": False,
        "new_record": False
    }

state = reset_game()
running = True

while running:
    dt = clock.tick(60)

    state["spawn_timer"] += dt
    state["rect_spawn_timer"] += dt

    # 👉 난이도 증가 계수
    difficulty = 1 + state["time_alive"] * 0.0005

    if not state["game_over"]:
        state["time_alive"] += dt
        state["score"] += dt * (1 + state["time_alive"] * 0.001)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                state = reset_game()

    # 🎮 이동
    if not state["game_over"]:
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1

        if dx != 0 or dy != 0:
            length = math.sqrt(dx**2 + dy**2)
            dx /= length
            dy /= length

        state["x"] += dx * 7
        state["y"] += dy * 7

        state["x"] = max(30, min(800 - 30, state["x"]))
        state["y"] = max(30, min(600 - 30, state["y"]))

        # 🔴 원 생성 (점점 많아짐 + 커짐)
        spawn_delay = max(300, 800 - state["time_alive"] * 0.1)

        if state["spawn_timer"] > spawn_delay:
            state["spawn_timer"] = 0
            state["circles"].append({
                "x": random.randint(0, 800),
                "y": random.randint(0, 600),
                "time": 0,
                "max_radius": random.randint(60, int(150 + state["time_alive"] * 0.05))
            })

        # 🟦 사각형 생성 (속도 증가)
        if state["rect_spawn_timer"] > 1200:
            state["rect_spawn_timer"] = 0
            side = random.choice(["top", "bottom", "left", "right"])

            base_speed = random.uniform(4, 7)
            speed = base_speed * difficulty

            if side == "top":
                rx, ry = random.randint(0, 800), -20
                vx, vy = random.uniform(-2, 2), speed
            elif side == "bottom":
                rx, ry = random.randint(0, 800), 620
                vx, vy = random.uniform(-2, 2), -speed
            elif side == "left":
                rx, ry = -20, random.randint(0, 600)
                vx, vy = speed, random.uniform(-2, 2)
            else:
                rx, ry = 820, random.randint(0, 600)
                vx, vy = -speed, random.uniform(-2, 2)

            state["rects"].append({
                "x": rx,
                "y": ry,
                "vx": vx,
                "vy": vy,
                "size": 15
            })

    screen.fill(WHITE)

    # 🔴 원 처리
    new_circles = []
    for c in state["circles"]:
        c["time"] += dt
        t = c["time"]

        if t < 2000:
            progress = t / 2000
            radius = int(c["max_radius"] * (progress ** 0.3))
            alpha = 255
        elif t < 2500:
            radius = c["max_radius"]
            alpha = int(255 * (1 - (t - 2000) / 500))
        else:
            continue

        surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 0, 0, alpha), (radius, radius), radius, width=4)
        screen.blit(surf, (c["x"] - radius, c["y"] - radius))

        if not state["game_over"]:
            dist = math.hypot(state["x"] - c["x"], state["y"] - c["y"])
            if dist < radius and t < 2000:
                state["hit_count"] += 1
                state["player_alpha"] = max(0, state["player_alpha"] - 85)
                state["shake_timer"] = 300
                c["time"] = 2500

                if state["hit_count"] >= 3:
                    state["game_over"] = True

        new_circles.append(c)

    state["circles"] = new_circles

    # 🟦 사각형 처리
    new_rects = []
    for r in state["rects"]:
        r["x"] += r["vx"]
        r["y"] += r["vy"]

        rect = pygame.Rect(r["x"], r["y"], r["size"], r["size"])
        pygame.draw.rect(screen, BLUE, rect)

        if not state["game_over"]:
            player_rect = pygame.Rect(
                state["x"] - 30, state["y"] - 30, 60, 60
            )

            if rect.colliderect(player_rect):
                state["hit_count"] += 1
                state["player_alpha"] = max(0, state["player_alpha"] - 85)
                state["shake_timer"] = 300

                if state["hit_count"] >= 3:
                    state["game_over"] = True
                continue

        if -50 < r["x"] < 850 and -50 < r["y"] < 650:
            new_rects.append(r)

    state["rects"] = new_rects

    # 📳 흔들림
    offset_x, offset_y = 0, 0
    if state["shake_timer"] > 0:
        state["shake_timer"] -= dt
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

    # 🔺 플레이어
    player_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.polygon(
        player_surf,
        (0, 255, 0, state["player_alpha"]),
        [(30, 0), (0, 60), (60, 60)]
    )
    screen.blit(player_surf, (state["x"] - 30 + offset_x, state["y"] - 30 + offset_y))

    # 👉 최고 점수 갱신
    if state["game_over"] and not state["new_record"]:
        if state["score"] > highscore:
            highscore = int(state["score"])
            state["new_record"] = True
            with open("highscore.txt", "w") as f:
                f.write(str(highscore))

    # FPS
    fps = clock.get_fps()
    screen.blit(font.render(f"FPS: {int(fps)}", True, BLACK), (10, 10))

    # 점수 + 👑
    score_display = f"Score: {int(state['score'])}"
    if state["game_over"] and state["new_record"]:
        score_display += " 👑"
    screen.blit(font.render(score_display, True, BLACK), (10, 40))

    # 최고 점수
    screen.blit(font.render(f"High: {highscore}", True, BLACK), (10, 70))

    # 게임오버
    if state["game_over"]:
        screen.blit(font.render("GAME OVER (Press R)", True, (255, 50, 50)), (250, 280))

    pygame.display.flip()

pygame.quit()
sys.exit()