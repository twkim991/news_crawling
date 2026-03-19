# news_crawling

뉴스 데이터(AG News, NewsAPI, SSAFY 뉴스, GDELT)를 수집/정제하고, 기술 뉴스만 추출해 **기술 카테고리 + 기술 스택(entity)** 로 분류한 뒤 기술 스택 트렌드 리포트를 생성하는 파이프라인입니다.

## 환경 설정
이 저장소의 실행 코드는 모두 Python으로 작성되어 있습니다. 따라서 의존성 설치와 런타임 검증도 Python 명령으로 직접 수행합니다.

```bash
python -m pip install -r requirements.txt
```

설치 후 아래 명령으로 핵심 Python 의존성이 모두 준비되었는지 확인할 수 있습니다.

```bash
python -c "import dotenv, joblib, numpy, pandas, requests, sentence_transformers, sklearn, torch"
```

## 파이프라인 개요
1. **AG 학습 (`src/ag_pipeline.py`)**
   - AG News를 기반으로 Sci/Tech vs Non-Tech 이진분류기 학습
2. **NewsAPI 수집/전처리 (`src/newsapi_pipeline.py`)**
   - NewsAPI에서 기사 수집 후 공통 스키마로 정규화
3. **GDELT 수집/전처리 (`src/gdelt_pipeline.py`)**
   - GDELT raw GKG 파일을 `masterfilelist.txt` 기준으로 내려받아 기술 기사 후보를 선별하고 공통 스키마로 정규화
4. **GDELT 단독 분석 (`src/gdelt_analysis_pipeline.py`)**
   - 전처리된 GDELT 기사만 대상으로 세부 기술 카테고리/트렌드 리포트를 생성
5. **운영 추론 + 트렌드 생성 (`src/pipeline.py`)**
   - NewsAPI/SSAFY/GDELT 운영 데이터 전처리
   - 이진분류기 추론으로 tech 기사 필터링
   - 불확실 기사 제거 후 세부 기술 카테고리 분류
   - stack/entity 매칭(`primary_stack`, `secondary_stack`) 추가
   - 주간/월간 카테고리 점유율, stack 점유율, source bias, emerging keywords 리포트 생성
6. **SSAFY 한국어 뉴스 분석 (`src/ssafy_news_pipeline.py`)**
   - CSV 컬럼 구조 자동 매핑(한/영 컬럼 대응, `|` 구분자/멀티라인 본문 대응)
   - 스키마/결측 비율 프로파일 JSON 생성
   - 이진분류 확률 기반 `tech_score`, `is_uncertain` 추가
   - 품질 플래그 기반 저품질/불확실 기사 제거 후 제로샷 세부분류
7. **NewsAPI 단독 분석 (`src/newsapi_analysis_pipeline.py`)**
   - 전처리된 NewsAPI 기사만 대상으로 세부 기술 카테고리 분류와 트렌드 리포트 생성

## taxonomy
- `src/taxonomy.py`는 이제 **상위 기술 카테고리 + stack/entity alias** 구조를 가집니다.
- 예: `AI/ML > OpenAI`, `Cloud & Infrastructure > AWS`, `Frameworks & Libraries > React`
- 분류 결과에는 `tech_category`와 별도로 `primary_stack`, `secondary_stack`, `stack_matches`가 추가됩니다.

## 핵심 디렉터리
- `src/`: 파이프라인 소스 코드 (`gdelt_pipeline.py` 포함)
- `data/raw`: 원천 데이터
- `data/processed`: 전처리 데이터
- `outputs/`: 최종 결과 CSV, 트렌드 리포트, 메타데이터
- `docs/architecture_review.md`: 현재 구조 점검 및 개선 제안
- `docs/refactoring_plan.md`: 우선순위별 리팩터링 계획

## 목적별 실행 가이드
아래 표만 보면 **무슨 목적일 때 어떤 파일을 실행해야 하는지** 빠르게 판단할 수 있습니다.

