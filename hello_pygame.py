import pygame
import sys
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")

WHITE = (0, 0, 0)
BLUE = (0, 255, 0)
BLACK = (255, 255, 255)

clock = pygame.time.Clock()
running = True

x = 600
y = 100
speed = 10

# 👉 폰트 설정
font = pygame.font.SysFont(None, 30)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    if keys[pygame.K_w]:
        dy -= 1
    if keys[pygame.K_s]:
        dy += 1
    if keys[pygame.K_a]:
        dx -= 1
    if keys[pygame.K_d]:
        dx += 1

    # 👉 대각선 속도 보정
    if dx != 0 or dy != 0:
        length = math.sqrt(dx**2 + dy**2)
        dx /= length
        dy /= length

    x += dx * speed
    y += dy * speed
    
    # 👉 화면 경계 제한 (반지름 100)
radius = 100

x = max(radius, min(800 - radius, x))
y = max(radius, min(600 - radius, y))

    screen.fill(WHITE)
    pygame.draw.circle(screen, BLUE, (int(x), int(y)), 100)

    # 👉 FPS 계산 및 출력
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {int(fps)}", True, BLACK)
    screen.blit(fps_text, (10, 10))  # 좌측 상단

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()