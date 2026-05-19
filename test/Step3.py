import base64, io
import pygame

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  스프라이트 시트 Base64 데이터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHEET_B64 = "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"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCREEN_W, SCREEN_H = 480, 320
FRAME_W, FRAME_H   = 80, 64
COLS               = 9
FRAME_DELAY        = 150   # ms
DISPLAY_SCALE      = 4     # 화면 확대 배율

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Sprite Animation Demo")
clock = pygame.time.Clock()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  시트 로드 → 프레임 리스트
#  인덱스 0 ~ 8 (총 9개)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sheet_bytes = base64.b64decode(SHEET_B64)
player_sheet = pygame.image.load(io.BytesIO(sheet_bytes)).convert_alpha()

player_frames = []
for i in range(9):
    row, col = divmod(i, COLS)
    rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
    player_frames.append(player_sheet.subsurface(rect))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  walk_frames: 선택한 프레임 순서
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
walk_frames = [player_frames[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8]]

frame_index = 0
frame_timer = 0
x = SCREEN_W // 2 - (FRAME_W * DISPLAY_SCALE) // 2
y = SCREEN_H // 2 - (FRAME_H * DISPLAY_SCALE) // 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  게임 루프
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    frame_timer += dt
    if frame_timer >= FRAME_DELAY:
        frame_index = (frame_index + 1) % len(walk_frames)
        frame_timer = 0

    screen.fill((30, 30, 40))
    frame_img = pygame.transform.scale(
        walk_frames[frame_index],
        (FRAME_W * DISPLAY_SCALE, FRAME_H * DISPLAY_SCALE)
    )
    screen.blit(frame_img, (x, y))
    pygame.display.flip()

pygame.quit()