| 목적 | 실행 파일 | 언제 쓰는지 | 대표 출력물 |
| --- | --- | --- | --- |
| AG News로 기술/비기술 이진분류기 학습 | `src/ag_pipeline.py` | 처음 모델을 만들거나 재학습할 때 | `models/ag_binary_logreg.joblib` |
| NewsAPI 기사 수집 + 전처리 | `src/newsapi_pipeline.py` | 외부 영문 기술 뉴스 수집본을 만들 때 | `data/raw/newsapi_raw.csv`, `data/processed/newsapi_processed.csv` |
| GDELT GKG 수집 + 전처리 | `src/gdelt_pipeline.py` | 기간 단위 대량 글로벌 기술 뉴스 후보를 만들 때 | `data/raw/gdelt_raw_gkg.csv`, `data/processed/gdelt_processed.csv` |
| GDELT 데이터만 세부 분석 | `src/gdelt_analysis_pipeline.py` | 이미 전처리된 GDELT 기사에 카테고리/트렌드 분석만 하고 싶을 때 | `outputs/tech_*.csv` |
| NewsAPI 데이터만 세부 분석 | `src/newsapi_analysis_pipeline.py` | 이미 전처리된 NewsAPI 기사에 카테고리/트렌드 분석만 하고 싶을 때 | `outputs/newsapi_*.csv` |
| SSAFY 한국어 뉴스 정제 + 분류 | `src/ssafy_news_pipeline.py` | 한국어 CSV를 품질 필터링 후 기술 뉴스만 뽑고 싶을 때 | `outputs/final_ssafy_tech_news.csv`, `outputs/ssafy_profile.json` |
| 여러 소스를 합쳐 운영용 최종 결과 생성 | `src/pipeline.py` | NewsAPI/SSAFY/GDELT를 통합해 최종 기술 뉴스와 리포트를 만들 때 | `outputs/final_tech_news_all_sources.csv`, `outputs/metadata.json` |

## 파이썬 콘솔(또는 REPL)에서 바로 실행하는 방법
아래 코드는 **파이썬 콘솔창에 그대로 복사/붙여넣기**할 수 있게 작성했습니다. 공통적으로 저장소 루트(`news_crawling`)에서 Python을 실행했다고 가정합니다.

### 0) 공통 실행 헬퍼
한 번만 붙여넣어 두면 아래 예시들을 그대로 사용할 수 있습니다.

```python
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path.cwd()
print(f"working dir = {ROOT}")

def run_module(module_name, *args):
    cmd = [sys.executable, "-m", module_name, *map(str, args)]
    print("\n$", " ".join(cmd))
    subprocess.run(cmd, check=True)
```

### 1) 목적: 의존성 설치 및 기본 점검
처음 저장소를 받았을 때 가장 먼저 실행합니다.

```python
import sys, subprocess

subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
subprocess.run([
    sys.executable,
    "-c",
    "import dotenv, joblib, numpy, pandas, requests, sentence_transformers, sklearn, torch; print('imports ok')",
], check=True)
```

### 2) 목적: AG News 이진분류기 학습
`data/raw/train.csv`, `data/raw/test.csv`가 준비되어 있고 `models/ag_binary_logreg.joblib`를 새로 만들고 싶을 때 사용합니다.

실행 파일: `src/ag_pipeline.py`

```python
run_module("src.ag_pipeline")
```

### 3) 목적: NewsAPI 기사 수집 + 전처리
NewsAPI 키가 필요합니다. `.env` 또는 환경변수에 `newsapi_key`가 있어야 합니다.

실행 파일: `src/newsapi_pipeline.py`

```python
import os

os.environ["newsapi_key"] = "YOUR_NEWSAPI_KEY"
run_module(
    "src.newsapi_pipeline",
    "--query", '(technology OR software OR developer OR programming OR cloud OR database OR "artificial intelligence" OR AI)',
    "--from-date", "2026-03-01",
    "--to-date", "2026-03-12",
    "--language", "en",
    "--page-size", 100,
    "--max-pages", 1,
    "--raw-output", "data/raw/newsapi_raw.csv",
    "--processed-output", "data/processed/newsapi_processed.csv",
)
```

### 4) 목적: GDELT 기간 수집 + 전처리
기간 단위로 GDELT GKG 파일을 내려받아 대량 후보 기사를 만들 때 사용합니다.

실행 파일: `src/gdelt_pipeline.py`

