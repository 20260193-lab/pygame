import pygame
import random
import sys
from pygame.math import Vector2

import base64, io

def load_base64_image(b64_string):
    image_data = base64.b64decode(b64_string)
    image_file = io.BytesIO(image_data)
    return pygame.image.load(image_file).convert_alpha()

def slice_sheet(sheet, frame_w, frame_h, cols):
    frames = []
    total = (sheet.get_width() // frame_w) * (sheet.get_height() // frame_h)
    
    for i in range(total):
        row, col = divmod(i, cols)
        rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
        frames.append(sheet.subsurface(rect))
    
    return frames

pygame.init()

def get_korean_font(size):
    # 한글 폰트 후보군 (윈도우, 맥, 나눔고딕 등)
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0:
            return font
    return pygame.font.SysFont(None, size)

WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (40, 40, 40)
BLUE, RED, YELLOW = (50, 150, 255), (255, 60, 60), (240, 200, 0)
GREEN = (50, 220, 80)

ARENA_W, ARENA_H = 300, 300
# 전역 변수로 관리하여 클래스들 사이에서 공유
ARENA_RECT = pygame.Rect((WIDTH - ARENA_W) // 2, (HEIGHT - ARENA_H) // 2, ARENA_W, ARENA_H)

SHEET_B64 = "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"

# 1~10라운드의 난이도를 자동으로 계산하여 생성합니다.
LEVELS = [
    {
        "min_speed": 100 + (i * 20),
        "max_speed": 350 + (i * 40),
        "spawn_rate": max(0.08, 0.5 - (i * 0.04)), 
        "target_score": (i + 1) * 100,
        "label": f"Round {i + 1}"
    }
    for i in range(10)
]

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # --- 스프라이트 로드 ---
        sheet = load_base64_image(SHEET_B64)

        frames = slice_sheet(sheet, 32, 32, 4)

        self.animations = {
            "down_idle": [frames[0], frames[1]],
            "down_run": [frames[12], frames[13], frames[14], frames[15]],
    
            "up_idle": [frames[8], frames[9]],
            "up_run": [frames[20], frames[21], frames[22], frames[23]],
    
            "right_idle": [frames[4], frames[5]],
            "right_run": [frames[16], frames[17], frames[18], frames[19]],
        }
        self.direction = "down"
        self.moving = False

        self.image = self.animations["down_idle"][0]
        self.rect = self.image.get_rect(center=ARENA_RECT.center)

        self.pos = Vector2(self.rect.center)
        self.speed = 300

        self.anim_timer = 0
        self.anim_frame = 0
        
        self.current_state = "down_idle"

    def update(self, dt):
        keys = pygame.key.get_pressed()
        move = Vector2(0, 0)

        if keys[pygame.K_LEFT]:
            move.x = -1
            self.direction = "left"
        if keys[pygame.K_RIGHT]:
            move.x = 1
            self.direction = "right"
        if keys[pygame.K_UP]:
            move.y = -1
            self.direction = "up"
        if keys[pygame.K_DOWN]:
            move.y = 1
            self.direction = "down"

        self.moving = move.length() > 0

        if self.moving:
            move = move.normalize()

        self.pos += move * self.speed * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.rect.clamp_ip(ARENA_RECT)
        self.pos = Vector2(self.rect.center)

        self.update_sprite(dt)

    def update_sprite(self, dt):
        state = "run" if self.moving else "idle"

        direction = self.direction
        flip = False

        if direction == "left":
            direction = "right"
            flip = True
            
        new_state = f"{direction}_{state}"

        if new_state != self.current_state:
            self.current_state = new_state
            self.anim_frame = 0    

        frames = self.animations[f"{direction}_{state}"]
        
        self.anim_frame %= len(frames)

        # 애니메이션
        self.anim_timer += dt
        if self.anim_timer > 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % len(frames)

        image = frames[self.anim_frame]

        if flip:
            image = pygame.transform.flip(image, True, False)
            
        scale = 2  # 👉 원하는 크기 (1=원본, 2=2배, 3=3배)

        image = pygame.transform.scale(
            image,
            (image.get_width() * scale, image.get_height() * scale)
        )

        self.image = image

class Enemy(pygame.sprite.Sprite):
    def __init__(self, level_cfg):
        super().__init__()
        radius = 6 # 장애물 크기를 작게 통일
        
        # 배경이 투명한 원형 장애물 생성
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (radius, radius), radius)
        
        self.rect = self.image.get_rect()
        
        speed = random.randint(level_cfg["min_speed"], level_cfg["max_speed"])
        
        # 화면 밖 스폰 위치 설정
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":      start_pos = Vector2(random.uniform(0, WIDTH), -50)
        elif side == "bottom": start_pos = Vector2(random.uniform(0, WIDTH), HEIGHT + 50)
        elif side == "left":   start_pos = Vector2(-50, random.uniform(0, HEIGHT))
        else:                  start_pos = Vector2(WIDTH + 50, random.uniform(0, HEIGHT))

        # 줄어든 아레나의 내부 랜덤한 위치를 타겟으로 조준
        target_pos = Vector2(random.uniform(ARENA_RECT.left, ARENA_RECT.right),
                             random.uniform(ARENA_RECT.top, ARENA_RECT.bottom))
        
        direction = (target_pos - start_pos).normalize()
        self.velocity = direction * speed
        self.pos = start_pos
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self, dt):
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # 화면을 벗어나면 삭제
        if not (-100 < self.pos.x < WIDTH + 100 and -100 < self.pos.y < HEIGHT + 100):
            self.kill()

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("R10unds")
        self.clock = pygame.time.Clock()
        self.font = get_korean_font(36)
        self.font_big = get_korean_font(72)
        
        self.state = "START_SCREEN"
        
        self.player = None
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()

    def reset_game(self):
        # 게임 재시작 시 아레나 크기를 원래대로(300x300) 복구합니다.
        ARENA_RECT.size = (300, 300)
        ARENA_RECT.center = (WIDTH // 2, HEIGHT // 2)

        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemies = pygame.sprite.Group()
        self.score = 0
        self.lives = 3
        self.invincible_timer = 0
        self.spawn_timer = 0
        self.score_timer = 0
        self.rest_timer = 0
        self.level_idx = 0
        self.state = "PLAYING"

    def draw_centered_text(self, text, font, color, y_pos):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(WIDTH // 2, y_pos))
        self.screen.blit(surface, rect)

    def draw_hud(self):
        level_cfg = LEVELS[self.level_idx]
        
        self.screen.blit(self.font.render(f"Score: {self.score}", True, WHITE), (10, 10))
        self.screen.blit(self.font.render(level_cfg['label'], True, YELLOW), (10, 40))
        
        # 하트 텍스트가 줄어드는 박스를 따라오게 할 수도 있지만, 
        # 안정적인 레이아웃을 위해 화면 우측 상단 고정으로 약간 수정했습니다.
        lives_surface = self.font.render(f"Lives: {'♥ ' * self.lives}", True, RED)
        self.screen.blit(lives_surface, (WIDTH - lives_surface.get_width() - 20, 10))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if self.state == "START_SCREEN":
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        self.reset_game()
                
                elif self.state in ["GAME_OVER", "GAME_CLEAR"]:
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_r: 
                            self.reset_game()
                        if e.key == pygame.K_q: 
                            pygame.quit(); sys.exit()

            # --- PLAYING 상태 ---
            if self.state == "PLAYING":
                level_cfg = LEVELS[self.level_idx]
                self.all_sprites.update(dt)
                
                self.spawn_timer += dt
                if self.spawn_timer >= level_cfg["spawn_rate"]:
                    self.spawn_timer = 0
                    enemy = Enemy(level_cfg)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)

                self.score_timer += dt
                if self.score_timer >= 1.0:
                    self.score += 10
                    self.score_timer = 0
                    
                    if self.score >= level_cfg["target_score"]:
                        if self.level_idx == len(LEVELS) - 1:
                            self.state = "GAME_CLEAR"
                            for enemy in self.enemies:
                                enemy.kill()
                        else:
                            self.state = "RESTING"
                            self.rest_timer = 5.0
                            for enemy in self.enemies:
                                enemy.kill()

                if self.invincible_timer > 0:
                    self.invincible_timer -= dt
                else:
                    if pygame.sprite.spritecollide(self.player, self.enemies, False):
                        self.lives -= 1
                        self.invincible_timer = 1.5
                        for enemy in self.enemies:
                            enemy.kill()
                        
                        if self.lives <= 0:
                            self.state = "GAME_OVER"

            # --- RESTING (휴식) 상태 ---
            elif self.state == "RESTING":
                if self.player:
                    self.player.update(dt)
                self.rest_timer -= dt
                
                if self.rest_timer <= 0:
                    self.level_idx += 1
                    self.state = "PLAYING"
                    
                    # ⭐ 라운드가 올라갈 때마다 아레나 크기를 가로, 세로 20픽셀씩 줄입니다.
                    ARENA_RECT.inflate_ip(-20, -20)

            # --- 화면 렌더링 파트 ---
            self.screen.fill(BLACK)
            
            if self.state == "START_SCREEN":
                self.draw_centered_text("R10unds", self.font_big, WHITE, 220)
                self.draw_centered_text("Click anywhere to START", self.font, YELLOW, 310)

            elif self.state in ["PLAYING", "RESTING"]:
                # 줄어드는 아레나를 화면에 그립니다.
                pygame.draw.rect(self.screen, WHITE, ARENA_RECT, 4)

                blink = int(self.invincible_timer * 10) % 2 == 0
                for sprite in self.all_sprites:
                    if sprite == self.player and not blink and self.invincible_timer > 0:
                        continue
                    self.screen.blit(sprite.image, sprite.rect)

                self.draw_hud()

                if self.state == "RESTING":
                    self.draw_centered_text("ROUND CLEARED!", self.font_big, GREEN, 220)
                    self.draw_centered_text(f"Next Round in {int(self.rest_timer) + 1}...", self.font, YELLOW, 310)

            elif self.state == "GAME_OVER":
                self.draw_centered_text("GAME OVER", self.font_big, RED, 220)
                self.draw_centered_text(f"Final Score: {self.score}", self.font, WHITE, 310)
                self.draw_centered_text("R: Restart   Q: Quit", self.font, WHITE, 360)

            elif self.state == "GAME_CLEAR":
                self.draw_centered_text("YOU SURVIVED!", self.font_big, YELLOW, 220)
                self.draw_centered_text("ALL 10 ROUNDS CLEARED", self.font, WHITE, 310)
                self.draw_centered_text("R: Restart   Q: Quit", self.font, WHITE, 360)

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()