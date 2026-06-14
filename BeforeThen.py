import pygame
import sys
import os
import random
import math

pygame.init()

# --------------------------------
# 화면 설정
# --------------------------------
WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D 횡스크롤 - BeforeThen")

clock = pygame.time.Clock()
GROUND_Y = 500

# 씬 상태 관리 변수 ("TITLE", "RULES", "LOADING", "GAME")
current_scene = "TITLE"
# 게임 세부 스테이지 관리 변수 ("PRACTICE", "BOSS")
game_stage = "PRACTICE"
# 컷씬 단계 및 타이머 제어 변수
cutscene_stage = 0      
cutscene_timer = 0      
cutscene_player_x = 0   

# 흑마법사(스프라이트) 관련 변수
black_mage_img = None
black_mage_state = "idle"  
black_mage_alpha = 255     

# 보스전 진입 시 플레이어의 크기만 줄이는 배율 변수
player_scale_factor = 1.0       
target_player_scale = 1.0

boss_animations = {}
boss_current_state = "teleport_in"  
boss_frame_index = 0
boss_spawn_x = WIDTH // 2           
boss_x = boss_spawn_x               
boss_y = 260                        
loading_timer = 0
glitch_trigger = False


# --------------------------------
# 경로 함수
# --------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_current_ground_y():
    return GROUND_Y

# --------------------------------
# 🌟 [사운드 설정 위치를 여기로 이동!]
# --------------------------------
pygame.mixer.init()

try:
    sound_sword = pygame.mixer.Sound(resource_path("sounds/sword.mp3"))
    sound_jumping = pygame.mixer.Sound(resource_path("sounds/jumping.mp3"))
    
    # 볼륨 설정
    sound_sword.set_volume(0.2)
    sound_jumping.set_volume(0.8)
except Exception as e:
    print(f"SFX 로드 실패: {e}")
    sound_sword = None
    sound_jumping = None

current_bgm = None

def play_bgm(filename):
    global current_bgm
    if current_bgm == filename:
        return
    try:
        pygame.mixer.music.load(resource_path(f"sounds/{filename}"))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
        current_bgm = filename
    except Exception as e:
        print(f"BGM 로드 실패 ({filename}): {e}")

is_paused = False
pause_selected_idx = 0

boss_death_trigger = False
boss_death_timer = 0

