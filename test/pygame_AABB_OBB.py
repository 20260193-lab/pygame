import pygame
import sys
import math

pygame.init()

# 화면 설정
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Collision Comparison")

clock = pygame.time.Clock()

# 폰트
font = pygame.font.SysFont(None, 28)

# 색상
GRAY = (150, 150, 150)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# 크기
box_size = 50

# 플레이어
player_x = 100
player_y = 100
player_speed = 5

# 중앙 오브젝트
center_x = WIDTH // 2
center_y = HEIGHT // 2

angle = 0
rotation_speed = 1

# -------------------------
# OBB 꼭짓점
# -------------------------
def get_obb_points(cx, cy, w, h, angle_deg):
    rad = math.radians(angle_deg)
    hw, hh = w / 2, h / 2

    corners = [
        (-hw, -hh),
        ( hw, -hh),
        ( hw,  hh),
        (-hw,  hh)
    ]

    rotated = []
    for x, y in corners:
        rx = x * math.cos(rad) - y * math.sin(rad)
        ry = x * math.sin(rad) + y * math.cos(rad)
        rotated.append((cx + rx, cy + ry))

    return rotated

# -------------------------
# SAT 충돌
# -------------------------
def dot(a, b):
    return a[0]*b[0] + a[1]*b[1]

def normalize(v):
    length = math.sqrt(v[0]**2 + v[1]**2)
    return (v[0]/length, v[1]/length)

def get_axes(points):
    axes = []
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i+1) % len(points)]

        edge = (p2[0] - p1[0], p2[1] - p1[1])
        normal = (-edge[1], edge[0])
        axes.append(normalize(normal))

    return axes

def project(points, axis):
    min_p = dot(points[0], axis)
    max_p = min_p

    for p in points:
        proj = dot(p, axis)
        min_p = min(min_p, proj)
        max_p = max(max_p, proj)

    return min_p, max_p

def is_colliding(poly1, poly2):
    axes = get_axes(poly1) + get_axes(poly2)

    for axis in axes:
        min1, max1 = project(poly1, axis)
        min2, max2 = project(poly2, axis)

        if max1 < min2 or max2 < min1:
            return False

    return True

# -------------------------

running = True
while running:
    bg_color = WHITE

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # 이동
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
    if keys[pygame.K_UP]:
        player_y -= player_speed
    if keys[pygame.K_DOWN]:
        player_y += player_speed

    # 회전 속도
    if keys[pygame.K_z]:
        rotation_speed = 5
    else:
        rotation_speed = 1

    angle += rotation_speed

    # Rect
    player_rect = pygame.Rect(player_x, player_y, box_size, box_size)
    center_rect = pygame.Rect(0, 0, box_size, box_size)
    center_rect.center = (center_x, center_y)

    # 중심
    player_center = player_rect.center
    center_center = center_rect.center

    # -------------------------
    # 🔵 Circle 충돌
    # -------------------------
    radius = box_size // 2

    dx = player_center[0] - center_center[0]
    dy = player_center[1] - center_center[1]
    distance = math.sqrt(dx*dx + dy*dy)

    circle_hit = distance <= radius * 2

    # -------------------------
    # 🔴 AABB 충돌
    # -------------------------
    aabb_hit = player_rect.colliderect(center_rect)

    # -------------------------
    # 🟢 OBB 충돌 (SAT)
    # -------------------------
    player_points = [
        player_rect.topleft,
        player_rect.topright,
        player_rect.bottomright,
        player_rect.bottomleft
    ]

    obb_points = get_obb_points(center_x, center_y, box_size, box_size, angle)

    obb_hit = is_colliding(player_points, obb_points)

    # -------------------------
    # 화면
    # -------------------------
    screen.fill(bg_color)

    # 도형 그리기
    pygame.draw.rect(screen, GRAY, player_rect)
    pygame.draw.rect(screen, RED, player_rect, 2)

    pygame.draw.rect(screen, GRAY, center_rect)
    pygame.draw.rect(screen, RED, center_rect, 2)

    pygame.draw.circle(screen, BLUE, player_center, radius, 2)
    pygame.draw.circle(screen, BLUE, center_center, radius, 2)

    pygame.draw.polygon(screen, GREEN, obb_points, 2)

    # -------------------------
    # 텍스트 표시
    # -------------------------
    circle_text = "Circle: HIT" if circle_hit else "Circle: MISS"
    aabb_text = "AABB: HIT" if aabb_hit else "AABB: MISS"
    obb_text = "OBB: HIT" if obb_hit else "OBB: MISS"

    text1 = font.render(circle_text, True, BLACK)
    text2 = font.render(aabb_text, True, BLACK)
    text3 = font.render(obb_text, True, BLACK)

    screen.blit(text1, (10, 10))
    screen.blit(text2, (10, 40))
    screen.blit(text3, (10, 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()