```python
run_module(
    "src.gdelt_pipeline",
    "--start-datetime", "20260301000000",
    "--end-datetime", "20260302000000",
    "--max-files", 96,
    "--processed-output", "data/processed/gdelt_processed.csv",
)
```

추가 키워드로 후보군을 넓히고 싶다면:

```python
run_module(
    "src.gdelt_pipeline",
    "--start-datetime", "20260301000000",
    "--end-datetime", "20260302000000",
    "--max-files", 96,
    "--extra-keywords", "semicon", "gpu", "edge ai",
    "--processed-output", "data/processed/gdelt_processed.csv",
)
```

### 5) 목적: GDELT 전처리 결과만 분석
이미 `data/processed/gdelt_processed.csv`가 있을 때 세부 카테고리와 트렌드 리포트만 생성합니다.

실행 파일: `src/gdelt_analysis_pipeline.py`

```python
run_module("src.gdelt_analysis_pipeline")
```

### 6) 목적: NewsAPI 전처리 결과만 분석
이미 `data/processed/newsapi_processed.csv`가 있을 때 NewsAPI 기사만 따로 세부 분석합니다.

실행 파일: `src/newsapi_analysis_pipeline.py`

```python
run_module(
    "src.newsapi_analysis_pipeline",
    "--input", "data/processed/newsapi_processed.csv",
    "--output-dir", "outputs",
)
```

### 7) 목적: SSAFY 한국어 뉴스 CSV 정제 + 분류
한글 컬럼명/영문 컬럼명이 섞여 있어도 자동으로 매핑해서 처리합니다.

실행 파일: `src/ssafy_news_pipeline.py`

```python
run_module(
    "src.ssafy_news_pipeline",
    "--input", "data/raw/ssafy_dataset_news_2025_1st_half.csv",
    "--model", "models/ag_binary_logreg.joblib",
    "--output", "outputs/final_ssafy_tech_news.csv",
    "--profile", "outputs/ssafy_profile.json",
    "--tech-threshold", 0.55,
    "--uncertainty-margin", 0.08,
)
```

### 8) 목적: NewsAPI + SSAFY + GDELT를 합쳐 운영용 최종 결과 만들기
최종 기술 뉴스, 불확실 기사, 메타데이터, 트렌드 리포트를 한 번에 생성할 때 사용합니다.

실행 파일: `src/pipeline.py`

```python
run_module(
    "src.pipeline",
    "--newsapi-input", "data/processed/newsapi_processed.csv",
    "--ssafy-input", "outputs/final_ssafy_tech_news.csv",
    "--gdelt-input", "data/processed/gdelt_processed.csv",
    "--model", "models/ag_binary_logreg.joblib",
    "--output-dir", "outputs",
    "--metadata", "outputs/metadata.json",
    "--tech-threshold", 0.55,
    "--uncertainty-margin", 0.08,
)
```

### 9) 목적: 특정 입력만 골라서 운영 파이프라인 실행
운영 파이프라인은 최소 1개 입력만 있어도 실행할 수 있습니다.

#### 9-1) NewsAPI만 사용
```python
run_module(
    "src.pipeline",
    "--newsapi-input", "data/processed/newsapi_processed.csv",
    "--model", "models/ag_binary_logreg.joblib",
)
```

#### 9-2) GDELT만 사용
```python
run_module(
    "src.pipeline",
    "--gdelt-input", "data/processed/gdelt_processed.csv",
    "--model", "models/ag_binary_logreg.joblib",
)
```

#### 9-3) SSAFY만 사용
```python
run_module(
    "src.pipeline",
    "--ssafy-input", "outputs/final_ssafy_tech_news.csv",
    "--model", "models/ag_binary_logreg.joblib",
)
```

## 자주 쓰는 실행 순서

### A. 처음부터 끝까지 한 번에 돌리는 기본 순서
```python
run_module("src.ag_pipeline")
run_module("src.newsapi_pipeline", "--max-pages", 1)
run_module("src.gdelt_pipeline", "--start-datetime", "20260301000000", "--end-datetime", "20260302000000", "--max-files", 96)
run_module("src.pipeline", "--newsapi-input", "data/processed/newsapi_processed.csv", "--gdelt-input", "data/processed/gdelt_processed.csv")
```

