# 🧠 Tech News Trend Analysis Pipeline

이 프로젝트는 다양한 뉴스 데이터(AG News, NewsAPI, GDELT 등)를 수집하여  
**기술 뉴스 추출 → 기술 분류 → 기술 스택 태깅 → 트렌드 분석**까지 수행합니다.

AG news, newsapi, gdelt project 등의 뉴스 데이터를 가지고 기술 관련 뉴스만 뽑아 어떤 기술 관련된 뉴스인지 분류한 뒤 이를 바탕으로 각 기술 스택의 뉴스 트랜드를 파악하는데 활용하기 위해 뉴스 데이터를 분류하고 정제하는 프로젝트

---

## 🔄 Pipeline Overview

```text
Raw Data
  ↓
Preprocess
  ↓
Tech Filtering
  ↓
Category Classification
  ↓
Stack Tagging
  ↓
Trend Aggregation
```

---

## 1. Data Collection

사용 데이터 소스

- AG News
- NewsAPI
- GDELT

GDELT의 경우 15분 단위 ZIP 파일을 다운로드한 뒤 내부 CSV를 파싱합니다.

주요 처리

- 원본 ZIP 다운로드
- TSV/CSV 파싱
- 필요한 컬럼만 유지
- 파일 메타데이터 유지

---

## 2. Data Preprocessing

목적: 노이즈 제거 + 분석용 텍스트 생성

주요 처리

- HTML 태그 제거
- URL 제거
- 공백 정리
- title / description / content 정리
- 분석용 `text` 컬럼 생성
- 중복 기사 제거

생성 컬럼

- `title`
- `description`
- `content`
- `text`
- `published_at`
- `source`

추가 필터

- 너무 짧은 기사 제거
- 의미 없는 제목 제거
- 중복 기사 제거

---

## 3. Tech News Filtering

목적: 전체 뉴스 중 기술 뉴스만 추출

방법

- Binary classifier 사용
- 기술 뉴스 여부 예측

출력 컬럼

- `tech_pred`
- `tech_score`
- `prediction_confidence`
- `is_uncertain`

추가 필터

- metadata 기반 필터
- 품질 필터
- 불확실 데이터 제거

---

## 4. Category Classification

기술 뉴스 → 대분류 카테고리 분류

카테고리 예시

- Programming Languages
- Frameworks
- Data & AI
- Databases & Storage
- Infrastructure & Cloud
- Data Engineering & Messaging
- DevOps & CI/CD
- Collaboration & Tools
- Other Tech

방법

1. 카테고리 정의를 embedding으로 변환
2. 기사 text를 embedding으로 변환
3. cosine similarity 계산
4. 가장 높은 카테고리 선택

사용 모델

- `intfloat/multilingual-e5-small`

출력 컬럼

- `tech_category`
- `tech_category_score`
- `tech_category_score_gap`
- `top2_category`
- `top2_score`

---

## 5. Stack Tagging

기사 내 기술 스택 추출

예시

- Python
- React
- AWS
- Kafka
- PostgreSQL
- Docker

동작 방식

- alias 기반 dictionary 구성
- regex 매칭
- 등장 횟수 기반 정렬

출력 컬럼

- `stack_labels`
- `stack_categories`
- `stack_subgroups`
- `primary_stack`
- `secondary_stack`
- `primary_stack_subgroup`
- `secondary_stack_subgroup`

---

## 6. Trend Analysis

시간 기준 기술 트렌드 분석

예시

```csv
period,tech_category,article_count
2026-03,Data & AI,1240
2026-03,Infrastructure & Cloud,980
```

집계 기준

- 월별 / 일별
- 카테고리별
- 스택별

---

## ⚡ Performance Optimization

속도 개선 전략

- content 길이 제한 (예: 700자)
- text 전체 길이 제한 (예: 2000자)
- 중복 text 제거
- embedding batch 처리
- similarity chunk 처리
- regex 통합 처리

---

## ⚠️ Important Notes

### GDELT Date Parsing

GDELT 날짜는 반드시 변환해야 합니다.

```python
pd.to_datetime(value, format="%Y%m%d%H%M%S", errors="coerce")
```

이 처리를 하지 않으면 다음과 같은 잘못된 결과가 나올 수 있습니다.

```text
1970-01
```

### Accuracy vs Speed

- 텍스트 길이를 줄이면 속도는 빨라짐
- 일부 정확도는 감소할 수 있음

현재 설정은 속도와 정확도의 균형 기준입니다.

---

## 📦 Final Output

최종 데이터는 다음 정보를 포함합니다.

- 기술 뉴스 여부 (`tech_pred`)
- 기술 카테고리 (`tech_category`)
- 기술 스택 (`primary_stack`)
- 하위 그룹 (`stack_subgroups`)
- 발행 시각 (`published_at`)
- 출처 (`source`)

---

## ✅ Summary

전체 흐름

1. 뉴스 수집
2. 텍스트 정제
3. 기술 뉴스 필터링
4. 카테고리 분류
5. 스택 태깅
6. 트렌드 분석
