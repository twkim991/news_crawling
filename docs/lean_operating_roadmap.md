# 저비용 운영 로드맵

## 배경
- 이 프로젝트의 목표는 여러 뉴스 소스에서 기술 관련 뉴스만 추출하고, 기술 카테고리 및 기술 스택(entity)를 분류한 뒤 트렌드 분석에 활용하는 것입니다.
- 다만 시간과 개발 인력이 매우 제한적이므로, **수작업 운영 평가셋 구축과 정확도 측정은 포기**합니다.
- 따라서 로드맵의 방향은 **정확도 최적화**가 아니라 **트렌드 왜곡을 줄이는 저비용 운영 파이프라인** 구축입니다.

## 운영 원칙
1. **정확도보다 노이즈 억제**
   - 명백한 비기술 기사, 재배포/광고성 기사, 중복 기사를 최대한 제거합니다.
2. **모델 고도화보다 규칙/사전 보강**
   - taxonomy alias, 품질 필터, 이벤트 키워드 규칙 중심으로 개선합니다.
3. **정답셋 대신 운영 품질 지표**
   - `uncertain_ratio`, `other_tech_ratio`, `unspecified_stack_ratio`, 날짜 파싱 성공률 등으로 파이프라인 상태를 모니터링합니다.
4. **해석 가능한 리포트 우선**
   - category/stack/event 축에서 사람이 읽기 쉬운 리포트를 우선 제공합니다.
5. **새 소스 도입은 늦게**
   - GDELT 같은 신규 소스는 현재 소스로 충분하지 않을 때만 도입합니다.

## 우선순위별 계획

### P0 — 최소 안정화
목표: **트렌드 결과를 심하게 왜곡하는 노이즈를 줄인다.**

1. 입력 품질/노이즈 필터 강화
   - 짧은 기사, 광고성 문구, 재배포 문구 제거
   - 날짜 파싱 실패, source 누락 등을 메타데이터에 기록
2. 불확실 기사 적극 제외
   - `is_uncertain` 기사를 최종 산출물에서 제거하고 별도 CSV로 저장
3. 중복 기사 제거 강화
   - URL/text 중복 외에 정규화 title 기반 dedup 추가
4. taxonomy coverage 개선
   - `Other Tech`, `Unspecified` 비율을 줄이도록 alias 사전 확장
5. 운영 품질 지표 추가
   - 실행 시 quality metrics를 metadata에 기록

### P1 — 해석 가능한 트렌드 강화
목표: **정확도는 몰라도 결과를 읽고 해석할 수 있게 만든다.**

1. 규칙 기반 event type 분류 추가
   - 출시, 보안사고, 투자, 규제, 실적, 제휴, 인수 등
2. stack 매칭 고도화
   - `mentioned_stacks`와 `primary_stack` 분리
   - 제목/설명/본문 위치 기반 가중치 추가
3. emerging keyword → emerging entity 중심 전환
   - token보다 stack/vendor/product/entity 급상승 리포트 우선
4. source bias 리포트 확장
   - source x stack, source x event_type 리포트 추가

### P2 — 저비용 운영성 확보
목표: **사람이 적어도 유지 가능한 실행 구조를 만든다.**

1. 설정 분리
   - query, 날짜 범위, threshold, output 경로를 코드 밖으로 분리
2. 운영 건강 상태 리포트 강화
   - source concentration, duplicate drop ratio, parse success ratio 추가
3. 구조 정리는 최소한만
   - 대규모 패키지화보다 공통 함수/출력 규칙 정리 우선
4. 신규 소스는 필요할 때만
   - GDELT는 P0/P1 완료 후 coverage 문제가 있을 때 검토

### P3 — 여력이 생기면
- taxonomy entity type 분리
- 다국어 분류 고도화
- NER/entity linking 기반 stack 추출
- supervised event classifier
- 대규모 패키지 구조 개편

## 바로 실행할 추천 작업
1. 공통 전처리 노이즈 제거 강화
2. 불확실 기사 별도 저장
3. normalized title dedup 추가
4. metadata 품질 지표 확대
5. taxonomy alias 확장

## 하지 않을 일
- 수작업 운영 평가셋 구축
- 정식 precision/recall/F1 측정 체계
- 고비용 모델 튜닝 프로젝트

## 성공 기준
- 최종 리포트에 명백한 노이즈가 줄어든다.
- 같은 사건의 중복 집계가 감소한다.
- `Other Tech`, `Unspecified` 비율이 관리 가능 수준으로 유지된다.
- 운영 메타데이터만으로도 파이프라인 상태 이상 여부를 빠르게 파악할 수 있다.
