PROJECT CONTEXT
This project is a production-grade golf system that includes:
- OCR-based data extraction from screen captures
- Backend API server for data storage and analysis
- Desktop GUI tools for calibration and operation
- Data pipelines for shot metrics and analytics

이 프로젝트는 골프 데이터 수집 및 분석을 위한 통합 시스템이다.
(OCR, 서버 API, 데스크톱 GUI, 데이터 파이프라인을 모두 포함한다)


GLOBAL DESIGN PRINCIPLES
- Determinism is critical: identical inputs must produce identical outputs.
- Data integrity is more important than feature speed.
- Silent failures are unacceptable.
- Every data transformation must be explicit and traceable.

결정론적 동작과 데이터 무결성을 최우선으로 한다.


LAYER SEPARATION (MANDATORY)
The codebase must be clearly separated into layers:

1. Capture / OCR Layer
   - Screen capture, image preprocessing, OCR
   - No business logic allowed
   - Output must be structured raw data with confidence metadata

2. Domain / Analysis Layer
   - Golf shot metrics, calculations, validation rules
   - No UI code, no OCR code, no network code

3. API / Server Layer
   - Data persistence, validation, versioned APIs
   - No OCR logic, no UI logic

4. GUI / Tooling Layer
   - Calibration tools, operator UI
   - No business logic, no direct database access

레이어 간 책임을 절대 섞지 않는다.


DATA FLOW RULES
- Data flows strictly in one direction:
  Capture → Domain → Server → Visualization
- No circular dependencies.
- No implicit data mutation.
- All coordinate systems and units must be explicitly documented.

데이터 흐름은 항상 단방향이며 명시적이어야 한다.


ERROR HANDLING (STRICT)
- OCR uncertainty must be propagated, never hidden.
- Network and IO errors must be logged and surfaced.
- Retry logic must be explicit and bounded.
- Any dropped or rejected data must be auditable.

OCR 신뢰도와 오류는 반드시 추적 가능해야 한다.


TESTING EXPECTATIONS
- Domain logic must be covered by deterministic unit tests.
- OCR components must have reproducible test fixtures.
- Integration tests must validate end-to-end data flow.

테스트는 결과 재현성을 기준으로 한다.


CHANGE POLICY
- OCR regions, screen resolutions, and formats WILL change.
- API versions must be backward compatible.
- Adding new metrics must not break existing data.

변경 가능성을 전제로 설계한다.


FINAL CHECK
If data correctness cannot be explained or reproduced,
the implementation is considered invalid.

데이터가 설명·재현되지 않으면 실패한 구현이다.


FILE MANAGEMENT POLICY (MANDATORY)
The project maintains three core client programs:
1. 좌표설정 (Calibration): calibrate_regions_gui.py
2. PC등록 (Registration): register_pc_gui.py
3. 샷 수집 (Shot Collector): shot_collector_gui.py

File cleanup rules:
- Delete unused/obsolete files immediately after refactoring
- Remove duplicate files (e.g., "복사본", "backup", "old")
- Remove CLI versions when GUI versions exist
- Remove unused build scripts
- Keep only one source file per program and its corresponding build script
- Remove root-level duplicates when client/core versions exist

Allowed files per program:
- 좌표설정: client/calibration/calibrate_regions_gui.py + build_calibrate_regions_gui.py
- PC등록: client/pc_register/register_pc_gui.py + build_register_pc_gui.py
- 샷 수집: client/shot_collector/shot_collector_gui.py + main.py + build_shot_collector_gui.py

Before committing or after major changes, verify:
- No duplicate source files exist
- No unused build scripts remain
- No backup/copy files (복사본, backup, old) exist
- Each program has exactly one source file and one build script

파일 정리는 지속적으로 유지하며, 혼동을 방지하기 위해 미사용 파일은 즉시 삭제한다.
---
name: golf-project-rules
description: This is a new rule
---

# Overview

Insert overview text here. The agent will only see this should they choose to apply the rule.
