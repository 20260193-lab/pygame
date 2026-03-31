import pygame
import random
import sys
from pygame.math import Vector2

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

# 1~10라운드의 난이도를 자동으로 계산하여 생성합니다.
LEVELS = [
    {
        "min_speed": 150 + (i * 20),
        "max_speed": 250 + (i * 30),
        "spawn_rate": max(0.08, 0.5 - (i * 0.04)), 
        "target_score": (i + 1) * 100,
        "label": f"Round {i + 1}"
    }
    for i in range(10)
]

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=ARENA_RECT.center)
        self.pos = Vector2(self.rect.center)
        self.speed = 300 

    def update(self, dt):
        keys = pygame.key.get_pressed()
        move = Vector2(0, 0)
        
        if keys[pygame.K_LEFT]:  move.x = -1
        if keys[pygame.K_RIGHT]: move.x = 1
        if keys[pygame.K_UP]:    move.y = -1
        if keys[pygame.K_DOWN]:  move.y = 1

        if move.length() > 0:
            move = move.normalize()
            
        self.pos += move * self.speed * dt
        
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        # 줄어든 아레나 크기에 맞춰서 플레이어가 밖으로 나가지 못하게 제한
        self.rect.clamp_ip(ARENA_RECT)
        self.pos = Vector2(self.rect.center)

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