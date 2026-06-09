import pygame
import sys
import os

pygame.init()

# --------------------------------
# 화면 설정
# --------------------------------
WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D 횡스크롤 - 콤보 공격 속도 가속 시스템")

clock = pygame.time.Clock()
GROUND_Y = 500

# --------------------------------
# 경로 함수
# --------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --------------------------------
# 플레이어 캐릭터 애니메이션 로드
# --------------------------------
def load_sprite_sheet(path, frame_width, frame_height, scale=1):
    try:
        sheet = pygame.image.load(resource_path(path)).convert_alpha()
    except pygame.error:
        sheet = pygame.Surface((frame_width * 4, frame_height), pygame.SRCALPHA)
        sheet.fill((200, 50, 50, 150))
    frames = []
    for x in range(0, sheet.get_width(), frame_width):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (x, 0, frame_width, frame_height))
        scaled_frame = pygame.transform.scale(
            frame, (int(frame_width * scale), int(frame_height * scale))
        )
        frames.append(scaled_frame)
    return frames

animations = {
    "idle": load_sprite_sheet("sprites/Player/_Idle.png", 120, 80, scale=2.5),
    "run": load_sprite_sheet("sprites/Player/_Run.png", 120, 80, scale=2.5),
    "jump": load_sprite_sheet("sprites/Player/_Jump.png", 120, 80, scale=2.5),
    "fall": load_sprite_sheet("sprites/Player/_Fall.png", 120, 80, scale=2.5),
    "crouch": load_sprite_sheet("sprites/Player/_Crouch.png", 120, 80, scale=2.5),
    
    "attack1": load_sprite_sheet("sprites/Player/_Attack.png", 120, 80, scale=2.5),
    "attack2": load_sprite_sheet("sprites/Player/_Attack2.png", 120, 80, scale=2.5),
    "attack1_no_move": load_sprite_sheet("sprites/Player/_AttackNoMovement.png", 120, 80, scale=2.5),
    "attack2_no_move": load_sprite_sheet("sprites/Player/_Attack2NoMovement.png", 120, 80, scale=2.5),
    "attack_combo": load_sprite_sheet("sprites/Player/_AttackCombo.png", 120, 80, scale=2.5),
    "attack_combo_no_move": load_sprite_sheet("sprites/Player/_AttackComboNoMovement.png", 120, 80, scale=2.5),
}

# 기본 속도 정의
state_data = {
    "idle": {"speed": 0, "animation_speed": 0.2},
    "run": {"speed": 5, "animation_speed": 0.3},
    "crouch": {"speed": 2, "animation_speed": 0.05},
    "jump": {"speed": 5, "animation_speed": 0.2},
    "fall": {"speed": 5, "animation_speed": 0.2},
    
    "attack1": {"speed": 0, "animation_speed": 0.23},
    "attack2": {"speed": 0, "animation_speed": 0.23},
    "attack1_no_move": {"speed": 0, "animation_speed": 0.23},
    "attack2_no_move": {"speed": 0, "animation_speed": 0.23},
    "attack_combo": {"speed": 0, "animation_speed": 0.25},       # 콤보 기본 속도
    "attack_combo_no_move": {"speed": 0, "animation_speed": 0.25},
}

# --------------------------------
# 가상의 적 클래스
# --------------------------------
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y - 100, 60, 100)
    def draw(self, screen):
        pygame.draw.rect(screen, (200, 50, 50), self.rect)

