# Browser Tetris v2.0 (HTML5 Canvas & Web Audio API)

모던 다크 네온 테마와 웹 오디오 신디사이저, 고스트 피스, 모바일 온스크린 터치 컨트롤을 지원하는 완벽한 단일 파일(`src/index.html`) 기반의 HTML5 테트리스 게임입니다.

---

## 🚀 주요 기능 (Key Features)
1. **Core Tetris Engine (FR-01)**: 10x20 그리드, 7종 테트로미노 표준 색상, 벽 차기(Wall Kick) 충돌 보정, 줄 제거 및 게임오버 판정.
2. **Ghost & Next Piece (FR-02)**: 현재 블록이 착지할 위치를 실시간으로 보여주는 반투명 Ghost Piece와 우측 Next Block 미리보기 캔버스.
3. **Score, Level & Storage (FR-03)**: 다중 줄 제거 가중치 점수, 10줄 제거마다 레벨업 및 낙하 속도 가속, `localStorage` 최고 점수 영구 저장.
4. **Web Audio SFX (FR-04)**: `AudioContext` 주파수 합성을 이용한 타격감 넘치는 레트로 효과음 및 음소거(Mute) 토글.
5. **Cross-Platform Controls (FR-05)**:
   - **PC 키보드**: 방향키(좌우 이동, 소프트드롭), Up/W/Q(회전), Space(하드드롭), P(일시정지), R(재시작).
   - **모바일/태블릿**: 반응형 온스크린 터치 컨트롤 패드(`◀`, `▼`, `▶`, `↻`, `DROP`).

---

## 🛠️ 실행 방법 (Running Locally)
1. 저장소를 클론하거나 다운로드합니다.
2. 브라우저에서 `src/index.html` 파일을 직접 엽니다 (더블 클릭 또는 브라우저로 드래그 앤 드롭).
   * 또는 VS Code의 **Live Server** 확장 프로그램을 사용하여 `src/index.html`을 실행하세요.

---

## 🌐 GitHub Pages 자동 배포
본 프로젝트는 `.github/workflows/deploy.yml` 워크플로우를 통해 `src/` 디렉터리의 정적 파일을 GitHub Pages로 자동 배포합니다.
* Repository **Settings > Pages**에서 Build and deployment source를 **GitHub Actions**로 설정하면 즉시 배포됩니다.
