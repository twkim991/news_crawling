# news_crawling

뉴스 데이터(AG News, NewsAPI, SSAFY 뉴스, GDELT)를 수집·정제하고  
기술 뉴스만 추출해 **기술 카테고리 + 기술 스택(entity)** 로 분류한 뒤  
트렌드 리포트를 생성하는 파이프라인입니다.

---

## 개요

이 프로젝트는 다음 과정을 자동화합니다.

- 뉴스 데이터 수집 (NewsAPI, GDELT, SSAFY)
- 데이터 정규화 및 전처리
- 기술 뉴스 필터링 (이진 분류)
- 세부 기술 카테고리 분류
- 기술 스택(entity) 추출
- 주간/월간 트렌드 리포트 생성

---

## 전체 파이프라인 흐름

AG 학습
→ 뉴스 수집 (NewsAPI / GDELT / SSAFY)
→ 전처리 및 공통 스키마 정규화
→ 기술 기사 필터링 (이진 분류)
→ 불확실 기사 제거
→ 기술 카테고리 + stack/entity 분류
→ 트렌드 리포트 생성

---

## 프로젝트 구조

```text
news_crawling/
├─ src/
│ ├─ ag_pipeline.py
│ ├─ newsapi_pipeline.py
│ ├─ gdelt_pipeline.py
│ ├─ gdelt_analysis_pipeline.py
│ ├─ newsapi_analysis_pipeline.py
│ ├─ ssafy_news_pipeline.py
│ ├─ pipeline.py
│ └─ taxonomy.py
├─ data/
│ ├─ raw/
│ └─ processed/
├─ outputs/
├─ models/
├─ docs/
├─ requirements.txt
└─ README.md

```

## 환경 설정

의존성 설치

```text
python -m pip install -r requirements.txt
```

기본 import 검증

```text
python -c "import dotenv, joblib, numpy, pandas, requests, sentence_transformers, sklearn, torch; print('imports ok')"

```

## Quick Start

```bash
# 1. 의존성 설치
python -m pip install -r requirements.txt

# 2. AG News 이진분류기 학습
python -m src.ag_pipeline

# 3. NewsAPI 기사 수집 + 전처리
python -m src.newsapi_pipeline --max-pages 1

# 4. GDELT 기사 수집 + 전처리
python -m src.gdelt_pipeline \
  --start-datetime 20260301000000 \
  --end-datetime 20260302000000 \
  --max-files 96

# 5. 최종 통합 파이프라인 실행
python -m src.pipeline \
  --newsapi-input data/processed/newsapi_processed.csv \
  --gdelt-input data/processed/gdelt_processed.csv \
  --model models/ag_binary_logreg.joblib \
  --output-dir outputs \
  --metadata outputs/metadata.json
```

## taxonomy 구조

taxonomy는 2단 구조입니다.

- 상위: 기술 카테고리
- 하위: stack/entity

예시:

AI/ML → OpenAI, PyTorch
Cloud → AWS, Kubernetes
Frontend → React

출력 필드:

- tech_category
- primary_stack
- secondary_stack
- stack_matches

---

## 실행 가이드

| 목적            | 실행                                    |
| --------------- | --------------------------------------- |
| AG 모델 학습    | python -m src.ag_pipeline               |
| NewsAPI 수집    | python -m src.newsapi_pipeline          |
| GDELT 수집      | python -m src.gdelt_pipeline            |
| GDELT 분석      | python -m src.gdelt_analysis_pipeline   |
| NewsAPI 분석    | python -m src.newsapi_analysis_pipeline |
| SSAFY 처리      | python -m src.ssafy_news_pipeline       |
| 통합 파이프라인 | python -m src.pipeline                  |

---

## 상세 실행 예시

### AG 학습

```bash
python -m src.ag_pipeline
```

---

### NewsAPI 수집

```bash
python -m src.newsapi_pipeline \
  --query '(technology OR software OR developer OR programming OR cloud OR database OR "artificial intelligence" OR AI)' \
  --from-date 2026-03-01 \
  --to-date 2026-03-12 \
  --language en \
  --page-size 100 \
  --max-pages 1 \
  --raw-output data/raw/newsapi_raw.csv \
  --processed-output data/processed/newsapi_processed.csv
```

---

### GDELT 수집

```bash
python -m src.gdelt_pipeline \
  --start-datetime 20260301000000 \
  --end-datetime 20260302000000 \
  --max-files 96 \
  --processed-output data/processed/gdelt_processed.csv
```

추가 키워드 사용:

```bash
python -m src.gdelt_pipeline \
  --start-datetime 20260301000000 \
  --end-datetime 20260302000000 \
  --max-files 96 \
  --extra-keywords semicon gpu "edge ai"
```

---

### GDELT 분석

```bash
python -m src.gdelt_analysis_pipeline
```

---

### NewsAPI 분석

```bash
python -m src.newsapi_analysis_pipeline \
  --input data/processed/newsapi_processed.csv \
  --output-dir outputs
```

---

### SSAFY 처리

```bash
python -m src.ssafy_news_pipeline \
  --input data/raw/ssafy_dataset_news_2025_1st_half.csv \
  --model models/ag_binary_logreg.joblib \
  --output outputs/final_ssafy_tech_news.csv \
  --profile outputs/ssafy_profile.json \
  --tech-threshold 0.55 \
  --uncertainty-margin 0.08
```

---

### 통합 파이프라인

```bash
python -m src.pipeline \
  --newsapi-input data/processed/newsapi_processed.csv \
  --ssafy-input outputs/final_ssafy_tech_news.csv \
  --gdelt-input data/processed/gdelt_processed.csv \
  --model models/ag_binary_logreg.joblib \
  --output-dir outputs \
  --metadata outputs/metadata.json
```

## GDELT 수집 메모

- 15분 단위 GKG 파일 기반
- 파일 수 많음 → max-files 제한 권장
- 중복 기사 및 노이즈 존재
- 후처리 필터링 필요

---

## 주의사항

- GDELT 데이터는 노이즈가 많음
- NewsAPI는 요청 제한 존재
- SSAFY CSV는 컬럼 구조 변동 가능
- 대량 데이터 시 디스크 용량 확인 필요

---

## 주요 산출물

models/ag_binary_logreg.joblib

data/raw/newsapi_raw.csv
data/processed/newsapi_processed.csv

data/raw/gdelt_raw_gkg.csv
data/processed/gdelt_processed.csv

outputs/final_tech_news_all_sources.csv
outputs/tech_category_monthly_share.csv
outputs/tech_stack_monthly_share.csv
outputs/tech_emerging_keywords.csv
outputs/metadata.json

---

## 참고 문서

- docs/architecture_review.md
- docs/refactoring_plan.md
- docs/gdelt_source_strategy.md
- docs/lean_operating_roadmap.md

```

```