# --------------------------------
# 배경 및 바닥, 타이틀 리소스 로드 함수
# --------------------------------
def load_environment_images():
    bg_layers = []
    for i in range(1, 9):
        path = resource_path(f"sprites/Backgrounds/{i}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            bg_layers.append(img)
        except pygame.error:
            dummy = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = 30 + (i * 20)
            color = (20 + i * 15, 30 + i * 10, 50 + i * 5, alpha)
            dummy.fill(color)
            bg_layers.append(dummy)
            
    tile_list = []
    tile_size = 16
    display_tile_size = 32  

    try:
        sheet = pygame.image.load(resource_path("sprites/Backgrounds/Tiles.png")).convert_alpha()
        for y in range(0, 96, tile_size):
            for x in range(0, 96, tile_size):
                tile_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                tile_surf.blit(sheet, (0, 0), (x, y, tile_size, tile_size))
                scaled_tile = pygame.transform.scale(tile_surf, (display_tile_size, display_tile_size))
                tile_list.append(scaled_tile)
    except pygame.error:
        for i in range(1, 37):
            dummy = pygame.Surface((display_tile_size, display_tile_size), pygame.SRCALPHA)
            if i <= 18:
                dummy.fill((55, 50, 75)) 
                pygame.draw.line(dummy, (130, 120, 180), (0, 0), (display_tile_size, 0), 3) 
            else:
                dummy.fill((30, 25, 45)) 
            tile_list.append(dummy)

    try:
        title_img = pygame.image.load(resource_path("sprites/Title.png")).convert_alpha()
        title_img = pygame.transform.scale(title_img, (WIDTH, HEIGHT))
    except pygame.error:
        title_img = pygame.Surface((WIDTH, HEIGHT))
        title_img.fill((15, 12, 22))
        for r in range(HEIGHT):
            color_val = max(0, min(255, 15 + r // 4))
            pygame.draw.line(title_img, (color_val, color_val // 2, color_val + 20), (0, r), (WIDTH, r))

    try:
        boss_bg_actual_image = pygame.image.load(resource_path("sprites/Backgrounds/Back.png")).convert()
        boss_bg_actual_image = pygame.transform.scale(boss_bg_actual_image, (WIDTH, HEIGHT))
    except Exception as e:
        boss_bg_actual_image = pygame.Surface((WIDTH, HEIGHT))
        boss_bg_actual_image.fill((30, 10, 50))

    boss_fire_frames = []
    try:
        fire_sheet = pygame.image.load(resource_path("sprites/Boss/Fire.png")).convert_alpha()
        sheet_w = fire_sheet.get_width()
        for fx in range(0, sheet_w, 64):
            frame_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            frame_surf.fill((0, 0, 0, 0))
            frame_surf.blit(fire_sheet, (0, 0), (fx, 0, 64, 64))
            boss_fire_frames.append(frame_surf)
    except:
        fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
        fallback.fill((255, 50, 0, 150))
        boss_fire_frames = [fallback]

    # 🌟 [3등분 개편]: 300x64 크기의 arm.png를 100px 단위로 정밀 컷팅
    boss_arm_parts = []
    try:
        arm_sheet = pygame.image.load(resource_path("sprites/Boss/arm.png")).convert_alpha()
        p1 = pygame.Surface((100, 64), pygame.SRCALPHA)
        p1.blit(arm_sheet, (0, 0), (0, 0, 100, 64))     # [0] 팔뚝 (늘어날 부위)
        p2 = pygame.Surface((100, 64), pygame.SRCALPHA)
        p2.blit(arm_sheet, (0, 0), (100, 0, 100, 64))   # [1] 전완 (고정)
        p3 = pygame.Surface((100, 64), pygame.SRCALPHA)
        p3.blit(arm_sheet, (0, 0), (200, 0, 100, 64))   # [2] 손 (고정)
        boss_arm_parts = [p1, p2, p3]
    except:
        d1 = pygame.Surface((100, 64), pygame.SRCALPHA); d1.fill((120, 0, 60, 200))
        d2 = pygame.Surface((100, 64), pygame.SRCALPHA); d2.fill((200, 0, 100, 255))
        d3 = pygame.Surface((100, 64), pygame.SRCALPHA); d3.fill((255, 0, 150, 255))
        boss_arm_parts = [d1, d2, d3]

    return bg_layers, tile_list, display_tile_size, title_img, boss_bg_actual_image, boss_fire_frames, boss_arm_parts

bg_layers, all_tiles, TILE_DISPLAY_SIZE, title_image, boss_bg_actual_image, boss_fire_frames, boss_arm_parts = load_environment_images()

# --------------------------------
# 보스전 전용 발판 클래스
# --------------------------------
boss_platforms = []

class BossPlatform:
    def __init__(self, x, y, width_in_tiles):
        self.width_tiles = max(3, width_in_tiles)
        self.rect = pygame.Rect(x, y, self.width_tiles * TILE_DISPLAY_SIZE, 20)

    def draw(self, screen):
        for i in range(self.width_tiles):
            target_x = self.rect.x + (i * TILE_DISPLAY_SIZE)
            if i == 0:
                screen.blit(all_tiles[0], (target_x, self.rect.y))
            elif i == self.width_tiles - 1:
                screen.blit(all_tiles[5], (target_x, self.rect.y))
            else:
                screen.blit(all_tiles[1], (target_x, self.rect.y))

# --------------------------------
# 보스 기믹 클래스
# --------------------------------
class BossSeekerOrb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 70
        self.speed = 0.75 
        self.is_dead = False
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        self.life_time = 5500       
        self.slow_factor = 0.6      

    def update(self, player, platforms, dt):
        self.life_time -= dt
        if self.life_time <= 0:
            self.is_dead = True
            return "NONE"

        dx = player.x - self.x
        target_y = player.y - 40
        dy = target_y - self.y
        dist = (dx**2 + dy**2)**0.5

        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.rect.center = (int(self.x), int(self.y))

        if player.invincible_timer <= 0:
            player_rect = pygame.Rect(player.x - 15, player.y - 70, 30, 70)
            if player_rect.colliderect(self.rect):
                player.take_damage(5.0) 
                player.movement_speed_modifier = self.slow_factor
                player.slow_debuff_timer = 200 
                return "HIT_TICK"
        return "NONE"

    def draw(self, screen, pulse_timer):
        pulse_r = self.radius + int(math.sin(pulse_timer * 2) * 6)
        pygame.draw.circle(screen, (80, 0, 120), (int(self.x), int(self.y)), pulse_r)
        pygame.draw.circle(screen, (140, 20, 180), (int(self.x), int(self.y)), pulse_r - 8, 2)
        pygame.draw.circle(screen, (10, 5, 15), (int(self.x), int(self.y)), pulse_r - 14)

class BossGroundFire:
    def __init__(self):
        self.warning_time = 1500 
        self.active_time = 2500  
        self.timer = self.warning_time + self.active_time
        self.is_dead = False
        self.rect = pygame.Rect(0, GROUND_Y - 10, WIDTH, HEIGHT - GROUND_Y + 10)
        self.frame_index = 0.0
        self.anim_speed = 0.25 

    def update(self, dt, player):
        self.timer -= dt
        if self.timer <= 0:
            self.is_dead = True
            return

        if self.timer < self.active_time:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(boss_fire_frames):
                self.frame_index = 0.0

            if player.invincible_timer <= 0:
                player_rect = pygame.Rect(player.x - 15, player.y - 70, 30, 70)
                if player_rect.colliderect(self.rect) and player.y >= GROUND_Y:
                    player.take_damage(4.0)

    def draw(self, screen):
        if self.timer > self.active_time:
            if int(self.timer / 100) % 2 == 0:
                warning_surf = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
                warning_surf.fill((230, 30, 30, 85))
                screen.blit(warning_surf, (0, GROUND_Y - 40))
                pygame.draw.line(screen, (255, 50, 50), (0, GROUND_Y - 40), (WIDTH, GROUND_Y - 40), 2)
                pygame.draw.line(screen, (255, 50, 50), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        else:
            current_frame_img = boss_fire_frames[int(self.frame_index)]
            scaled_fire = pygame.transform.scale(current_frame_img, (96, 96))
            for hx in range(-32, WIDTH + 32, 32):
                screen.blit(scaled_fire, (hx, GROUND_Y - 82))

class BossOmnThrustManager:
    def __init__(self):
        self.is_dead = False
        self.total_arms_count = 18
        self.arms_list = []
        for i in range(self.total_arms_count):
            delay = i * 280  
            self.arms_list.append(SingleOmniArm(delay))

    def update(self, dt, player):
        all_done = True
        for arm in self.arms_list:
            arm.update(dt, player)
            if not arm.is_finished:
                all_done = False
        if all_done:
            self.is_dead = True

    def draw(self, screen):
        for arm in self.arms_list:
            arm.draw(screen)


class BossDoppelgangerManager:
    """ 모든 발판 위에서 보라색 도플갱어가 동시에 나타나 일제히 공격하는 패턴 (중복 및 오류 제거 완료) """
    def __init__(self, boss_x, boss_y, player):
        self.is_dead = False
        self.timer = 0
        self.has_fired = False
        self.boss_x = boss_x
        self.boss_y = boss_y
        
        self.copied_actions = list(player.saved_actions)
        if not self.copied_actions:
            self.copied_actions = ["attack1"]
            
        self.target_platforms = list(boss_platforms)

    def update(self, dt, player):
        global boss_current_state, boss_frame_index
        
        # 🌟 오직 자신의 고유 도트 모션인 attack5(분신 소환)만 제어합니다.
        if boss_current_state != "attack5" and not self.has_fired:
            boss_current_state = "attack5"
            boss_frame_index = 0

        self.timer += dt
        
        if self.timer >= 500 and not self.has_fired:
            self.has_fired = True
            
            all_attack_spots = []
            for plat in self.target_platforms:
                all_attack_spots.append((plat.rect.centerx, plat.rect.top))
            all_attack_spots.append((self.boss_x, GROUND_Y))
            
            for spot_x, spot_y in all_attack_spots:
                for action in self.copied_actions:
                    facing = player.x > spot_x
                    new_effect = Effect(spot_x, spot_y, "release", facing, saved_state=action)
                    new_effect.type = "doppel_slash" 
                    new_effect.color_mod = (140, 20, 255, 255) 
                    game_effects.append(new_effect)
                
        if self.timer >= 1600: 
            self.is_dead = True
            if boss_current_state == "attack5":
                boss_current_state = "idle"
                boss_frame_index = 0

    def draw(self, screen):
        if self.timer < 500:
            aura_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (80, 20, 160, 100), (100, 100), 80)
            pygame.draw.circle(aura_surf, (140, 40, 255, 140), (100, 100), 60, 3)
            screen.blit(aura_surf, (self.boss_x - 100, self.boss_y - 100))


class BossLightningManager:
    """ 쿠츠나 라이팅 스타일: 보스 애니메이션 월식(붉은 달) 표식 타이밍에 맞춰 3연속 뇌격을 가하는 최종 기믹 """
    def __init__(self, boss_x, boss_y, player):
        self.is_dead = False
        self.timer = 0
        self.boss_x = boss_x
        self.boss_y = boss_y
        self.num_bolts = 5
        
        self.strike_stage = 0 
        self.stage_timer = 0 
        
        # 🌟 1타, 2타, 3타 벼락의 붉은 네모 장판과 실시간 살아있는 곡선 궤적 완전 분리
        self.paths_1st = self.generate_curved_paths()
        self.paths_2nd = self.generate_curved_paths()
        self.paths_3rd = self.generate_curved_paths()

    def generate_curved_paths(self):
        paths = []
        for _ in range(self.num_bolts):
            sx = random.choice([random.randint(-100, 100), random.randint(900, 1100)])
            sy = random.randint(-80, 0)
            ex = random.randint(100, 900)
            ey = HEIGHT + 100
            
            dx, dy = ex - sx, ey - sy
            dist = math.sqrt(dx**2 + dy**2)
            dir_x, dir_y = dx / dist, dy / dist
            perp_x, perp_y = -dir_y, dir_x
            
            points = [(sx, sy)]
            segments = 25
            for j in range(1, segments):
                t = j / segments
                base_x = sx + dx * t
                base_y = sy + dy * t
                wave = math.sin(t * math.pi * 4 + random.uniform(-1, 1)) * 45
                noise = random.randint(-10, 10)
                displacement = wave + noise
                points.append((base_x + perp_x * displacement, base_y + perp_y * displacement))
                
            points.append((ex, ey))
            paths.append((points, (perp_x, perp_y), dist, sx, sy, ex, ey))
        return paths

    def update(self, dt, player):
        global boss_current_state, boss_frame_index
        
        if boss_current_state != "attack3" and self.strike_stage < 4:
            boss_current_state = "attack3"

        self.timer += dt
        self.stage_timer += dt
        current_frame = int(boss_frame_index)

        # 1차 타격 (6프레임 이상)
        if self.strike_stage == 0 and current_frame >= 6:
            self.strike_stage = 1
            self.stage_timer = 0
            self.trigger_damage(player, self.paths_1st, damage_amount=10)

        # 2차 타격 (12프레임 이상, 월식 정점)
        if self.strike_stage == 1 and current_frame >= 12:
            self.strike_stage = 2
            self.stage_timer = 0
            self.trigger_damage(player, self.paths_2nd, damage_amount=12)

        # 3차 타격 (18프레임 이상, 에너지 대폭발)
        if self.strike_stage == 2 and current_frame >= 18:
            self.strike_stage = 3
            self.stage_timer = 0
            self.trigger_damage(player, self.paths_3rd, damage_amount=14)

        # 애니메이션 종료 시 온전히 복귀
        b_frames = boss_animations.get("attack3", [])
        if b_frames and boss_frame_index >= len(b_frames) - 1.0 and self.strike_stage >= 3:
            self.strike_stage = 4
            self.is_dead = True
            boss_current_state = "idle"
            boss_frame_index = 0
            
        if self.timer >= 3500:
            self.is_dead = True
            boss_current_state = "idle"
            boss_frame_index = 0

    def trigger_damage(self, player, paths, damage_amount):
        if player.invincible_timer <= 0:
            p_rect = pygame.Rect(player.x - 15, player.y - 70, 30, 70)
            for path, _, _, _, _, _, _ in paths:
                for i in range(len(path) - 1):
                    if self.check_line_box_collision(path[i][0], path[i][1], path[i+1][0], path[i+1][1], p_rect):
                        player.take_damage(damage_amount)
                        break

    def check_line_box_collision(self, x1, y1, x2, y2, box):
        cx, cy = box.centerx, box.centery
        line_dx, line_dy = x2 - x1, y2 - y1
        line_len_sq = line_dx**2 + line_dy**2
        if line_len_sq == 0: return False
        u = max(0.0, min(1.0, ((cx - x1) * line_dx + (cy - y1) * line_dy) / line_len_sq))
        return math.hypot(cx - (x1 + u * line_dx), cy - (y1 + u * line_dy)) < 40

    def draw(self, screen):
        if self.strike_stage == 0: self.draw_warning_lines(screen, self.paths_1st)
        elif self.strike_stage == 1 and self.stage_timer < 250: self.draw_lightning_bolt(screen, self.paths_1st)

        if self.strike_stage <= 1: self.draw_warning_lines(screen, self.paths_2nd)
        elif self.strike_stage == 2 and self.stage_timer < 250: self.draw_lightning_bolt(screen, self.paths_2nd)

        if self.strike_stage <= 2: self.draw_warning_lines(screen, self.paths_3rd)
        elif self.strike_stage == 3 and self.stage_timer < 250: self.draw_lightning_bolt(screen, self.paths_3rd)

        if self.strike_stage in [1, 2, 3] and self.stage_timer < 60:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 35))
            screen.blit(flash, (0, 0))

    def draw_warning_lines(self, screen, paths):
        for _, (px, py), _, sx, sy, ex, ey in paths:
            offset_x, offset_y = px * 32, py * 32
            points = [(sx + offset_x, sy + offset_y), (ex + offset_x, ey + offset_y), (ex - offset_x, ey - offset_y), (sx - offset_x, sy - offset_y)]
            warn_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(warn_mask, (240, 20, 20, 45), points)
            screen.blit(warn_mask, (0, 0))
            pygame.draw.line(screen, (255, 40, 40, 90), (sx, sy), (ex, ey), 2)

    def draw_lightning_bolt(self, screen, paths):
        fade_progress = min(1.0, self.stage_timer / 250)
        core_thickness = max(1, int(12 * (1.0 - fade_progress)))
        aura_thickness = max(2, int(32 * (1.0 - fade_progress)))
        alpha = max(0, int(255 * (1.0 - fade_progress)))
        
        if alpha > 0:
            for path, _, _, _, _, _, _ in paths:
                red_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                for i in range(len(path) - 1): pygame.draw.line(red_surf, (255, 15, 60, alpha // 3), path[i], path[i+1], aura_thickness)
                screen.blit(red_surf, (0, 0))
                white_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                for i in range(len(path) - 1): pygame.draw.line(white_surf, (255, 255, 255, alpha), path[i], path[i+1], core_thickness)
                screen.blit(white_surf, (0, 0))

                
class SingleOmniArm:
    def __init__(self, delay):
        self.delay = delay
        self.is_finished = False
        self.warning_duration = 1400
        self.attack_duration = 350
        self.timer = 0
        
        side_start = random.choice(["LEFT", "RIGHT", "TOP", "BOTTOM"])
        if side_start == "LEFT":
            self.spawn_x = -150
            self.spawn_y = random.randint(50, HEIGHT - 150)
            self.end_x = WIDTH + 150
            self.end_y = random.randint(50, HEIGHT - 150)
        elif side_start == "RIGHT":
            self.spawn_x = WIDTH + 150
            self.spawn_y = random.randint(50, HEIGHT - 150)
            self.end_x = -150
            self.end_y = random.randint(50, HEIGHT - 150)
        elif side_start == "TOP":
            self.spawn_x = random.randint(100, WIDTH - 100)
            self.spawn_y = -150
            self.end_x = random.randint(100, WIDTH - 100)
            self.end_y = HEIGHT + 150
        else: 
            self.spawn_x = random.randint(100, WIDTH - 100)
            self.spawn_y = HEIGHT + 150
            self.end_x = random.randint(100, WIDTH - 100)
            self.end_y = -150

        dx = self.end_x - self.spawn_x
        dy = self.end_y - self.spawn_y
        self.total_dist = math.sqrt(dx**2 + dy**2)
        self.dir_x = dx / self.total_dist
        self.dir_y = dy / self.total_dist
        self.angle_deg = math.degrees(math.atan2(dy, dx))

    def update(self, dt, player):
        if self.is_finished: return
        if self.delay > 0: self.delay -= dt; return

        self.timer += dt
        if self.timer >= (self.warning_duration + self.attack_duration):
            self.is_finished = True
            return

        if self.warning_duration <= self.timer < (self.warning_duration + self.attack_duration):
            if player.invincible_timer <= 0:
                p_rect = pygame.Rect(player.x - 15, player.y - 70, 30, 70)
                progress = (self.timer - self.warning_duration) / self.attack_duration
                current_reach = self.total_dist * progress
                reach_x = self.spawn_x + self.dir_x * current_reach
                reach_y = self.spawn_y + self.dir_y * current_reach
                
                if self.check_line_box_collision(self.spawn_x, self.spawn_y, reach_x, reach_y, p_rect):
                    player.take_damage(10)

    def check_line_box_collision(self, x1, y1, x2, y2, box):
        cx, cy = box.centerx, box.centery
        line_dx, line_dy = x2 - x1, y2 - y1
        line_len_sq = line_dx**2 + line_dy**2
        if line_len_sq == 0: return False
        u = ((cx - x1) * line_dx + (cy - y1) * line_dy) / line_len_sq
        u = max(0.0, min(1.0, u))
        closest_x = x1 + u * line_dx
        closest_y = y1 + u * line_dy
        dist = math.sqrt((cx - closest_x)**2 + (cy - closest_y)**2)
        return dist < 45 

    def draw(self, screen):
        if self.is_finished or self.delay > 0: return
        if self.timer < self.warning_duration:
            # 🌟 깜빡임 삭제: 예고 장판을 항상 반투명하게 그립니다.
            perp_x = -self.dir_y * 32
            perp_y = self.dir_x * 32
            points = [
                (self.spawn_x + perp_x, self.spawn_y + perp_y),
                (self.end_x + perp_x, self.end_y + perp_y),
                (self.end_x - perp_x, self.end_y - perp_y),
                (self.spawn_x - perp_x, self.spawn_y - perp_y)
            ]
            warn_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(warn_mask, (255, 0, 0, 50), points)
            screen.blit(warn_mask, (0, 0))
            pygame.draw.line(screen, (255, 30, 30), (self.spawn_x + perp_x, self.spawn_y + perp_y), (self.end_x + perp_x, self.end_y + perp_y), 2)
            pygame.draw.line(screen, (255, 30, 30), (self.spawn_x - perp_x, self.spawn_y - perp_y), (self.end_x - perp_x, self.end_y - perp_y), 2)
        else:
            b_arm = boss_arm_parts[0]       # 팔뚝 (늘릴 부위)
            forearm = boss_arm_parts[1]     # 전완 (고정 100px)
            hand = boss_arm_parts[2]        # 손 (고정 100px)
            
            progress = (self.timer - self.warning_duration) / self.attack_duration
            current_reach = self.total_dist * progress
            
            arm_width = max(1, int(current_reach - 200))
            scaled_b_arm = pygame.transform.scale(b_arm, (arm_width, 64))
            
            canvas = pygame.Surface((arm_width + 200, 64), pygame.SRCALPHA)
            canvas.blit(scaled_b_arm, (0, 0))
            canvas.blit(forearm, (arm_width, 0))
            canvas.blit(hand, (arm_width + 100, 0))
            
            rotated_full_arm = pygame.transform.rotate(canvas, -self.angle_deg)
            arm_rect = rotated_full_arm.get_rect()
            
            arm_rect.center = (int(self.spawn_x + self.dir_x * (current_reach / 2)), 
                               int(self.spawn_y + self.dir_y * (current_reach / 2)))
            screen.blit(rotated_full_arm, arm_rect)

# --------------------------------
# 스프라이트 시트 로드 함수
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
        scaled_frame = pygame.transform.scale(frame, (int(frame_width * scale), int(frame_height * scale)))
        frames.append(scaled_frame)
    return frames

animations = {
    "idle": load_sprite_sheet("sprites/Player/_Idle.png", 120, 80, scale=2.5),
    "run": load_sprite_sheet("sprites/Player/_Run.png", 120, 80, scale=2.5),
    "jump": load_sprite_sheet("sprites/Player/_Jump.png", 120, 80, scale=2.5),
    "jump_fall_between": load_sprite_sheet("sprites/Player/_JumpFallinbetween.png", 120, 80, scale=2.5),
    "fall": load_sprite_sheet("sprites/Player/_Fall.png", 120, 80, scale=2.5),
    "dash": load_sprite_sheet("sprites/Player/_Dash.png", 120, 80, scale=2.5),
    "death": load_sprite_sheet("sprites/Player/_Death.png", 120, 80, scale=2.5),
    "hit": load_sprite_sheet("sprites/Player/_Hit.png", 120, 80, scale=2.5),
    "crouch": load_sprite_sheet("sprites/Player/_Crouch.png", 120, 80, scale=2.5),
    "crouch_walk": load_sprite_sheet("sprites/Player/_CrouchWalk.png", 120, 80, scale=2.5),
    "crouch_attack": load_sprite_sheet("sprites/Player/_CrouchAttack.png", 120, 80, scale=2.5),
    "attack1": load_sprite_sheet("sprites/Player/_Attack.png", 120, 80, scale=2.5),
    "attack2": load_sprite_sheet("sprites/Player/_Attack2.png", 120, 80, scale=2.5),
    "attack1_no_move": load_sprite_sheet("sprites/Player/_AttackNoMovement.png", 120, 80, scale=2.5),
    "attack2_no_move": load_sprite_sheet("sprites/Player/_Attack2NoMovement.png", 120, 80, scale=2.5),
    "attack_combo": load_sprite_sheet("sprites/Player/_AttackCombo.png", 120, 80, scale=2.5),
    "attack_combo_no_move": load_sprite_sheet("sprites/Player/_AttackComboNoMovement.png", 120, 80, scale=2.5),
    "slash_projectile": load_sprite_sheet("sprites/Player/Slash.png", 120, 80, scale=2.5)
}

try:
    cutscene_mage_images = {
        "idle": load_sprite_sheet("sprites/CutScene/Idle.png", 250, 250, scale=2.5),
        "cut": load_sprite_sheet("sprites/CutScene/Cut.png", 250, 250, scale=2.5)
    }
except Exception as e:
    dummy_mage = pygame.Surface((120, 140), pygame.SRCALPHA)
    dummy_mage.fill((50, 0, 70))
    cutscene_mage_images = {"idle": [dummy_mage], "cut": [dummy_mage]}

mage_frame_index = 0

try:
    boss_animations = {
        "teleport_in": load_sprite_sheet("sprites/Boss/teleport in.png", 320, 320, scale=1.8),
        "teleport_out": load_sprite_sheet("sprites/Boss/teleport out.png", 320, 320, scale=1.8),
        "idle": load_sprite_sheet("sprites/Boss/idle.png", 320, 320, scale=1.8),
        "attack1": load_sprite_sheet("sprites/Boss/attack1.png", 320, 320, scale=1.8),
        "attack2": load_sprite_sheet("sprites/Boss/attack2.png", 320, 320, scale=1.8),
        "attack3": load_sprite_sheet("sprites/Boss/attack3.png", 320, 320, scale=1.8),
        "attack4": load_sprite_sheet("sprites/Boss/attack4.png", 320, 320, scale=1.8),
        "attack5": load_sprite_sheet("sprites/Boss/attack5.png", 320, 320, scale=1.8)
    }
except Exception as e:
    dummy_boss = pygame.Surface((250, 320), pygame.SRCALPHA)
    dummy_boss.fill((120, 10, 20))
    boss_animations = {"teleport_in": [dummy_boss], "teleport_out": [dummy_boss], "idle": [dummy_boss], "attack1": [dummy_boss], "attack2": [dummy_boss], "attack3": [dummy_boss], "attack4": [dummy_boss], "attack5": [dummy_boss]}

boss_frame_index = 0

hit_effects_animations = {
    "04": load_sprite_sheet("sprites/Effects/04.png", 256, 256, scale=1.0),
    "06": load_sprite_sheet("sprites/Effects/06.png", 256, 256, scale=1.0),
    "08": load_sprite_sheet("sprites/Effects/08.png", 256, 256, scale=1.0),
    "10": load_sprite_sheet("sprites/Effects/10.png", 256, 256, scale=1.0)
}

state_data = {
    "idle": {"speed": 0, "animation_speed": 0.2},
    "run": {"speed": 5, "animation_speed": 0.3},
    "jump": {"speed": 5, "animation_speed": 0.2},
    "jump_fall_between": {"speed": 5, "animation_speed": 0.2},
    "fall": {"speed": 5, "animation_speed": 0.2},
    "dash": {"speed": 12, "animation_speed": 0.2}, 
    "death": {"speed": 0, "animation_speed": 0.15},
    "hit": {"speed": 0, "animation_speed": 0.18}, 
    "crouch": {"speed": 0, "animation_speed": 0.05},
    "crouch_walk": {"speed": 2, "animation_speed": 0.15},  
    "crouch_attack": {"speed": 0, "animation_speed": 0.25}, 
    "attack1": {"speed": 0, "animation_speed": 0.23},
    "attack2": {"speed": 0, "animation_speed": 0.23},
    "attack1_no_move": {"speed": 0, "animation_speed": 0.23},
    "attack2_no_move": {"speed": 0, "animation_speed": 0.23},
    "attack_combo": {"speed": 0, "animation_speed": 0.25},       
    "attack_combo_no_move": {"speed": 0, "animation_speed": 0.25},
}

KOREAN_FONTS = ["malgungothic", "applesandgothic", "notosanscjk", "dotum", "arial"]

# --------------------------------
# 비주얼 타격 이펙트 클래스
# --------------------------------
class HitEffect:
    def __init__(self, x, y, effect_id):
        self.type = "visual_hit"
        self.frames = hit_effects_animations.get(effect_id, [])
        self.frame_index = 0
        self.anim_speed = 0.3 
        self.is_dead = False
        if self.frames:
            self.rect = self.frames[0].get_rect(center=(int(x), int(y)))
        else:
            self.is_dead = True

    def update(self, dt, enemies, game_effects, player):
        self.frame_index += self.anim_speed
        if self.frame_index >= len(self.frames):
            self.is_dead = True
        return 0 

# --------------------------------
# 이펙트 및 투사체 클래스
# --------------------------------
class Effect:
    def __init__(self, x, y, effect_type, facing_right, saved_state=None):
        self.x = x
        self.y = y
        self.type = effect_type
        self.facing_right = facing_right
        self.frame_index = 0
        self.saved_state = saved_state
        self.is_dead = False
        self.hit_enemies = set() 
        self.has_triggered_slash = False  
        
        if self.type == "slash":
            self.frames = animations["slash_projectile"]
            self.anim_speed = 0.3
            self.speed = 20 if self.facing_right else -20
            if self.facing_right:
                self.rect = self.frames[0].get_rect(midleft=(int(self.x), int(self.y)))
            else:
                self.rect = self.frames[0].get_rect(midright=(int(self.x), int(self.y)))
        else:
            self.frames = animations.get(saved_state, animations["idle"])
            self.anim_speed = state_data.get(saved_state, {"animation_speed": 0.2})["animation_speed"]
            self.speed = 0
            self.rect = self.frames[0].get_rect(midbottom=(int(self.x), int(self.y)))

        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self.update_hitbox()

    def update_hitbox(self):
        if "attack" in str(self.saved_state):
            total_frames = len(self.frames)
            start_frame = total_frames // 4
            end_frame = int(total_frames * 0.75)
            if start_frame <= int(self.frame_index) <= end_frame:
                h_width = 100
                h_height = 45 if self.saved_state == "crouch_attack" else 80
                h_x = self.x if self.facing_right else self.x - h_width
                h_y = self.y - h_height
                self.attack_hitbox = pygame.Rect(h_x, h_y, h_width, h_height)
                return
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self, dt, enemies, game_effects, player):
        if self.is_dead:
            return 0

        if self.type == "slash":
            self.x += self.speed
            if self.facing_right:
                self.rect.midleft = (int(self.x), int(self.y))
            else:
                self.rect.midright = (int(self.x), int(self.y))
            if self.x < -150 or self.x > WIDTH + 150:
                self.is_dead = True
                return 0
        
        self.frame_index += self.anim_speed
        if self.frame_index >= len(self.frames):
            if self.type == "slash":
                self.frame_index = len(self.frames) - 1 
            else:
                self.is_dead = True
                return 0

        self.update_hitbox()

        # 🌟 [버그 수정]: 도플갱어 참격일 경우 보스가 아닌 '플레이어'를 공격합니다.
        if self.type == "doppel_slash":
            player_rect = pygame.Rect(player.x - 15, player.y - 70, 30, 70)
            # attack_hitbox나 투사체 본체 rect가 플레이어와 겹치면 피격
            collision_rect = self.attack_hitbox if "attack" in str(self.saved_state) else self.rect
            if collision_rect.colliderect(player_rect):
                if player not in self.hit_enemies: # 중복 피격 방지
                    self.hit_enemies.add(player)
                    player.take_damage(8) # 플레이어에게 대미지 8 부여
            return 0 # 보스에게는 대미지를 주지 않고 리턴

        # 기존 플레이어 분신/참격이 적(보스)을 공격하는 로직
        damage_sum = 0
        for enemy in enemies:
            if enemy.is_boss and boss_current_state == "teleport_out":
                continue

            if self.type == "slash":
                collision_box = self.rect.inflate(-210, -60) 
                if collision_box.colliderect(enemy.rect):
                    if enemy not in self.hit_enemies:
                        self.hit_enemies.add(enemy)
                        damage_sum += 20 
                        overlap = collision_box.clip(enemy.rect)
                        hx = overlap.centerx + random.randint(-10, 10)
                        hy = overlap.centery + random.randint(-10, 10)
                        game_effects.append(HitEffect(hx, hy, "04"))
            elif self.type != "slash" and self.attack_hitbox.colliderect(enemy.rect):
                if enemy not in self.hit_enemies:
                    self.hit_enemies.add(enemy)
                    damage_sum += 10 
                    overlap = self.attack_hitbox.clip(enemy.rect)
                    hx = overlap.centerx + random.randint(-20, 20)
                    hy = overlap.centery + random.randint(-20, 20)
                    if player.combo_timer > 0:
                        game_effects.append(HitEffect(hx, hy, "10"))
                    else:
                        eff_id = random.choice(["06", "08"])
                        game_effects.append(HitEffect(hx, hy, eff_id))
        return damage_sum

    def draw(self, screen):
        if self.is_dead or not self.frames:
            return

        idx = min(int(self.frame_index), len(self.frames) - 1)
        current_image = self.frames[idx].copy()

        current_scale = getattr(player, "scale_factor", 1.0)
        if current_scale != 1.0:
            w = int(current_image.get_width() * current_scale)
            h = int(current_image.get_height() * current_scale)
            current_image = pygame.transform.scale(current_image, (w, h))

        if not self.facing_right:
            current_image = pygame.transform.flip(current_image, True, False)
        
        # 🌟 이 부분을 추가해 줍니다!
        if hasattr(self, "color_mod"):
            current_image.fill(self.color_mod, special_flags=pygame.BLEND_RGBA_MULT)
        elif self.type == "slash":
            current_image.fill((255, 215, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            current_image.fill((218, 165, 32, 255), special_flags=pygame.BLEND_RGBA_MULT)

        image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
        screen.blit(current_image, image_rect)

# --------------------------------
# 가상의 적 및 보스 클래스
# --------------------------------
class Enemy:
    def __init__(self, x, y, is_boss=False):
        self.is_boss = is_boss
        if is_boss:
            self.rect = pygame.Rect(x - 40, y - 80, 80, 160)
        else:
            self.rect = pygame.Rect(x, y - 100, 60, 100)

    def draw(self, screen):
        if not self.is_boss:
            pygame.draw.rect(screen, (140, 90, 70), self.rect, border_radius=6)
            pygame.draw.rect(screen, (200, 40, 40), (self.rect.x + 15, self.rect.y + 20, 30, 30), border_radius=15)

# --------------------------------
# 플레이어 클래스
# --------------------------------
class Player:
    def __init__(self):
        self.x = 100
        self.y = GROUND_Y
        self.facing_right = True
        self.current_state = "idle"
        self.frame_index = 0

        self.y_velocity = 0
        self.gravity = 0.6
        self.jump_power = -13.5  
        self.is_grounded = True

        self.attack_count = 0        
        self.hit_count = 0           
        self.combo_timer = 0         
        
        self.has_hit_first = False   
        self.has_hit_second = False  
        self.has_hit_normal = False  
        self.has_saved_this_attack = False

        self.max_hp = 100
        self.current_hp = 100
        
        self.boss_max_hp = 1300
        self.boss_current_hp = 1300
        self.pulse_timer = 0

        self.saved_actions = []     
        self.player_attack_hitbox = pygame.Rect(0, 0, 0, 0)

        self.scale_factor = 1.0
        self.target_scale = 1.0

        self.max_dashes = 2
        self.available_dashes = 2
        self.dash_cooldown_time = 2000  
        self.dash_cooldown_timer = 0
        self.was_dashing_last_frame = False
        
        self.movement_speed_modifier = 1.0
        self.slow_debuff_timer = 0
        
        self.flash_timer = 0
        self.invincible_timer = 0  

        # 🌟 대쉬 잔상 제어용 변수
        self.dash_afterimages = []
        self.afterimage_timer = 0

    def change_state(self, new_state):
        if self.current_state == "hit" and new_state != "idle":
            if self.frame_index < len(animations["hit"]) - 1:
                return
        if self.current_state == "dash" and new_state not in ["idle", "hit", "death"]:
            return
        if self.current_state != new_state:
            self.current_state = new_state
            self.frame_index = 0
            if "attack" in new_state:
                self.has_hit_first = False
                self.has_hit_second = False
                self.has_hit_normal = False
                self.has_saved_this_attack = False

    def take_damage(self, amount):
        if self.is_dead() or self.invincible_timer > 0:
            return
        self.current_hp = max(0, self.current_hp - amount)
        self.change_state("hit") 
        self.flash_timer = 150   
        self.invincible_timer = 600 

    def is_attacking(self):
        return "attack" in self.current_state
        
    def is_dashing(self):
        return self.current_state == "dash"

    def is_dead(self):
        return self.current_state == "death"

    def update_player_hitbox(self):
        if self.is_attacking():
            current_frames = animations[self.current_state]
            total_frames = len(current_frames)
            start_frame = total_frames // 4
            end_frame = int(total_frames * 0.75)
            if start_frame <= int(self.frame_index) <= end_frame:
                h_width = 130
                h_height = 45 if self.current_state == "crouch_attack" else 80
                h_x = self.x if self.facing_right else self.x - h_width
                h_y = self.y - h_height
                self.player_attack_hitbox = pygame.Rect(h_x, h_y, h_width, h_height)
                return
        self.player_attack_hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self, keys, dt, enemies, game_effects):
        current_floor = get_current_ground_y()

        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            if self.invincible_timer < 0: self.invincible_timer = 0

        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer < 0: self.flash_timer = 0

        if self.available_dashes < self.max_dashes:
            self.dash_cooldown_timer += dt
            if self.dash_cooldown_timer >= self.dash_cooldown_time:
                self.available_dashes += 1
                self.dash_cooldown_timer = 0

        currently_dashing = self.is_dashing()
        if currently_dashing and not self.was_dashing_last_frame:
            if self.available_dashes <= 0:
                if hasattr(self, "dash_timer"): self.dash_timer = 0
                if hasattr(self, "dash_duration"): self.dash_duration = 0
                self.change_state("idle") 
            else:
                self.available_dashes -= 1
                if self.available_dashes == self.max_dashes - 1:
                    self.dash_cooldown_timer = 0
        self.was_dashing_last_frame = currently_dashing

        if self.current_hp <= 0:
            self.change_state("death")

        if self.is_dead():
            if not self.is_grounded:
                self.y += self.y_velocity
                self.y_velocity += self.gravity
                if self.y >= current_floor:
                    self.y = current_floor
                    self.y_velocity = 0
                    self.is_grounded = True

            current_frames = animations[self.current_state]
            base_anim_speed = state_data[self.current_state]["animation_speed"]
            self.frame_index += base_anim_speed
            if self.frame_index >= len(current_frames):
                self.frame_index = len(current_frames) - 1
            return

        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_timer = 0

        self.pulse_timer += 0.1
        current_speed = state_data[self.current_state]["speed"]
        current_speed *= self.movement_speed_modifier

        if self.current_state == "hit":
            current_speed = 0

        if self.is_dashing():
            self.x += current_speed if self.facing_right else -current_speed
        else:
            if keys[pygame.K_LEFT] and self.current_state != "hit":
                self.x -= current_speed
                self.facing_right = False
            if keys[pygame.K_RIGHT] and self.current_state != "hit":
                self.x += current_speed
                self.facing_right = True

        self.x = max(50, min(self.x, WIDTH - 50))

        if not self.is_grounded:
            self.y += self.y_velocity
            self.y_velocity += self.gravity
            
            if game_stage == "BOSS" and self.y_velocity > 0:
                feet_rect = pygame.Rect(self.x - 12, self.y - 4, 24, 8)
                for plat in boss_platforms:
                    if plat.rect.colliderect(feet_rect) and (self.y - self.y_velocity <= plat.rect.top + 3):
                        self.y = plat.rect.top
                        self.y_velocity = 0
                        self.is_grounded = True
                        break

            if self.y >= current_floor:
                self.y = current_floor
                self.y_velocity = 0
                self.is_grounded = True

        if cutscene_stage == 0:
            if not self.is_attacking() and not self.is_dashing() and self.current_state != "hit":
                if not self.is_grounded:
                    if self.current_state != "dash":
                        if self.y_velocity < -2.0:
                            self.change_state("jump")
                        elif -2.0 <= self.y_velocity <= 2.0:
                            self.change_state("jump_fall_between")
                        else:
                            self.change_state("fall")
                else:
                    moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
                    if keys[pygame.K_DOWN]:
                        if moving:
                            self.change_state("crouch_walk")
                        else:
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

        fps_modifier = (dt / 16.66) if dt > 0 else 1.0
        fps_modifier = max(0.5, min(fps_modifier, 2.0))
        
        self.frame_index += final_anim_speed * fps_modifier

        if self.is_attacking():
            current_frame_int = int(self.frame_index)
            total_frames = len(current_frames)

            if "combo" in self.current_state:
                first_hit_frame = total_frames // 4
                second_hit_frame = int(total_frames * 0.7)
                if current_frame_int == first_hit_frame and not self.has_hit_first:
                    self.has_hit_first = True
                    self.check_attack_combo_collision(enemies, is_combo_hit=True)
                if current_frame_int == second_hit_frame and not self.has_hit_second:
                    self.has_hit_second = True
                    self.check_attack_combo_collision(enemies, is_combo_hit=True)
            else:
                normal_hit_frame = total_frames // 2
                if current_frame_int == normal_hit_frame and not self.has_hit_normal:
                    self.has_hit_normal = True
                    self.check_attack_combo_collision(enemies, is_combo_hit=False)

        self.update_player_hitbox()

        if self.frame_index >= len(current_frames):
            if self.current_state == "hit":
                self.current_state = "idle"
                self.frame_index = 0
            else:
                self.frame_index = 0
                if self.is_attacking():
                    if self.current_state == "crouch_attack":
                        if keys[pygame.K_DOWN]:
                            self.change_state("crouch")
                        else:
                            self.change_state("idle")
                    else:
                        self.attack_count = 1 - self.attack_count 
                        self.change_state("idle")
                elif self.is_dashing():
                    self.change_state("idle")

        # 🌟 대쉬 잔상 매커니즘 연동
        if self.is_dashing():
            self.afterimage_timer += dt
            if self.afterimage_timer >= 40:
                self.afterimage_timer = 0
                idx = min(int(self.frame_index), len(current_frames) - 1)
                img_copy = current_frames[idx].copy()
                if not self.facing_right:
                    img_copy = pygame.transform.flip(img_copy, True, False)
                self.dash_afterimages.append({
                    "img": img_copy, "x": self.x, "y": self.y, "alpha": 180
                })

        for ghost in self.dash_afterimages[:]:
            ghost["alpha"] -= 8
            if ghost["alpha"] <= 0:
                self.dash_afterimages.remove(ghost)

    # 🌟 [완벽 복구]: 날아갔던 핵심 메서드 핸들러 라인 재배치
    def handle_attack_input(self, keys):
        if self.is_attacking() or self.is_dashing() or not self.is_grounded or self.is_dead() or self.current_state == "hit":
            return 

        if sound_sword: sound_sword.play() # 🌟 [공격 사운드 추가]

        if keys[pygame.K_DOWN]:
            self.change_state("crouch_attack")
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

    def handle_skill_input(self, key, game_effects):
        if self.is_dead() or self.current_state == "hit":
            return

        if key == pygame.K_a:
            if self.is_attacking() and not self.has_saved_this_attack:
                if len(self.saved_actions) < 2:
                    self.saved_actions.append(self.current_state)
                    self.has_saved_this_attack = True
                    print(f"동작 세이브: {self.current_state} ({len(self.saved_actions)}/2)")
            elif not self.is_attacking():
                print("공격 중에만 기술을 세이브할 수 있습니다!")

        elif key == pygame.K_s:
            if len(self.saved_actions) > 0:
                offset = 40
                current_spawn_y = self.y 
                
                for state in self.saved_actions:
                    spawn_x = self.x + offset if self.facing_right else self.x - offset
                    game_effects.append(Effect(spawn_x, current_spawn_y, "release", self.facing_right, saved_state=state))
                    offset += 50
                self.saved_actions.clear()

    def check_attack_combo_collision(self, enemies, is_combo_hit):
        hitbox_width = 130
        if self.current_state == "crouch_attack":
            hitbox_height = 45
            hitbox_y = self.y - hitbox_height
        else:
            hitbox_height = 80
            hitbox_y = self.y - hitbox_height

        attack_rect = pygame.Rect(self.x if self.facing_right else self.x - hitbox_width, hitbox_y, hitbox_width, hitbox_height)

        for enemy in enemies:
            if enemy.is_boss and boss_current_state == "teleport_out":
                continue

            if attack_rect.colliderect(enemy.rect):
                self.boss_current_hp = max(0, self.boss_current_hp - 10)

                overlap = attack_rect.clip(enemy.rect)
                hx = overlap.centerx + random.randint(-20, 20)
                hy = overlap.centery + random.randint(-20, 20)
                if self.combo_timer > 0:
                    game_effects.append(HitEffect(hx, hy, "10"))
                else:
                    eff_id = random.choice(["06", "08"])
                    game_effects.append(HitEffect(hx, hy, eff_id))

                if not is_combo_hit and self.combo_timer <= 0:
                    self.hit_count += 1
                    if self.hit_count >= 5:
                        self.combo_timer = 3000  
                        self.hit_count = 0
                break

    def draw(self, screen):
        for ghost in self.dash_afterimages:
            ghost_img = ghost["img"].copy()
            ghost_img.fill((255, 200, 0, ghost["alpha"]), special_flags=pygame.BLEND_RGBA_MULT)
            ghost_rect = ghost_img.get_rect(midbottom=(int(ghost["x"]), int(ghost["y"])))
            screen.blit(ghost_img, ghost_rect)

        current_frames = animations[self.current_state]
        idx = min(int(self.frame_index), len(current_frames) - 1)
        current_image = current_frames[idx].copy()
        current_scale = getattr(self, "scale_factor", 1.0)

        if current_scale != 1.0:
            w = int(current_image.get_width() * current_scale)
            h = int(current_image.get_height() * current_scale)
            current_image = pygame.transform.scale(current_image, (w, h))

        if not self.facing_right:
            current_image = pygame.transform.flip(current_image, True, False)

        if self.flash_timer > 0 or (self.invincible_timer > 0 and int(self.invincible_timer / 40) % 2 == 0):
            white_mask = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
            white_mask.fill((255, 255, 255, 150)) 
            current_image.blit(white_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        image_rect = current_image.get_rect(midbottom=(int(self.x), int(self.y)))
        screen.blit(current_image, image_rect)

    def draw_vector_ui(self, screen):
        if not hasattr(self, "hero_lerp_hp"): self.hero_lerp_hp = self.current_hp
        if not hasattr(self, "boss_lerp_hp"): self.boss_lerp_hp = self.boss_current_hp

        self.hero_lerp_hp += (self.current_hp - self.hero_lerp_hp) * 0.05
        self.boss_lerp_hp += (self.boss_current_hp - self.boss_lerp_hp) * 0.05

        start_x = 30
        start_y = 25
        panel_w = 260
        panel_h = 56
        panel_x = start_x + 40  
        panel_y = start_y + 8
        
        pygame.draw.rect(screen, (35, 25, 22), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (45, 38, 35), (panel_x + 2, panel_y + 2, panel_w - 4, panel_h - 4))
        pygame.draw.rect(screen, (24, 18, 15), (panel_x + 6, panel_y + 18, panel_w - 12, panel_h - 22))
        
        font = pygame.font.SysFont(KOREAN_FONTS, 12, bold=True)
        text_surf = font.render("HERO", True, (168, 147, 126)) 
        screen.blit(text_surf, (panel_x + 35, panel_y + 4))

        bar_x = panel_x + 10
        bar_w = panel_w - 20
        bar_h = 10
        
        pygame.draw.rect(screen, (40, 15, 15), (bar_x, panel_y + 22, bar_w, bar_h))
        
        hero_lerp_ratio = max(0.0, self.hero_lerp_hp / self.max_hp)
        if hero_lerp_ratio > 0:
            lerp_fill_w = int(bar_w * hero_lerp_ratio)
            pygame.draw.rect(screen, (220, 180, 20), (bar_x, panel_y + 22, lerp_fill_w, bar_h))
            
        hp_ratio = max(0.0, self.current_hp / self.max_hp)
        if hp_ratio > 0:
            fill_w = int(bar_w * hp_ratio)
            pygame.draw.rect(screen, (185, 35, 15), (bar_x, panel_y + 22, fill_w, bar_h))
            pygame.draw.rect(screen, (235, 75, 55), (bar_x, panel_y + 22, fill_w, 2))
            pygame.draw.rect(screen, (120, 15, 5), (bar_x, panel_y + 22 + bar_h - 2, fill_w, 2))
            
        pygame.draw.rect(screen, (70, 55, 45), (bar_x, panel_y + 22, bar_w, bar_h), 1)

        combo_y = panel_y + 36
        if self.combo_timer > 0:
            c_color = (220, 140, 20) if int(self.pulse_timer * 2) % 2 == 0 else (190, 110, 10)
            c_hi = (255, 200, 70)
            c_sh = (130, 70, 5)
            mp_ratio = self.combo_timer / 3000
        else:
            c_color = (180, 90, 20)
            c_hi = (220, 130, 40)
            c_sh = (110, 50, 10)
            mp_ratio = self.hit_count / 5

        pygame.draw.rect(screen, (35, 20, 10), (bar_x, combo_y, bar_w, bar_h))
        if mp_ratio > 0:
            fill_w = int(bar_w * mp_ratio)
            pygame.draw.rect(screen, c_color, (bar_x, combo_y, fill_w, bar_h))
            pygame.draw.rect(screen, c_hi, (bar_x, combo_y, fill_w, 2))
            pygame.draw.rect(screen, c_sh, (bar_x, combo_y + bar_h - 2, fill_w, 2))
        pygame.draw.rect(screen, (70, 55, 45), (bar_x, combo_y, bar_w, bar_h), 1)

        dash_bar_y = combo_y + 14
        pygame.draw.rect(screen, (20, 18, 16), (bar_x, dash_bar_y, bar_w, 8))
        
        avail_dashes = getattr(self, "available_dashes", 2)
        cooldown_timer = getattr(self, "dash_cooldown_timer", 0)
        cooldown_time = getattr(self, "dash_cooldown_time", 2000)
        
        if avail_dashes == 2:
            pygame.draw.rect(screen, (0, 255, 200), (bar_x, dash_bar_y, bar_w, 8)) 
        elif avail_dashes == 1:
            half_w = bar_w // 2
            pygame.draw.rect(screen, (0, 255, 200), (bar_x, dash_bar_y, half_w, 8)) 
            progress = min(1.0, cooldown_timer / cooldown_time)
            charge_w = int(half_w * progress)
            pygame.draw.rect(screen, (200, 150, 0), (bar_x + half_w, dash_bar_y, charge_w, 8)) 
        else:
            progress = min(1.0, cooldown_timer / cooldown_time)
            half_w = bar_w // 2
            charge_w = int(half_w * progress)
            pygame.draw.rect(screen, (120, 40, 40), (bar_x, dash_bar_y, charge_w, 8)) 

        pygame.draw.rect(screen, (70, 55, 45), (bar_x, dash_bar_y, bar_w, 8), 1)
        pygame.draw.line(screen, (70, 55, 45), (bar_x + bar_w // 2, dash_bar_y), (bar_x + bar_w // 2, dash_bar_y + 7), 1)

        circle_x = start_x + 32
        circle_y = start_y + 32
        radius = 32
        pygame.draw.circle(screen, (35, 28, 24), (circle_x, circle_y), radius)      
        pygame.draw.circle(screen, (115, 98, 83), (circle_x, circle_y), radius - 1)  
        pygame.draw.circle(screen, (150, 132, 115), (circle_x, circle_y), radius - 3, 1) 
        pygame.draw.circle(screen, (24, 18, 15), (circle_x, circle_y), radius - 4)  
        pygame.draw.circle(screen, (55, 45, 40), (circle_x, circle_y - 6), 11)
        pygame.draw.ellipse(screen, (55, 45, 40), (circle_x - 18, circle_y + 4, 36, 26))
        pygame.draw.circle(screen, (70, 55, 45), (circle_x, circle_y), radius - 4, 1)

        slot_y = panel_y + panel_h + 10
        slot_size = 50  
        font_key = pygame.font.SysFont("arial", 20, bold=True)
        font_stack = pygame.font.SysFont("arial", 11, bold=True)
        mint_blue = (0, 245, 255) 

        slot_a_x = panel_x + 6
        pygame.draw.rect(screen, (35, 25, 22), (slot_a_x, slot_y, slot_size, slot_size))
        pygame.draw.rect(screen, (55, 48, 44), (slot_a_x + 2, slot_y + 2, slot_size - 4, slot_size - 4))
        txt_a = font_key.render("A", True, mint_blue)
        a_rect = txt_a.get_rect(center=(slot_a_x + slot_size // 2, slot_y + 16))
        screen.blit(txt_a, a_rect)
        stack_txt = font_stack.render(f"{len(self.saved_actions)}/2", True, (180, 220, 240))
        stack_rect = stack_txt.get_rect(center=(slot_a_x + slot_size // 2, slot_y + 36))
        screen.blit(stack_txt, stack_rect)

        slot_s_x = slot_a_x + slot_size + 12
        pygame.draw.rect(screen, (35, 25, 22), (slot_s_x, slot_y, slot_size, slot_size))
        pygame.draw.rect(screen, (55, 48, 44), (slot_s_x + 2, slot_y + 2, slot_size - 4, slot_size - 4))
        txt_s = font_key.render("S", True, mint_blue)
        s_rect = txt_s.get_rect(center=(slot_s_x + slot_size // 2, slot_y + 16))
        screen.blit(txt_s, s_rect)

        if game_stage == "BOSS":
            boss_bar_w = 500              
            boss_bar_h = 16
            boss_x_bar = (WIDTH // 2) - (boss_bar_w // 2)
            boss_y_bar = HEIGHT - 45          
            
            pygame.draw.rect(screen, (35, 25, 22), (boss_x_bar - 4, boss_y_bar - 4, boss_bar_w + 8, boss_bar_h + 8))
            pygame.draw.rect(screen, (45, 38, 35), (boss_x_bar - 2, boss_y_bar - 2, boss_bar_w + 4, boss_bar_h + 4))
            pygame.draw.rect(screen, (24, 18, 15), (boss_x_bar, boss_y_bar, boss_bar_w, boss_bar_h))
            
            boss_lerp_ratio = self.boss_lerp_hp / self.boss_max_hp
            if boss_lerp_ratio > 0:
                b_lerp_fill = int(boss_bar_w * boss_lerp_ratio)
                pygame.draw.rect(screen, (220, 180, 20), (boss_x_bar, boss_y_bar, b_lerp_fill, boss_bar_h))
                
            boss_ratio = self.boss_current_hp / self.boss_max_hp
            if boss_ratio > 0:
                b_fill = int(boss_bar_w * boss_ratio)
                pygame.draw.rect(screen, (140, 25, 25), (boss_x_bar, boss_y_bar, b_fill, boss_bar_h))
                pygame.draw.rect(screen, (200, 50, 50), (boss_x_bar, boss_y_bar, b_fill, 3)) 
                pygame.draw.rect(screen, (80, 10, 10), (boss_x_bar, boss_y_bar + boss_bar_h - 3, b_fill, 3))
                
            pygame.draw.rect(screen, (85, 70, 60), (boss_x_bar, boss_y_bar, boss_bar_w, boss_bar_h), 1)
# --------------------------------
# 타이틀 씬 버튼 드로잉 및 클릭 헬퍼 함수
# --------------------------------
def draw_title_button(screen, text, x, y, width, height, mouse_pos):
    button_rect = pygame.Rect(x, y, width, height)
    is_hovered = button_rect.collidepoint(mouse_pos)
    bg_color = (45, 38, 35) if not is_hovered else (55, 52, 60)
    line_color = (35, 25, 22) if not is_hovered else (0, 245, 255)
    text_color = (168, 147, 126) if not is_hovered else (0, 245, 255)
    pygame.draw.rect(screen, line_color, (x - 2, y - 2, width + 4, height + 4), border_radius=6)
    pygame.draw.rect(screen, bg_color, button_rect, border_radius=4)
    font_btn = pygame.font.SysFont(KOREAN_FONTS, 18, bold=True)
    btn_surf = font_btn.render(text, True, text_color)
    btn_rect = btn_surf.get_rect(center=button_rect.center)
    screen.blit(btn_surf, btn_rect)
    return button_rect

# --------------------------------
# 인스턴스 초기화 및 메인 루프 시작
# --------------------------------
player = Player()
enemies = [Enemy(700, GROUND_Y, is_boss=False)]
game_effects = [] 

while True:
    dt = clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()

    # 🌟 [BGM 마스터 오토 체인저]
    if current_scene in ["TITLE", "RULES"]:
        play_bgm("Dark.wav")
    elif current_scene == "GAME":
        if game_stage == "PRACTICE":
            play_bgm("Dark.wav")
        elif game_stage == "BOSS":
            play_bgm("Har.wav")

    # ==================================================================
    # 🌟 [전면 수정] 메인 이벤트 핸들러 루프 (일시정지 인풋 버그 완전 해결)
    # ==================================================================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        # --------------------------------------------------------------
        # ① 마우스 클릭 이벤트 관리 구역
        # --------------------------------------------------------------
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 🌟 [치명적 버그 해결]: 일시정지 상태일 때 마우스 클릭 좌표 정밀 매핑
            if current_scene == "GAME" and is_paused:
                menu_w, menu_h = 320, 360
                menu_x, menu_y = (WIDTH // 2) - (menu_w // 2), (HEIGHT // 2) - (menu_h // 2)
                
                # 각 버튼의 실제 사각형 Rect 구역 계산
                btn_restart_rect = pygame.Rect((WIDTH // 2) - 110, menu_y + 110, 220, 45)
                btn_menu_rect    = pygame.Rect((WIDTH // 2) - 110, menu_y + 180, 220, 45)
                btn_exit_rect    = pygame.Rect((WIDTH // 2) - 110, menu_y + 250, 220, 45)
                
                if btn_restart_rect.collidepoint(mouse_pos):
                    is_paused = False
                    player.__init__()
                    if game_stage == "BOSS":
                        boss_current_state = "teleport_in"
                        boss_frame_index = 0
                        player.boss_current_hp = player.boss_max_hp
                        player.boss_arms.clear()
                        enemies = [Enemy(boss_spawn_x, 260, is_boss=True)]
                    else:
                        enemies = [Enemy(700, GROUND_Y, is_boss=False)]
                    game_effects.clear()
                    continue
                    
                elif btn_menu_rect.collidepoint(mouse_pos):
                    is_paused = False
                    current_scene = "TITLE"
                    continue
                    
                elif btn_exit_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
            
            # 일반 인게임 씬 마우스 클릭 분기점 (일시정지가 아닐 때만 작동)
            elif current_scene == "TITLE":
                btn_start = pygame.Rect(80, 320, 220, 50)
                btn_rules = pygame.Rect(80, 390, 220, 50)
                btn_exit = pygame.Rect(80, 460, 220, 50)
                if btn_start.collidepoint(mouse_pos):
                    current_scene = "GAME"
                    game_stage = "PRACTICE" 
                    cutscene_stage = 0      
                    cutscene_timer = 0      
                    cutscene_player_x = 0   
                    black_mage_img = None
                    black_mage_state = "idle"  
                    black_mage_alpha = 255     
                    player.__init__() 
                    enemies = [Enemy(700, GROUND_Y, is_boss=False)]
                    game_effects.clear()
                elif btn_rules.collidepoint(mouse_pos):
                    current_scene = "RULES"
                elif btn_exit.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                    
            elif current_scene == "RULES":
                btn_back = pygame.Rect(80, 500, 180, 45)
                if btn_back.collidepoint(mouse_pos):
                    current_scene = "TITLE"

        # --------------------------------------------------------------
        # ② 키보드 누름(KEYDOWN) 이벤트 관리 구역
        # --------------------------------------------------------------
        if event.type == pygame.KEYDOWN:
            # 인게임 상태에서 ESC 누르면 언제나 부드럽게 일시정지 온/오프 토글
            if current_scene == "GAME" and event.key == pygame.K_ESCAPE and cutscene_stage == 0 and not boss_death_trigger:
                is_paused = not is_paused
                pause_selected_idx = 0
                continue

            # 🌟 [키보드 엔터 버그 해결]: 일시정지 메뉴가 활성화되었을 때의 독립적 키보드 제어 라인
            if current_scene == "GAME" and is_paused:
                if event.key == pygame.K_UP:
                    pause_selected_idx = (pause_selected_idx - 1) % 3
                elif event.key == pygame.K_DOWN:
                    pause_selected_idx = (pause_selected_idx + 1) % 3
                elif event.key == pygame.K_RETURN:
                    if pause_selected_idx == 0:     # 재시작
                        is_paused = False
                        player.__init__()
                        if game_stage == "BOSS":
                            boss_current_state = "teleport_in"
                            boss_frame_index = 0
                            player.boss_current_hp = player.boss_max_hp
                            player.boss_arms.clear()
                            enemies = [Enemy(boss_spawn_x, 260, is_boss=True)]
                        else:
                            enemies = [Enemy(700, GROUND_Y, is_boss=False)]
                        game_effects.clear()
                    elif pause_selected_idx == 1:   # 메인 메뉴로
                        is_paused = False
                        current_scene = "TITLE"
                    elif pause_selected_idx == 2:   # 게임 종료
                        pygame.quit()
                        sys.exit()
                continue # 일시정지 중일 때는 하단의 캐릭터 플레이어 조작 입력을 차단(스킵)합니다.

            # 일반 인게임 캐릭터 키 제어선 (일시정지가 아닐 때만 유효)
            if current_scene == "GAME" and not player.is_dead():
                if event.key == pygame.K_x:  
                    player.handle_attack_input(pygame.key.get_pressed())
                
                if event.key == pygame.K_z and not player.is_attacking() and player.current_state != "dash":
                    player.change_state("dash")
                    
                if event.key in [pygame.K_a, pygame.K_s]:
                    player.handle_skill_input(event.key, game_effects)
                    
                if event.key == pygame.K_SPACE and player.is_grounded and not player.is_dashing() and cutscene_stage == 0:
                    player.y_velocity = player.jump_power
                    player.is_grounded = False
                    player.change_state("jump")
                    if sound_jumping:
                        sound_jumping.play()

    # --- [SCENE 1: TITLE SCREEN] ---
    if current_scene == "TITLE":
        screen.blit(title_image, (0, 0))
        font_title = pygame.font.SysFont(KOREAN_FONTS, 48, bold=True)
        title_surf = font_title.render("BeforeThen", True, (255, 235, 205))
        screen.blit(title_surf, (80, 120))
        draw_title_button(screen, "게 임 시 작", 80, 320, 220, 50, mouse_pos)
        draw_title_button(screen, "규   칙", 80, 390, 220, 50, mouse_pos)
        draw_title_button(screen, "게 임 종 료", 80, 460, 220, 50, mouse_pos)

    # --- [SCENE 2: RULES SCREEN] ---
    elif current_scene == "RULES":
        screen.blit(title_image, (0, 0))
        panel_surf = pygame.Surface((750, 480), pygame.SRCALPHA)
        panel_surf.fill((24, 18, 15, 230))
        screen.blit(panel_surf, (80, 50))
        pygame.draw.rect(screen, (168, 147, 126), (80, 50, 750, 480), 2, border_radius=8)
        font_rh = pygame.font.SysFont(KOREAN_FONTS, 24, bold=True)
        font_rb = pygame.font.SysFont(KOREAN_FONTS, 15, bold=False)
        mint_color = (0, 245, 255)
        screen.blit(font_rh.render("■ 고유 능력: '세이브(Save)' 규칙 가이드", True, (255, 215, 0)), (110, 80))
        rules_text = [
            "1. 자신이 행동한 공격 동작을 임의로 저장하고, 원할 때 내보낼 수 있습니다.",
            "2. 저장된 동작은 스스로 낸 그 이상의 파괴력을 낸 수 없습니다 (최대 2개 저장 가능).",
            "3. [핵심 반발 참격 규칙]",
            "   저장된 행동 2개의 타격 영역이 겹치거나, 분신과 본인의 공격선이 겹칠 때 마력 외부에 둘러둔",
            "   '기'의 반발 덕분에 마력이 섞이지 못하고 상대를 관통하는 강력한 [황금빛 참격 투사체]를 밀어냅니다.",
            "",
            "■ 조작 방법 가이드",
            "   - 좌우 방향키 : 캐릭터 횡스크롤 이동 (아래 방향키와 연계 시 웅크려 이동)",
            "   - SPACE 바 : 점프 구동 (체공 속도에 따라 낙하 가교 모션 자동 연동)",
            "   - Z 키 : 전방으로 기민하게 이동하는 황금빛 불투명 대쉬",
            "   - X 키 : 기본 연속 공격 (콤보 5회 누적 시 가속 버프 돌입)",
            "   - A 키 : 세이브(SAVE) - 플레이어가 공격 모션 작동 중에만 슬롯 저장 유효",
            "   - S 키 : 로드(LOAD) - 저장된 모션을 필드 전방에 순차적으로 불투명 실루엣 방출"
        ]
        y_offset = 130
        for line in rules_text:
            color = mint_color if "■" in line or "키" in line or "참격" in line else (220, 210, 200)
            screen.blit(font_rb.render(line, True, color), (110, y_offset))
            y_offset += 25
        draw_title_button(screen, "돌 아 가 기", 80, 500, 180, 45, mouse_pos)

    # --- [SCENE 3: BLACK LOADING SCREEN] ---
    elif current_scene == "LOADING":
        screen.fill((10, 10, 14))
        loading_timer -= dt
        font_load = pygame.font.SysFont(KOREAN_FONTS, 26, bold=True)
        load_surf = font_load.render("B O S S   S T A G E   L O A D I N G . . .", True, (0, 245, 255))
        load_rect = load_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(title_image, (0, 0)) 
        screen.blit(font_load.render("B O S S   S T A G E   L O A D I N G . . .", True, (0, 245, 255)), load_rect)
        if loading_timer <= 0:
            current_scene = "GAME"
            game_stage = "PRACTICE"  
            cutscene_stage = 1  
            cutscene_timer = 0
            player.x = -50                  
            player.facing_right = True
            player.change_state("run")      
            player.scale_factor = 1.0
            player.target_scale = 1.0
            black_mage_state = "idle"
            black_mage_alpha = 255
            enemies = [] 
            game_effects.clear()

    # --- [SCENE 4: ACTUAL MAIN GAMEPLAY] ---
    elif current_scene == "GAME":
        keys = pygame.key.get_pressed()

        # 🌟 일시정지 상태면 게임 월드의 시간이 멈춥니다.
        if is_paused:
            pass 
        else:
            player.scale_factor += (player.target_scale - player.scale_factor) * 0.05
            
            # --- 🌟 보스 처치 판정 및 death 애니메이션 전개 스케줄러 ---
            if game_stage == "BOSS" and player.boss_current_hp <= 0 and not boss_death_trigger:
                boss_death_trigger = True
                boss_current_state = "death"
                boss_frame_index = 0
                player.boss_arms.clear()

            if boss_death_trigger:
                b_frames = boss_animations.get("death", [])
                if b_frames:
                    boss_frame_index += 0.15
                    if boss_frame_index >= len(b_frames):
                        boss_frame_index = len(b_frames) - 1
                        boss_death_timer += dt
                        if boss_death_timer >= 1500:
                            current_scene = "CLEAR" # 클리어 화면으로 강제 전송
            
            # 🌟 보스가 살아있을 때만 기존의 무결점 보스 AI 및 공격 패턴 업데이트가 작동합니다.
            if game_stage == "BOSS" and cutscene_stage == 0 and not boss_death_trigger:
                b_frames = boss_animations.get(boss_current_state, [])
                if b_frames:
                    boss_frame_index += 0.15
                    if boss_frame_index >= len(b_frames):
                        if boss_current_state == "teleport_out":
                            boss_current_state = "teleport_in"
                            boss_frame_index = 0
                            player.boss_current_point_idx = player.boss_next_point_idx
                            boss_x, boss_y = player.boss_fixed_points[player.boss_current_point_idx]
                            if enemies: enemies[0].rect.center = (boss_x, boss_y)
                                
                        elif boss_current_state == "teleport_in":
                            boss_current_state = "idle"
                            boss_frame_index = 0
                            
                            if not hasattr(player, "patterns_done") or player.patterns_done == 0:
                                player.patterns_to_do = random.randint(1, 2)
                                player.patterns_done = 0
                            
                            if player.patterns_done < player.patterns_to_do:
                                pattern = random.choice([0, 1, 2, 3, 4])
                                
                                if pattern == 0:
                                    boss_current_state = "attack1"
                                    player.boss_projectiles.append(BossSeekerOrb(boss_x - 140, boss_y - 40))
                                elif pattern == 1:
                                    boss_current_state = "attack2"
                                    player.boss_fires.append(BossGroundFire())
                                elif pattern == 2:
                                    boss_current_state = "attack4"
                                    player.boss_arms.append(BossOmnThrustManager())
                                elif pattern == 3:
                                    boss_current_state = "attack5"
                                    player.boss_arms.append(BossDoppelgangerManager(boss_x, boss_y, player))
                                else:
                                    boss_current_state = "attack3"
                                    player.boss_arms.append(BossLightningManager(boss_x, boss_y, player))
                                
                                boss_frame_index = 0
                                player.patterns_done += 1
                            
                            if player.patterns_done >= player.patterns_to_do:
                                boss_current_state = "teleport_out"
                                player.patterns_done = 0 
                                player.boss_pattern_timer = 3000
                                
                        elif boss_current_state in ["attack1", "attack2", "attack3", "attack4", "attack5"]:
                            boss_current_state = "idle"
                            boss_frame_index = 0
                        else:
                            boss_frame_index = 0

            # (이 아래에 붙어있던 cutscene_stage 분기 및 보스 텔레포트 오토 모듈 타이머 연산, 투사체/이펙트 update(fx.update) 루프 등은 지우지 말고 그대로 흐르게 두시면 됩니다!)

        # 컷씬 제어 모듈 파이프라인 가드
        if cutscene_stage > 0:
            mage_frames = cutscene_mage_images.get(black_mage_state, [])
            if mage_frames:
                mage_frame_index = (mage_frame_index + 0.15) % len(mage_frames)

            if cutscene_stage == 1:
                player.x += 3.5  
                player.current_state = "run"
                player.frame_index = (player.frame_index + 0.15) % len(animations["run"])
                if player.x >= 350:  
                    player.change_state("idle")
                    cutscene_stage = 2
                    cutscene_timer = 2000  

            elif cutscene_stage == 2:
                cutscene_timer -= dt
                player.change_state("idle")
                if cutscene_timer <= 0:
                    cutscene_stage = 3
                    black_mage_state = "cut" 
                    mage_frame_index = 0     
                    cutscene_timer = 3000 
                    glitch_trigger = True

            elif cutscene_stage == 3:
                cutscene_timer -= dt
                if cutscene_timer <= 0:
                    cutscene_stage = 0 
                    game_stage = "BOSS"
                    player.target_scale = 0.75
                    boss_current_state = "teleport_in"
                    boss_frame_index = 0
                    
                    boss_x = boss_spawn_x
                    boss_y = 260
                    enemies = [Enemy(boss_x, boss_y, is_boss=True)]
                    
                    boss_platforms = [
                        BossPlatform(70, 420, 5),    
                        BossPlatform(770, 420, 5),   
                        BossPlatform(200, 310, 4),   
                        BossPlatform(640, 310, 4),   
                        BossPlatform(380, 200, 8),   
                        BossPlatform(140, 110, 3),   
                        BossPlatform(740, 110, 3)    
                    ]
                    glitch_trigger = False

        # ==================================================================
        # 🌟 [구조 전면 개편] 보스 5지점 텔레포트 AI 오토 모듈 및 타이머 스케줄러
        # ==================================================================
        if game_stage == "BOSS" and cutscene_stage == 0:
            if not hasattr(player, "boss_fixed_points"):
                player.boss_fixed_points = [
                    (WIDTH // 2, 260),               
                    (WIDTH // 2, 110),               
                    (WIDTH // 2, 380),               
                    (WIDTH // 2 - 250, 260),         
                    (WIDTH // 2 + 250, 260)          
                ]
                player.boss_current_point_idx = 0 
                player.boss_next_point_idx = -1
                player.boss_pattern_timer = 5000 # 패턴 간격 딜레이 스케줄링     
                player.boss_projectiles = []     
                player.boss_fires = []           
                player.boss_arms = []      
                player.last_pattern = 0          

            if player.slow_debuff_timer > 0:
                player.slow_debuff_timer -= dt
                if player.slow_debuff_timer <= 0:
                    player.movement_speed_modifier = 1.0 
                    player.slow_debuff_timer = 0

            # 🌟 보스가 완벽하게 공격 모션을 끝마치고 "idle" 상태로 쉬고 있을 때만 다음 패턴 쿨타임을 차감합니다.
            if boss_current_state == "idle":
                player.boss_pattern_timer -= dt

            # 패턴 타이머가 종료되었을 때, 다른 복잡한 캔슬 루프 없이 텔레포트 시퀀스로 부드럽게 이행
            if player.boss_pattern_timer <= 0 and boss_current_state == "idle":
                boss_current_state = "teleport_out"
                boss_frame_index = 0
                valid_indices = [i for i in range(5) if i != player.boss_current_point_idx]
                player.boss_next_point_idx = random.choice(valid_indices)
                player.boss_pattern_timer = 5000 
                
                # 연속 패턴 처리를 위한 스택 초기화 가드
                if hasattr(player, "patterns_done"):
                    player.patterns_done = 0

            # 🌟 [핵심 정상화]: 보스 상태와 완전히 독립적으로 투사체와 매니저들의 라이프 사이클을 업데이트합니다.
            for orb in player.boss_projectiles[:]:
                orb.update(player, boss_platforms, dt)
                if orb.is_dead: player.boss_projectiles.remove(orb)

            for fire in player.boss_fires[:]:
                fire.update(dt, player)
                if fire.is_dead: player.boss_fires.remove(fire)

            # 앞서 쓴 패턴들이 필드에 남아있어도 끊기지 않고 병렬로 끝까지 투다다다 실행됩니다!
            for arm in player.boss_arms[:]:
                arm.update(dt, player)
                if arm.is_dead: player.boss_arms.remove(arm)

        if game_stage == "BOSS" and player.is_grounded and player.y < GROUND_Y:
            on_platform = False
            player_feet = pygame.Rect(player.x - 12, player.y - 3, 24, 6)
            for plat in boss_platforms:
                if plat.rect.colliderect(player_feet):
                    on_platform = True
                    break
            if not on_platform:
                player.is_grounded = False

        # 대쉬 상태일 때는 수직 속도를 강제로 0으로 고정하여 중력에 낙하하지 않게 보정
        if player.current_state == "dash":
            player.y_velocity = 0

        player.update(keys, dt, enemies, game_effects)

        if game_stage == "PRACTICE" and player.x >= WIDTH - 60:
            current_scene = "LOADING"
            loading_timer = 1500 

        active_clones = [fx for fx in game_effects if fx.type == "release" and not fx.is_dead]
        
        if len(active_clones) >= 2:
            for i in range(len(active_clones)):
                for j in range(i + 1, len(active_clones)):
                    c1 = active_clones[i]
                    c2 = active_clones[j]
                    if c1.attack_hitbox.width > 0 and c2.attack_hitbox.width > 0:
                        if c1.attack_hitbox.colliderect(c2.attack_hitbox):
                            if not c1.has_triggered_slash and not c2.has_triggered_slash:
                                c1.has_triggered_slash = True
                                c2.has_triggered_slash = True
                                overlap = c1.attack_hitbox.clip(c2.attack_hitbox)
                                game_effects.append(Effect(overlap.centerx, overlap.centery, "slash", player.facing_right))

        if player.player_attack_hitbox.width > 0:
            for clone in active_clones:
                if clone.attack_hitbox.width > 0:
                    if player.player_attack_hitbox.colliderect(clone.attack_hitbox):
                        if not clone.has_triggered_slash:
                            clone.has_triggered_slash = True
                            overlap = player.player_attack_hitbox.clip(clone.attack_hitbox)
                            game_effects.append(Effect(overlap.centerx, overlap.centery, "slash", player.facing_right))

        for fx in game_effects[:]:
            damage_done = fx.update(dt, enemies, game_effects, player)
            if damage_done > 0:
                player.boss_current_hp = max(0, player.boss_current_hp - damage_done)
            if fx.is_dead:
                game_effects.remove(fx)

    # --------------------------------
    # 렌더링 파이프라인
    # --------------------------------
    if current_scene == "LOADING":
        screen.fill((10, 10, 14))
        font_load = pygame.font.SysFont(KOREAN_FONTS, 26, bold=True)
        load_surf = font_load.render("B O S S   S T A G E   L O A D I N G . . .", True, (0, 245, 255))
        load_rect = load_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(font_load.render("B O S S   S T A G E   L O A D I N G . . .", True, (0, 245, 255)), load_rect)

    elif current_scene == "GAME":
        screen.fill((10, 10, 12)) 

        if game_stage == "BOSS" or cutscene_stage == 3:
            screen.blit(boss_bg_actual_image, (0, 0))
            if cutscene_stage == 3 and random.random() < 0.1:
                glitch_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                glitch_mask.fill((120, 0, 150, 40))
                screen.blit(glitch_mask, (0, 0))
        else:
            for idx, layer in enumerate(bg_layers):
                speed_factor = 0.01 + ((idx + 1) * 0.05)
                parallax_offset = -int(player.x * speed_factor) % WIDTH
                screen.blit(layer, (parallax_offset - WIDTH, 0))
                screen.blit(layer, (parallax_offset, 0))

        for target_y in range(GROUND_Y, HEIGHT, TILE_DISPLAY_SIZE):
            for target_x in range(0, WIDTH + TILE_DISPLAY_SIZE, TILE_DISPLAY_SIZE):
                if target_y == GROUND_Y:
                    tile_index = 1 + ((target_x // TILE_DISPLAY_SIZE) % 3)
                else:
                    tile_index = 20  
                tile_index = max(0, min(tile_index, len(all_tiles) - 1))
                screen.blit(all_tiles[tile_index], (target_x, target_y))

        if game_stage == "BOSS":
            for plat in boss_platforms:
                plat.draw(screen)

        if game_stage == "BOSS" and cutscene_stage == 0:
            if hasattr(player, "boss_fires"):
                for fire in player.boss_fires:
                    fire.draw(screen)

        if game_stage == "BOSS" and cutscene_stage == 0:
            if hasattr(player, "boss_arms"):
                for arm in player.boss_arms:
                    arm.draw(screen)

        if cutscene_stage > 0 and black_mage_alpha > 0:
            current_mage_frames = cutscene_mage_images.get(black_mage_state, [])
            m_idx = min(int(mage_frame_index), len(current_mage_frames) - 1)
            mage_img = current_mage_frames[m_idx].copy()
            mage_img = pygame.transform.flip(mage_img, True, False)
            mage_img.set_alpha(black_mage_alpha)
            mage_rect = mage_img.get_rect(midbottom=(650, GROUND_Y + 210))
            screen.blit(mage_img, mage_rect)

        # 이 구역을 찾으세요!
        if game_stage == "PRACTICE":
            for enemy in enemies:
                enemy.draw(screen)

        # 🌟 [사망 모션 렌더링 가드 수정]: 보스가 살아있을 때나 죽어가는 연출 중일 때 모두 스프라이트를 정밀 출력합니다.
        if (game_stage == "BOSS" and cutscene_stage == 0) or boss_death_trigger:
            b_frames = boss_animations.get(boss_current_state, [])
            if b_frames:
                b_idx = min(int(boss_frame_index), len(b_frames) - 1)
                boss_img = b_frames[b_idx].copy()
                boss_rect = boss_img.get_rect(center=(boss_x, boss_y))
                screen.blit(boss_img, boss_rect)

        player.draw(screen)

        if game_stage == "BOSS" and cutscene_stage == 0:
            if hasattr(player, "boss_projectiles"):
                for orb in player.boss_projectiles:
                    orb.draw(screen, player.pulse_timer)

        for fx in game_effects:
            if hasattr(fx, "type") and fx.type == "visual_hit":
                if not fx.is_dead and fx.frames:
                    idx = min(int(fx.frame_index), len(fx.frames) - 1)
                    screen.blit(fx.frames[idx], fx.rect)
            else:
                fx.draw(screen)
        
        player.draw_vector_ui(screen)

        # 🌟 [추가] GAME CLEAR SCREEN 렌더링 파이프라인
        if current_scene == "CLEAR":
            screen.blit(title_image, (0, 0))
            panel = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            panel.fill((10, 5, 20, 200))
            screen.blit(panel, (0, 0))
            
            font_clear = pygame.font.SysFont(KOREAN_FONTS, 54, bold=True)
            font_sub = pygame.font.SysFont(KOREAN_FONTS, 20, bold=False)
            
            txt_clear = font_clear.render("VICTORY - BOSS DEFEATED", True, (0, 245, 255))
            txt_sub = font_sub.render("에스토리아 왕국이 해방되었습니다. 축하합니다!", True, (240, 220, 200))
            txt_info = font_sub.render("[ ESC 누르면 메인 메뉴로 이동 ]", True, (150, 140, 130))
            
            screen.blit(txt_clear, txt_clear.get_rect(center=(WIDTH//2, HEIGHT//2 - 60)))
            screen.blit(txt_sub, txt_sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
            screen.blit(txt_info, txt_info.get_rect(center=(WIDTH//2, HEIGHT//2 + 120)))
            
            if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                boss_death_trigger = False
                boss_death_timer = 0
                player.boss_current_hp = player.boss_max_hp
                current_scene = "TITLE"

        # 🌟 [추가] ESC PAUSE MENU 오버레이 UI 렌더링
        if current_scene == "GAME" and is_paused:
            dim_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim_surf.fill((20, 16, 14, 210))
            screen.blit(dim_surf, (0, 0))
            
            menu_w, menu_h = 320, 360
            menu_x, menu_y = (WIDTH // 2) - (menu_w // 2), (HEIGHT // 2) - (menu_h // 2)
            pygame.draw.rect(screen, (168, 147, 126), (menu_x, menu_y, menu_w, menu_h), 2, border_radius=8)
            pygame.draw.rect(screen, (45, 38, 35), (menu_x + 2, menu_y + 2, menu_w - 4, menu_h - 4), border_radius=6)
            
            font_phead = pygame.font.SysFont(KOREAN_FONTS, 28, bold=True)
            title_txt = font_phead.render("PAUSED", True, (255, 235, 205))
            screen.blit(title_txt, title_txt.get_rect(center=(WIDTH // 2, menu_y + 45)))
            
            btn_labels = ["재 시 작", "메 인 메 뉴", "게 임 종 료"]
            for idx, label in enumerate(btn_labels):
                b_y = menu_y + 110 + (idx * 70)
                is_sel = (pause_selected_idx == idx)
                bg_c = (55, 52, 60) if is_sel else (35, 28, 25)
                ln_c = (0, 245, 255) if is_sel else (30, 20, 15)
                tx_c = (0, 245, 255) if is_sel else (168, 147, 126)
                
                b_rect = pygame.Rect((WIDTH // 2) - 110, b_y, 220, 45)
                pygame.draw.rect(screen, ln_c, (b_rect.x - 2, b_rect.y - 2, 224, 49), border_radius=6)
                pygame.draw.rect(screen, bg_c, b_rect, border_radius=4)
                
                font_pbtn = pygame.font.SysFont(KOREAN_FONTS, 16, bold=True)
                l_surf = font_pbtn.render(label, True, tx_c)
                screen.blit(l_surf, l_surf.get_rect(center=b_rect.center))

    pygame.display.flip()