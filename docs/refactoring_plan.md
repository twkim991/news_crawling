# 우선순위별 리팩터링 계획

## 목표
이 문서는 뉴스 분류/정제 프로젝트를 **기술 스택 트렌드 분석용 운영 파이프라인**으로 고도화하기 위한 우선순위별 실행 계획을 분리해 정리합니다.

## P0 — 분류 결과를 분석 가능한 구조로 고정
1. **taxonomy 운영 기준 확정**
   - 상위 카테고리와 stack/entity alias 사전 버전 관리
2. **공통 전처리/임베딩/분류 모듈 분리**
   - 공통 로직을 CLI 스크립트에서 분리하고 재사용 가능한 구조로 정리
3. **불확실 기사 후처리 분리**
   - `is_uncertain`은 평가 목적이 아니라 운영상 제외/보류 플래그로만 사용

## P1 — 분석용 출력 고도화
1. **점유율/증감률 리포트 자동화**
   - 주간/월간 category share, stack share, growth report
2. **source bias 모니터링**
   - source별 카테고리 쏠림과 global lift 계산
3. **emerging keyword 검출 개선**
   - 현재 빈도 기반에서 entity-aware keyword extraction으로 확장

## P2 — 파이프라인 구조 정리
1. **패키지화**
   - `src/news_trend/training`, `ingestion`, `inference`, `analytics`, `reporting`
2. **설정 분리**
   - taxonomy 버전, 모델 경로, threshold, 날짜 범위를 YAML/ENV로 분리
3. **입력 스키마 검증 강화**
   - 컬럼 존재 여부를 넘어서 타입/결측률까지 검증

## P3 — 소스 및 분석 범위 확장
1. **GDELT 운영 안정화**
   - 글로벌 이벤트성 뉴스 수집 파이프라인 운영 기준 정리
2. **벤더/제품 엔티티 추출**
   - OpenAI, AWS, Kubernetes 같은 stack/entity를 추세 분석 축으로 분리
3. **event type 분류기 추가**
   - 릴리스, 보안 사고, 투자, 정책, 실적, 인수합병 등

## 프로젝트 원칙
- 이 프로젝트는 정답셋 기반 성능 평가를 목표로 하지 않습니다.
- 목적은 뉴스 소스 정제, 기술 카테고리/스택 구조화, 트렌드 탐색 자동화입니다.

## 완료 기준
- 주간/월간 트렌드 리포트 자동 생성
- source bias/emerging keyword 리포트 자동 생성
- taxonomy와 모델 버전을 메타데이터에 기록
- 공통 로직이 모듈화되어 소스별 파이프라인에서 재사용 가능