### B. 한국어 SSAFY 데이터까지 포함하는 순서
```python
run_module("src.ag_pipeline")
run_module("src.newsapi_pipeline", "--max-pages", 1)
run_module("src.gdelt_pipeline", "--start-datetime", "20260301000000", "--end-datetime", "20260302000000", "--max-files", 96)
run_module("src.ssafy_news_pipeline", "--input", "data/raw/ssafy_dataset_news_2025_1st_half.csv")
run_module(
    "src.pipeline",
    "--newsapi-input", "data/processed/newsapi_processed.csv",
    "--ssafy-input", "outputs/final_ssafy_tech_news.csv",
    "--gdelt-input", "data/processed/gdelt_processed.csv",
)
```

## CLI로 직접 실행하는 예시
```bash
python -m src.ag_pipeline
python -m src.newsapi_pipeline
python -m src.gdelt_pipeline \
  --start-datetime 20260301000000 \
  --end-datetime 20260302000000 \
  --max-files 96 \
  --processed-output data/processed/gdelt_processed.csv
python -m src.gdelt_analysis_pipeline
python -m src.pipeline \
  --newsapi-input data/processed/newsapi_processed.csv \
  --gdelt-input data/processed/gdelt_processed.csv \
  --metadata outputs/metadata.json
```

SSAFY 한국어 뉴스 파일 사용 예시:
```bash
python -m src.ssafy_news_pipeline \
  --input data/raw/ssafy_dataset_news_2025_1st_half.csv \
  --output outputs/final_ssafy_tech_news.csv \
  --profile outputs/ssafy_profile.json
```

## 생성 산출물
- `models/ag_binary_logreg.joblib`: AG News 기반 기술/비기술 이진분류기
- `data/raw/newsapi_raw.csv`: NewsAPI 원천 수집 결과
- `data/processed/newsapi_processed.csv`: NewsAPI 전처리 결과
- `data/raw/gdelt_raw_gkg.csv`: GDELT GKG 원천 수집 결과
- `data/processed/gdelt_processed.csv`: GDELT 전처리 결과
- `outputs/newsapi_tech_analyzed.csv`: NewsAPI 단독 분석 결과
- `outputs/final_ssafy_tech_news.csv`: SSAFY 최종 기술 뉴스
- `outputs/final_tech_news_all_sources.csv`: 전체 소스 통합 기술 뉴스
- `outputs/final_tech_news_<source>.csv`: 소스별 최종 기술 뉴스
- `outputs/tech_category_weekly_counts.csv`: 주간 카테고리 기사 수
- `outputs/tech_category_monthly_counts.csv`: 월간 카테고리 기사 수
- `outputs/tech_category_weekly_share.csv`: 주간 카테고리 점유율
- `outputs/tech_category_monthly_share.csv`: 월간 카테고리 점유율
- `outputs/tech_category_monthly_growth.csv`: 월간 카테고리 증감률
- `outputs/tech_stack_monthly_share.csv`: 월간 stack/entity 점유율
- `outputs/tech_source_bias.csv`: source별 카테고리 편향 리포트
- `outputs/tech_emerging_keywords.csv`: 최근 기간 대비 급상승 키워드
- `outputs/metadata.json`: 실행 파라미터/입력/행 수/카테고리/stack 분포 메타데이터
- `outputs/ssafy_profile.json`: SSAFY 입력 스키마/결측 비율 프로파일
- `outputs/uncertain_articles_all_sources.csv`: 불확실성 기준으로 최종 산출물에서 제외된 기사

## 참고
- 아키텍처 효율성 점검 및 개선안: `docs/architecture_review.md`
- 우선순위별 작업 계획: `docs/refactoring_plan.md`

## GDELT 수집 메모
- 기본 구현은 `GDELT raw GKG` 파일을 `masterfilelist.txt`에서 찾아 다운로드하는 방식입니다.
- 15분 단위 배치 파일을 기간별로 골라 내려받기 때문에, 월/주 단위 트렌드 분석용 백필 데이터 구축에 더 적합합니다.
- 자세한 비교와 선택 근거는 `docs/gdelt_source_strategy.md`를 참고하세요.
- 저비용 운영 중심 개선 로드맵: `docs/lean_operating_roadmap.md`
