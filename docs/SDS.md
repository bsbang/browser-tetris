# Software Design Specification (SDS) - Browser Tetris v2.0

## 1. 단일 파일 모듈화 아키텍처 (`src/index.html`)
HTML5, CSS3(Flexbox/Grid 다크 네온 테마), ES6+ Vanilla JS를 단일 파일 내에 구조화하여 Cloud Shell Web Preview 및 GitHub Pages에서 즉시 실행 가능하도록 구성한다.

## 2. 핵심 모듈 명세
1. **`SoundEngine` 클래스**:
   - `AudioContext` 싱글톤 관리 (사용자 최초 입력 시 Resume).
   - `play(type)` 메서드: `move`, `rotate`, `drop`, `clear`, `gameover` 별 주파수(Hz) 및 파형(`square`, `triangle`, `sawtooth`) 제어.
2. **`TetrisGame` 상태 및 렌더링**:
   - 메인 캔버스(`#board`, 240x480 또는 300x600 스케일링) 및 서브 캔버스(`#next`, 100x100).
   - `getGhostY()`: 현재 블록 복사본의 Y 좌표를 충돌 직전까지 증가시켜 고스트 블록 렌더링 좌표 산출.
   - `hardDrop()`: 블록을 `getGhostY()` 위치로 즉시 이동 후 고정(`merge`), 추가 점수 부여.
3. **UI/UX 레이아웃**:
   - 상단/우측: `Score`, `High Score`, `Level`, `Lines` 대시보드 및 `Pause`, `Sound Toggle` 버튼.
   - 하단: 모바일 터치 이벤트(`touchstart`/`click`) 바인딩 컨트롤 버튼 그리드.

## 3. 출력 제약 사항 (Agent Output Rule)
- 에이전트가 코드를 생성할 때는 마크다운 설명 없이 즉시 실행 가능한 완전한 `<!DOCTYPE html>...</html>` 전체 코드만 반환해야 한다.
