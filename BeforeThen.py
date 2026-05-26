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
pygame.display.set_caption("2D 횡스크롤")

clock = pygame.time.Clock()

# --------------------------------
# 경로 함수
# --------------------------------
def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except AttributeError:
        base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

    return os.path.join(base_path, relative_path)

# --------------------------------
# 스프라이트 시트 로드
# --------------------------------
def load_sprite_sheet(
    path,
    frame_width,
    frame_height,
    scale=1
):

    sheet = pygame.image.load(
        resource_path(path)
    ).convert_alpha()

    frames = []

    for x in range(0, sheet.get_width(), frame_width):

        frame = pygame.Surface(
            (frame_width, frame_height),
            pygame.SRCALPHA
        )

        frame.blit(
            sheet,
            (0, 0),
            (x, 0, frame_width, frame_height)
        )

        # 픽셀아트 확대
        scaled_frame = pygame.transform.scale(
            frame,
            (
                frame_width * scale,
                frame_height * scale
            )
        )

        frames.append(scaled_frame)

    return frames
# --------------------------------
# 애니메이션 로드
# --------------------------------
animations = {

    "idle": load_sprite_sheet(
        "sprites/Player/_Idle.png",
        120,
        80,
        scale=2.5
    ),

    "run": load_sprite_sheet(
        "sprites/Player/_Run.png",
        120,
        80,
        scale=2.5
    ),
}

# --------------------------------
# 상태별 설정
# --------------------------------
state_data = {

    "idle": {
        "speed": 0,
        "animation_speed": 0.2
    },

    "run": {
        "speed": 5,
        "animation_speed": 0.3
    },

    "crouch": {
        "speed": 2,
        "animation_speed": 0.05
    }
}

# --------------------------------
# 플레이어 클래스
# --------------------------------
class Player:

    def __init__(self):

        # 위치
        self.x = 300
        self.y = 500

        # 방향
        self.facing_right = True

        # 현재 상태
        self.current_state = "idle"

        # 애니메이션 프레임
        self.frame_index = 0

    # ----------------------------
    # 상태 변경
    # ----------------------------
    def change_state(self, new_state):

        if self.current_state != new_state:

            self.current_state = new_state
            self.frame_index = 0

    # ----------------------------
    # 업데이트
    # ----------------------------
    def update(self, keys):

        moving = False

        current_speed = state_data[
            self.current_state
        ]["speed"]

        # 왼쪽 이동
        if keys[pygame.K_LEFT]:

            self.x -= current_speed

            self.facing_right = False
            moving = True

        # 오른쪽 이동
        if keys[pygame.K_RIGHT]:

            self.x += current_speed

            self.facing_right = True
            moving = True

        # 상태 처리
        if keys[pygame.K_DOWN]:

            self.change_state("crouch")

        elif moving:

            self.change_state("run")

        else:

            self.change_state("idle")

        # 현재 상태 애니메이션
        current_frames = animations[
            self.current_state
        ]

        animation_speed = state_data[
            self.current_state
        ]["animation_speed"]

        # 프레임 진행
        self.frame_index += animation_speed

        if self.frame_index >= len(current_frames):
            self.frame_index = 0

    # ----------------------------
    # 그리기
    # ----------------------------
    def draw(self, screen):

        current_frames = animations[
            self.current_state
        ]

        current_image = current_frames[
            int(self.frame_index)
        ]

        # 방향 반전
        if not self.facing_right:

            current_image = pygame.transform.flip(
                current_image,
                True,
                False
            )

        image_rect = current_image.get_rect(
            midbottom=(
                int(self.x),
                int(self.y)
            )
        )

        screen.blit(
            current_image,
            image_rect
        )

player = Player()

# --------------------------------
# 게임 루프
# --------------------------------
while True:

    dt = clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    
    player.update(keys)


    # --------------------------------
    # 화면 그리기
    # --------------------------------
    screen.fill((30, 30, 30))

    pygame.draw.rect(
        screen,
        (70, 120, 70),
        (0, 500, WIDTH, 100)
    )

    player.draw(screen)

    pygame.display.flip()
