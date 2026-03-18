# 우선순위별 리팩터링 계획

## 목표
이 문서는 뉴스 분류/정제 프로젝트를 **기술 스택 트렌드 분석용 운영 파이프라인**으로 고도화하기 위한 우선순위별 실행 계획을 분리해 정리합니다.

## P0 — 분류 결과를 분석 가능한 구조로 고정
1. **운영 평가셋 구축**
   - 실제 NewsAPI/SSAFY 기사 300~1000건 라벨링
   - 라벨: `is_tech`, `tech_category`, `primary_stack`, `secondary_stack`, `event_type`
2. **taxonomy 운영 기준 확정**
   - 상위 카테고리와 stack/entity alias 사전 버전 관리
3. **불확실 기사 검수 플로우 추가**
   - `is_uncertain == True` 샘플을 별도 검수 큐로 저장

## P1 — 분석용 출력 고도화
1. **점유율/증감률 리포트 자동화**
   - 주간/월간 category share, stack share, growth report
2. **source bias 모니터링**
   - source별 카테고리 쏠림과 global lift 계산
3. **emerging keyword 검출 개선**
   - 현재 빈도 기반에서 entity-aware keyword extraction으로 확장

## P2 — 파이프라인 구조 정리
1. **패키지화**
   - `src/news_trend/training`, `ingestion`, `inference`, `analytics`, `evaluation`
2. **설정 분리**
   - taxonomy 버전, 모델 경로, threshold, 날짜 범위를 YAML/ENV로 분리
3. **입력 스키마 검증 강화**
   - 컬럼 존재 여부를 넘어서 타입/결측률까지 검증

## P3 — 소스 및 분석 범위 확장
1. **GDELT ingestion 추가**
   - 글로벌 이벤트성 뉴스 수집
2. **벤더/제품 엔티티 추출**
   - OpenAI, AWS, Kubernetes 같은 stack/entity를 추세 분석 축으로 분리
3. **event type 분류기 추가**
   - 릴리스, 보안 사고, 투자, 정책, 실적, 인수합병 등

## 완료 기준
- 운영 평가셋 기준 category/stack 성능 지표 확보
- 주간/월간 트렌드 리포트 자동 생성
- source bias/emerging keyword 리포트 자동 생성
- taxonomy와 모델 버전을 메타데이터에 기록
