# R10unds 빌드 및 배포 메모

## 1. 상대경로와 절대경로

### 상대경로
```python
./sounds/bgm.mp3
```

- 현재 실행 중인 파일 위치를 기준으로 찾음
- 프로젝트 이동 시에도 폴더 구조만 유지되면 작동
- 협업/배포에 적합

---

### 절대경로
```python
C:/Users/HOSEO/Desktop/game/sounds/bgm.mp3
```

- 컴퓨터의 실제 위치를 직접 지정
- 다른 컴퓨터에서는 거의 대부분 깨짐
- 배포용 게임에서는 보통 사용하지 않음

---

# 2. PyInstaller 설치

Thonny Shell 또는 CMD에서:

```bash
pip install pyinstaller
```

설치 확인:

```bash
pyinstaller --version
```

---

# 3. Thonny에서 Shell 열기

## 방법

- 상단 메뉴 → 보기(View)
- Shell 체크

또는:

```text
Ctrl + T
```

---

# 4. 빌드 명령어

## 기본 빌드

```bash
pyinstaller --onefile --windowed --name R10unds --icon=icon.ico --add-data "sounds;sounds" R10unds.py
```

---

# 5. 빌드 옵션 의미

## --onefile

```text
exe 하나로 압축
```

### 결과

```text
R10unds.exe
```

---

## --windowed

```text
콘솔(cmd) 창 숨김
```

### 있음

- 게임창만 뜸

### 없음

- 게임창 + 검은 콘솔창 같이 뜸

---

## --name R10unds

```text
최종 exe 이름 설정
```

결과:

```text
R10unds.exe
```

---

## --icon=icon.ico

```text
exe 아이콘 설정
```

주의:

- icon.ico 파일이 실제로 존재해야 함
- py 파일과 같은 폴더에 두는 게 가장 편함

---

## --add-data "sounds;sounds"

```text
sounds 폴더를 exe 내부에도 포함시킴
```

### 왼쪽

원본 폴더

### 오른쪽

exe 내부에서의 이름

즉:

```text
원본 sounds 폴더를
exe 내부에서도 sounds 이름으로 저장
```

---

# 6. resource_path 함수

PyInstaller의 onefile 모드에서는 실행 시 임시 폴더에 압축 해제됨.

그래서 일반 상대경로:

```python
./sounds/bgm.mp3
```

만 사용하면 exe에서 파일을 못 찾을 수 있음.

이를 해결하기 위한 함수:

```python
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
```

---

# 7. 사운드 로드 수정

## 기존 코드

```python
pygame.mixer.music.load("./sounds/bgm.mp3")

self.hit_sound = pygame.mixer.Sound("./sounds/hit.wav")
self.clear_sound = pygame.mixer.Sound("./sounds/clear.mp3")
self.gameover_sound = pygame.mixer.Sound("./sounds/gameover.mp3")
```

---

## 수정 코드

```python
pygame.mixer.music.load(resource_path("sounds/bgm.mp3"))

self.hit_sound = pygame.mixer.Sound(resource_path("sounds/hit.wav"))
self.clear_sound = pygame.mixer.Sound(resource_path("sounds/clear.mp3"))
self.gameover_sound = pygame.mixer.Sound(resource_path("sounds/gameover.mp3"))
```

---

# 8. main 부분

이 부분은 그대로 유지:

```python
if __name__ == "__main__":
    game = Game()
    game.run()
```

---

# 9. 아이콘 오류 해결

## 오류

```text
FileNotFoundError: Icon input file not found
```

## 원인

```text
icon.ico 파일이 없음
```

## 해결

- icon.ico 파일 생성
- py 파일과 같은 위치에 배치

또는:

```bash
--icon 제거
```

---

# 10. sounds 폴더 오류

## 오류

```text
FileNotFoundError: 지정된 경로를 찾을 수 없습니다: 'sounds'
```

## 원인

exe 내부에서는 경로가 달라짐.

## 해결

resource_path 사용.

---

# 11. PermissionError 해결

## 오류

```text
PermissionError: 액세스가 거부되었습니다
```

## 원인

기존 exe가 실행 중.

## 해결

- 게임 종료
- 작업 관리자에서 R10unds.exe 종료
- 다시 빌드

---

# 12. build/dist 정리

빌드 꼬였을 때:

```bash
rmdir /s /q build
rmdir /s /q dist
del R10unds.spec
```

이후 다시 빌드.

---

# 13. exe 위치

빌드 완료 후:

```text
dist/R10unds.exe
```