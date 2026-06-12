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
# 배경 및 바닥 이미지 로드 함수
# --------------------------------
# --------------------------------
# 배경(패럴랙스 8레이어) 및 바닥 이미지 로드 함수
# --------------------------------
def load_environment_images():
    bg_layers = []
    
    # 1부터 8까지의 배경 레이어 로드
    for i in range(1, 9):
        path = resource_path(f"sprites/Backgrounds/{i}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            # 화면 크기에 맞게 스케일링 (가로 폭은 무한 스크롤을 위해 화면 크기로 맞춤)
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            bg_layers.append(img)
        except pygame.error:
            # 이미지 파일이 없을 경우 레이어 구분을 위해 임시로 투명도가 있는 색상 Surface 생성
            dummy = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # 숫자가 커질수록 조금씩 다른 색상과 알파값 부여
            alpha = 30 + (i * 20)
            color = (20 + i * 15, 30 + i * 10, 50 + i * 5, alpha)
            dummy.fill(color)
            bg_layers.append(dummy)
            
    # 바닥 타일 이미지 로드
    try:
        tile_img = pygame.image.load(resource_path("sprites/Background/tile.png")).convert_alpha()
        tile_img = pygame.transform.scale(tile_img, (64, 64))
    except pygame.error:
        tile_img = pygame.Surface((64, 64), pygame.SRCALPHA)
        tile_img.fill((50, 100, 50))
        pygame.draw.rect(tile_img, (70, 130, 70), (0, 0, 64, 64), 2)
        pygame.draw.rect(tile_img, (40, 80, 40), (0, 0, 64, 8))

    return bg_layers, tile_img

# 함수 호출하여 8개의 레이어 리스트와 타일 가져오기
bg_layers, tile_image = load_environment_images()

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
    "attack_combo": {"speed": 0, "animation_speed": 0.25},       
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

        # 화면 밖으로 나가지 않도록 맵 경계 제한 (시차 스크롤 연산 안정성을 위해 추가)
        self.x = max(50, min(self.x, WIDTH - 50))

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

        current_frames = animations[self.current_state]
        base_anim_speed = state_data[self.current_state]["animation_speed"]
        
        if self.combo_timer > 0 and self.is_attacking():
            final_anim_speed = base_anim_speed * 1.6
        else:
            final_anim_speed = base_anim_speed

        self.frame_index += final_anim_speed

        if self.is_attacking():
            current_frame_int = int(self.frame_index)
            total_frames = len(current_frames)

            if "combo" in self.current_state:
                first_hit_frame = total_frames // 4
                second_hit_frame = int(total_frames * 0.7)

                if current_frame_int == first_hit_frame and not self.has_hit_first:
                    self.has_hit_first = True
                    self.check_attack_collision(enemies, is_combo_hit=True)

                if current_frame_int == second_hit_frame and not self.has_hit_second:
                    self.has_hit_second = True
                    self.check_attack_collision(enemies, is_combo_hit=True)
            else:
                normal_hit_frame = total_frames // 2
                if current_frame_int == normal_hit_frame and not self.has_hit_normal:
                    self.has_hit_normal = True
                    self.check_attack_collision(enemies, is_combo_hit=False)

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
                self.boss_current_hp = max(0, self.boss_current_hp - 10)
                
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
    # 고급형 입체 UI 그리기 함수 (이미지 스타일 구현)
    # ----------------------------
    def draw_vector_ui(self, screen):
        # 전체 UI 기준 위치
        start_x = 30
        start_y = 25
        
        # 오른쪽 바 패널 크기
        panel_w = 260
        panel_h = 56
        panel_x = start_x + 40  # 원형 초상화와 겹치도록 약간 오른쪽에서 시작
        panel_y = start_y + 8
        
        # --- [1] 우측 어두운 배경 패널 그리기 ---
        # 외부 어두운 테두리
        pygame.draw.rect(screen, (35, 25, 22), (panel_x, panel_y, panel_w, panel_h))
        # 내부 살짝 밝은 메탈릭 배경
        pygame.draw.rect(screen, (45, 38, 35), (panel_x + 2, panel_y + 2, panel_w - 4, panel_h - 4))
        # 중앙 안쪽 음영 영역 (바들이 들어갈 공간)
        pygame.draw.rect(screen, (24, 18, 15), (panel_x + 6, panel_y + 18, panel_w - 12, panel_h - 22))
        
        # --- [2] 텍스트 그리기 (HERO) ---
        # 폰트가 없으면 기본 시스템 폰트 사용 (크기 작게 상단 중앙 배치)
        font = pygame.font.SysFont("arial", 12, bold=True)
        text_surf = font.render("HERO", True, (168, 147, 126)) # 은은한 베이지/골드 톤
        screen.blit(text_surf, (panel_x + 12, panel_y + 4))

        # --- [3] 게이지 바 공통 설정 ---
        bar_x = panel_x + 10
        bar_w = panel_w - 20
        bar_h = 10
        
        # --- [4] HP 바 그리기 (상단 바) ---
        hp_y = panel_y + 22
        hp_ratio = self.current_hp / self.max_hp
        
        # HP 바 배경 (어두운 홈)
        pygame.draw.rect(screen, (40, 15, 15), (bar_x, hp_y, bar_w, bar_h))
        if hp_ratio > 0:
            fill_w = int(bar_w * hp_ratio)
            # HP 주 메인 색상 (중앙)
            pygame.draw.rect(screen, (185, 35, 15), (bar_x, hp_y, fill_w, bar_h))
            # 입체감을 위한 상단 하이라이트 선 (밝은 빨강)
            pygame.draw.rect(screen, (235, 75, 55), (bar_x, hp_y, fill_w, 2))
            # 입체감을 위한 하단 섀도우 선 (어두운 빨강)
            pygame.draw.rect(screen, (120, 15, 5), (bar_x, hp_y + bar_h - 2, fill_w, 2))
        # 바 자체 테두리
        pygame.draw.rect(screen, (70, 55, 45), (bar_x, hp_y, bar_w, bar_h), 1)

        # --- [5] 콤보 바 그리기 (하단 바) ---
        combo_y = panel_y + 36
        if self.combo_timer > 0:
            # 콤보 버프 중일 때는 번쩍이는 금색 효과
            c_color = (220, 140, 20) if int(self.pulse_timer * 2) % 2 == 0 else (190, 110, 10)
            c_hi = (255, 200, 70)
            c_sh = (130, 70, 5)
            mp_ratio = self.combo_timer / 3000
        else:
            # 평소 스택 쌓일 때는 주황/적갈색 느낌
            c_color = (180, 90, 20)
            c_hi = (220, 130, 40)
            c_sh = (110, 50, 10)
            mp_ratio = self.hit_count / 5

        # 콤보 바 배경 (어두운 홈)
        pygame.draw.rect(screen, (35, 20, 10), (bar_x, combo_y, bar_w, bar_h))
        if mp_ratio > 0:
            fill_w = int(bar_w * mp_ratio)
            # 콤보 바 메인 채우기
            pygame.draw.rect(screen, c_color, (bar_x, combo_y, fill_w, bar_h))
            # 상단 하이라이트
            pygame.draw.rect(screen, c_hi, (bar_x, combo_y, fill_w, 2))
            # 하단 섀도우
            pygame.draw.rect(screen, c_sh, (bar_x, combo_y + bar_h - 2, fill_w, 2))
        # 바 자체 테두리
        pygame.draw.rect(screen, (70, 55, 45), (bar_x, combo_y, bar_w, bar_h), 1)

        # --- [6] 왼쪽 원형 초상화 프레임 그리기 ---
        circle_x = start_x + 32
        circle_y = start_y + 32
        radius = 32
        
        # 1. 외곽 테두리 (입체적인 금속 링 표현을 위해 크기별로 레이어링)
        pygame.draw.circle(screen, (35, 28, 24), (circle_x, circle_y), radius)      # 바깥 어두운 선
        pygame.draw.circle(screen, (115, 98, 83), (circle_x, circle_y), radius - 1)  # 메인 금속 프레임
        pygame.draw.circle(screen, (150, 132, 115), (circle_x, circle_y), radius - 3, 1) # 안쪽 밝은 하이라이트 링
        pygame.draw.circle(screen, (24, 18, 15), (circle_x, circle_y), radius - 4)  # 내부 어두운 배경 영역
        
        # 2. 내부 캐릭터 실루엣 (실제 드로잉으로 이미지 느낌 흉내내기)
        # 나중에 여기에 플레이어 얼굴 이미지를 자르거나 넣을 수 있습니다. 우선 실루엣 배치:
        inner_center = (circle_x, circle_y)
        # 머리
        pygame.draw.circle(screen, (55, 45, 40), (circle_x, circle_y - 6), 11)
        # 어깨 및 몸통
        pygame.draw.ellipse(screen, (55, 45, 40), (circle_x - 18, circle_y + 4, 36, 26))
        
        # 3. 이미지처럼 프레임 가장 안쪽에 얇은 음영 링 한 번 더 추가
        pygame.draw.circle(screen, (70, 55, 45), (circle_x, circle_y), radius - 4, 1)


        # --- [7] 보스 체력 바 (스타일 통일을 위해 함께 메탈릭하게 수정) ---
        boss_bar_w = 500              
        boss_bar_h = 16
        boss_x = (WIDTH // 2) - (boss_bar_w // 2)
        boss_y = HEIGHT - 45          
        boss_ratio = self.boss_current_hp / self.boss_max_hp
        
        # 보스 패널 테두리 및 배경
        pygame.draw.rect(screen, (35, 25, 22), (boss_x - 4, boss_y - 4, boss_bar_w + 8, boss_bar_h + 8))
        pygame.draw.rect(screen, (45, 38, 35), (boss_x - 2, boss_y - 2, boss_bar_w + 4, boss_bar_h + 4))
        pygame.draw.rect(screen, (24, 18, 15), (boss_x, boss_y, boss_bar_w, boss_bar_h))
        
        if boss_ratio > 0:
            b_fill = int(boss_bar_w * boss_ratio)
            pygame.draw.rect(screen, (140, 25, 25), (boss_x, boss_y, b_fill, boss_bar_h))
            pygame.draw.rect(screen, (200, 50, 50), (boss_x, boss_y, b_fill, 3)) # 보스 하이라이트
            pygame.draw.rect(screen, (80, 10, 10), (boss_x, boss_y + boss_bar_h - 3, b_fill, 3))
        pygame.draw.rect(screen, (85, 70, 60), (boss_x, boss_y, boss_bar_w, boss_bar_h), 1)

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

    # --------------------------------
    # 렌더링 시작
    # --------------------------------
    # 검은색 기본 바탕 (혹시 모를 여백 대비)
    screen.fill((10, 10, 12))

    # 8개의 레이어를 패럴랙스 효과를 적용하여 순서대로 그리기
    for idx, layer in enumerate(bg_layers):
        layer_num = idx + 1  # 1부터 8까지의 레이어 번호
        
        # 🌟 시차 스크롤 핵심 연산
        # 1번 레이어는 0.03 (거의 안 움직임) -> 8번 레이어는 0.45 (많이 움직임)
        # 플레이어 진행 방향 반대로 배경이 밀리도록 마이너스(-) 처리
        speed_factor = 0.01 + (layer_num * 0.05)
        parallax_offset = -int(player.x * speed_factor) % WIDTH
        
        # 무한 반복 스크롤을 위해 두 번 겹쳐서 그리기
        screen.blit(layer, (parallax_offset - WIDTH, 0))
        screen.blit(layer, (parallax_offset, 0))

    # 2. 바닥 타일 그리기 (기존과 동일하게 유지되는 그리드 반복 배치)
    tile_w = tile_image.get_width()
    tile_h = tile_image.get_height()
    for target_y in range(GROUND_Y, HEIGHT, tile_h):
        for target_x in range(0, WIDTH + tile_w, tile_w):
            screen.blit(tile_image, (target_x, target_y))

    # 3. 오브젝트 및 UI 그리기
    for enemy in enemies:
        enemy.draw(screen)
    player.draw(screen)
    player.draw_vector_ui(screen)

    pygame.display.flip()