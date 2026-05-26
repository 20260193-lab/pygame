# 2D 횡스크롤 게임 개발 일지

## 1. 기본 플레이어 이동 구현
- Pygame 기반 2D 횡스크롤 프로젝트 시작
- 방향키를 이용한 좌우 이동 구현
- Idle / Run 상태 분리

---

## 2. 상대경로 기반 이미지 로딩
- Base64 방식 대신 파일 기반 이미지 사용
- `resource_path()` 함수 제작
- PyInstaller export 대응 구조 적용

```python
resource_path("sprites/Player/_Idle.png")