# --------------------------------
# 플레이어 클래스
# --------------------------------
class Player:
    def __init__(self):
        self.x = 300
        self.y = GROUND_Y
        self.facing_right = True
        self.current_state = "idle"
        self.frame_index = 0

        # 물리 변수
        self.y_velocity = 0
        self.gravity = 0.6
        self.jump_power = -12
        self.is_grounded = True

        # 공격 및 콤보 변수
        self.attack_count = 0        
        self.hit_count = 0           
        self.combo_timer = 0         
        
        # 다단히트 제어용 플래그
        self.has_hit_first = False   
        self.has_hit_second = False  
        self.has_hit_normal = False  

        # 플레이어 스탯
        self.max_hp = 100
        self.current_hp = 100
        
        # 보스 체력 변수
        self.boss_max_hp = 100
        self.boss_current_hp = 100

        # UI 연출용 타이머
        self.pulse_timer = 0

    def change_state(self, new_state):
        if self.current_state != new_state:
            self.current_state = new_state
            self.frame_index = 0
            if "attack" in new_state:
                self.has_hit_first = False
                self.has_hit_second = False
                self.has_hit_normal = False

    def is_attacking(self):
        return "attack" in self.current_state

    def update(self, keys, dt, enemies):
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_timer = 0

        self.pulse_timer += 0.1

        current_speed = state_data[self.current_state]["speed"]

        if keys[pygame.K_LEFT]:
            self.x -= current_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.x += current_speed
            self.facing_right = True

        if not self.is_grounded:
            self.y += self.y_velocity
            self.y_velocity += self.gravity
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.y_velocity = 0
                self.is_grounded = True

        if not self.is_attacking():
            if not self.is_grounded:
                if self.y_velocity < 0:
                    self.change_state("jump")
                else:
                    self.change_state("fall")
            else:
                moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
                if keys[pygame.K_DOWN]:
                    self.change_state("crouch")
                elif moving:
                    self.change_state("run")
                else:
                    self.change_state("idle")

        # --- 애니메이션 프레임 진행 및 공속 가속 핸들링 ---
        current_frames = animations[self.current_state]
        base_anim_speed = state_data[self.current_state]["animation_speed"]
        
        # 🌟 콤보 버프 상태(combo_timer > 0)일 때 공격 속도를 1.6배 가속시킵니다.
        if self.combo_timer > 0 and self.is_attacking():
            final_anim_speed = base_anim_speed * 1.6
        else:
            final_anim_speed = base_anim_speed

        self.frame_index += final_anim_speed

        # 공격 종류별 정밀 타격 판정 로직
        if self.is_attacking():
            current_frame_int = int(self.frame_index)
            total_frames = len(current_frames)

            if "combo" in self.current_state:
                # 콤보 다단히트 프레임 타이밍 계산
                first_hit_frame = total_frames // 4
                second_hit_frame = int(total_frames * 0.7)

                # 1타 판정 체크
                if current_frame_int == first_hit_frame and not self.has_hit_first:
                    self.has_hit_first = True
                    self.check_attack_collision(enemies, is_combo_hit=True)

                # 2타 판정 체크
                if current_frame_int == second_hit_frame and not self.has_hit_second:
                    self.has_hit_second = True
                    self.check_attack_collision(enemies, is_combo_hit=True)
            else:
                # 일반 공격 분기 (중간 프레임)
                normal_hit_frame = total_frames // 2
                if current_frame_int == normal_hit_frame and not self.has_hit_normal:
                    self.has_hit_normal = True
                    self.check_attack_collision(enemies, is_combo_hit=False)

        # 애니메이션 종료 처리
        if self.frame_index >= len(current_frames):
            self.frame_index = 0
            if self.is_attacking():
                self.attack_count = 1 - self.attack_count 
                self.change_state("idle")

    def handle_attack_input(self, keys):
        if self.is_attacking() or not self.is_grounded:
            return 

        is_moving_input = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
        is_combo_active = self.combo_timer > 0

        if is_combo_active:
            if is_moving_input:
                self.change_state("attack_combo")
            else:
                self.change_state("attack_combo_no_move")
        else:
            if self.attack_count == 0:  
                if is_moving_input:
                    self.change_state("attack1")
                else:
                    self.change_state("attack1_no_move")
            else:                       
                if is_moving_input:
                    self.change_state("attack2")
                else:
                    self.change_state("attack2_no_move")

    def check_attack_collision(self, enemies, is_combo_hit):
        hitbox_width = 100
        hitbox_height = 80
        hitbox_x = self.x if self.facing_right else self.x - hitbox_width
        hitbox_y = self.y - hitbox_height

        attack_rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)

        for enemy in enemies:
            if attack_rect.colliderect(enemy.rect):
                # 오직 적(보스)의 HP만 감소 (플레이어 피격 버그 수정 반영 유지)
                self.boss_current_hp = max(0, self.boss_current_hp - 10)
                
                # 콤보 활성화 스택 누적 로직 (버프 오프 상태일 때만 축적)
                if not is_combo_hit and self.combo_timer <= 0:
                    self.hit_count += 1
                    if self.hit_count >= 5:
                        self.combo_timer = 3000  
                        self.hit_count = 0
                break

    def draw(self, screen):
        current_frames = animations[self.current_state]
        idx = min(int(self.frame_index), len(current_frames) - 1)
        current_image = current_frames[idx]

        if not self.facing_right:
            current_image = pygame.transform.flip(current_image, True, False)

        image_rect = current_image.get_rect(midbottom=(int(self.x), int(self.y)))
        screen.blit(current_image, image_rect)

    # ----------------------------
    # UI 그리기 함수
    # ----------------------------
    def draw_vector_ui(self, screen):
        start_x = 20
        start_y = 20
        bar_width = 220
        bar_height = 14

        bg_panel = pygame.Surface((250, 65), pygame.SRCALPHA)
        bg_panel.fill((0, 0, 0, 140))
        screen.blit(bg_panel, (start_x - 5, start_y - 5))

        # --- [1] 플레이어 HP 바 ---
        hp_ratio = self.current_hp / self.max_hp
        if hp_ratio > 0.7:
            hp_color = (46, 204, 113)  
        elif hp_ratio > 0.4:
            hp_color = (230, 126, 34)  
        else:
            hp_color = (231, 76, 60) if int(self.pulse_timer) % 2 == 0 else (150, 25, 25)

        pygame.draw.rect(screen, (40, 40, 40), (start_x, start_y, bar_width, bar_height))
        if hp_ratio > 0:
            pygame.draw.rect(screen, hp_color, (start_x, start_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(screen, (200, 200, 200), (start_x, start_y, bar_width, bar_height), 1)

        # --- [2] 플레이어 MP 바 ---
        if self.combo_timer > 0:
            mp_color = (254, 211, 48) if int(self.pulse_timer * 2) % 2 == 0 else (241, 196, 15)
            mp_ratio = self.combo_timer / 3000
        else:
            mp_color = (52, 152, 219)  
            mp_ratio = self.hit_count / 5

        mp_y = start_y + bar_height + 8
        pygame.draw.rect(screen, (40, 40, 40), (start_x, mp_y, bar_width, bar_height - 2))
        if mp_ratio > 0:
            pygame.draw.rect(screen, mp_color, (start_x, mp_y, int(bar_width * mp_ratio), bar_height - 2))
        pygame.draw.rect(screen, (180, 180, 180), (start_x, mp_y, bar_width, bar_height - 2), 1)


        # --- [3] 보스 체력 바 (중앙 하단 유지) ---
        boss_bar_w = 500              
        boss_bar_h = 14
        boss_x = (WIDTH // 2) - (boss_bar_w // 2)
        boss_y = HEIGHT - 40          

        boss_ratio = self.boss_current_hp / self.boss_max_hp
        
        boss_panel = pygame.Surface((boss_bar_w + 20, boss_bar_h + 10), pygame.SRCALPHA)
        boss_panel.fill((0, 0, 0, 160)) 
        screen.blit(boss_panel, (boss_x - 10, boss_y - 5))

        pygame.draw.rect(screen, (30, 30, 30), (boss_x, boss_y, boss_bar_w, boss_bar_h))
        if boss_ratio > 0:
            pygame.draw.rect(screen, (39, 174, 96), (boss_x, boss_y, int(boss_bar_w * boss_ratio), boss_bar_h))
        pygame.draw.rect(screen, (241, 196, 15), (boss_x, boss_y, boss_bar_w, boss_bar_h), 1) 


# --------------------------------
# 메인 루프 실행부
# --------------------------------
player = Player()
enemies = [Enemy(700, GROUND_Y)]

while True:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x:  
                player.handle_attack_input(pygame.key.get_pressed())
            if event.key == pygame.K_SPACE and player.is_grounded:
                player.y_velocity = player.jump_power
                player.is_grounded = False
                player.change_state("jump")

    keys = pygame.key.get_pressed()
    player.update(keys, dt, enemies)

    screen.fill((30, 30, 30))

    # 바닥
    pygame.draw.rect(screen, (70, 120, 70), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    for enemy in enemies:
        enemy.draw(screen)
    player.draw(screen)

    # UI 드로잉 호출
    player.draw_vector_ui(screen)

    pygame.display.flip()