# Software Requirements Specification (SRS) - Browser Tetris v2.0

## 1. 목적 및 범위
외부 라이브러리나 에셋(이미지, 오디오 파일) 의존성 없이 단일 파일(`src/index.html`)로 완벽히 동작하는 모던 HTML5 Canvas 테트리스 게임을 구축한다.

## 2. 기능 요구사항 (Functional Requirements)
- **FR-01 (Core Engine)**: 10x20 그리드, 7종 테트로미노(I, J, L, O, S, T, Z) 표준 색상, 회전 및 벽 차기(Wall Kick) 충돌 보정, 줄 제거 및 게임오버 판정.
- **FR-02 (Ghost & Next Piece)**: 현재 블록이 바닥에 착지할 위치를 반투명하게 표시하는 Ghost Piece 렌더링 및 우측 사이드 패널에 다음 블록(Next Piece) 미리보기 캔버스 구현.
- **FR-03 (Score, Level & Storage)**: 동시 제거 줄 수(1~4줄)에 비례하는 가중치 점수 계산, 10줄 제거마다 Level 상승 및 낙하 속도(Drop Interval) 단축, `localStorage`를 통한 최고 점수(High Score) 영구 저장.
- **FR-04 (Web Audio SFX)**: `window.AudioContext` 오실레이터 주파수 합성을 활용하여 블록 이동, 회전, 소프트/하드 드롭, 라인 클리어, 게임오버 시 각기 다른 레트로 효과음 출력 (Mute 토글 지원).
- **FR-05 (Cross-Platform Controls)**:
  - PC 키보드: 방향키(이동/소프트드롭), Up/W/Q(회전), Space(하드드롭), P(일시정지), R(재시작).
  - 모바일/태블릿: 화면 하단에 반응형 온스크린 터치 컨트롤 패드(`◀`, `▼`, `▶`, `↻`, `DROP`) 배치.
