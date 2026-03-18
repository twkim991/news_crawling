# 아키텍처/파이프라인 점검 리포트

## 1) 현재 구조 요약
- `ag_pipeline.py`: AG News(4-class)에서 Sci/Tech vs Non-Tech 이진분류기 학습.
- `newsapi_pipeline.py`: NewsAPI 수집/정규화/전처리.
- `pipeline.py`: 운영 데이터(NewsAPI/SSAFY)만 대상으로 이진분류 -> 테크 뉴스 추출 -> 카테고리 분류 -> stack/entity 매칭 -> 트렌드 리포트/메타데이터 생성.
- `common.py`: 스키마 보정, 전처리, 임베딩 인코딩, 세부 카테고리 분류, stack/entity annotation 로직.
- `taxonomy.py`: 상위 카테고리 + stack/entity alias taxonomy.
- `analytics.py`: 메타데이터, 점유율, 증감률, source bias, emerging keywords 리포트 생성.

## 2) 이번 단계에서 반영된 핵심 개선
1. **taxonomy를 기술 스택 중심으로 재설계**
   - 상위 카테고리 안에 실제 stack/entity alias를 두는 2단 구조로 전환.
2. **분류 결과에 stack/entity 축 추가**
   - `primary_stack`, `secondary_stack`, `stack_matches`, `stack_domain` 컬럼 생성.
3. **트렌드 분석 출력 확장**
   - 단순 기사 수 외에 점유율, 월간 growth, source bias, emerging keywords 리포트 추가.
4. **리팩터링 계획 문서 분리**
   - 우선순위별 실행 계획을 `docs/refactoring_plan.md`로 독립 문서화.

## 3) 현재 장점
- 운영 데이터에서 “카테고리”와 “실제 stack/entity”를 동시에 볼 수 있어 기술 스택 트렌드 분석 목적에 더 직접적으로 맞습니다.
- 단순 건수 외에 점유율과 성장률까지 제공해 기간 비교가 쉬워졌습니다.
- source bias와 emerging keywords를 함께 생성해 트렌드 해석 보조 지표가 늘어났습니다.

## 4) 남아있는 리스크
1. **stack/entity 매칭이 아직 규칙 기반**
   - alias 사전에 없는 표기 변형이나 문맥적 언급은 놓칠 수 있습니다.
2. **emerging keywords가 빈도 기반**
   - 의미 단위 엔티티 추출이 아니라 토큰 증가량 중심입니다.
3. **운영 평가셋 부재**
   - 실제 기사에 대한 category/stack 정답셋이 아직 부족합니다.
4. **GDELT 미연동**
   - 글로벌 이벤트/정책 분석을 위한 소스 확장이 남아 있습니다.

## 5) 다음 단계
- 운영 평가셋 구축
- stack/entity alias 사전 고도화
- event type 분류 추가
- GDELT ingestion 추가
