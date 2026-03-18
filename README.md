# news_crawling

뉴스 데이터(AG News, NewsAPI, SSAFY 뉴스)를 수집/정제하고, 기술 뉴스만 추출해 **기술 카테고리 + 기술 스택(entity)** 로 분류한 뒤 기술 스택 트렌드 리포트를 생성하는 파이프라인입니다.

## 파이프라인 개요
1. **AG 학습 (`src/ag_pipeline.py`)**
   - AG News를 기반으로 Sci/Tech vs Non-Tech 이진분류기 학습
2. **NewsAPI 수집/전처리 (`src/newsapi_pipeline.py`)**
   - NewsAPI에서 기사 수집 후 공통 스키마로 정규화
3. **운영 추론 + 트렌드 생성 (`src/pipeline.py`)**
   - NewsAPI/SSAFY 운영 데이터 전처리
   - 이진분류기 추론으로 tech 기사 필터링
   - 불확실 기사 제거 후 세부 기술 카테고리 분류
   - stack/entity 매칭(`primary_stack`, `secondary_stack`) 추가
   - 주간/월간 카테고리 점유율, stack 점유율, source bias, emerging keywords 리포트 생성
4. **SSAFY 한국어 뉴스 분석 (`src/ssafy_news_pipeline.py`)**
   - CSV 컬럼 구조 자동 매핑(한/영 컬럼 대응, `|` 구분자/멀티라인 본문 대응)
   - 스키마/결측 비율 프로파일 JSON 생성
   - 이진분류 확률 기반 `tech_score`, `is_uncertain` 추가
   - 품질 플래그 기반 저품질/불확실 기사 제거 후 제로샷 세부분류

## taxonomy
- `src/taxonomy.py`는 이제 **상위 기술 카테고리 + stack/entity alias** 구조를 가집니다.
- 예: `AI/ML > OpenAI`, `Cloud & Infrastructure > AWS`, `Frameworks & Libraries > React`
- 분류 결과에는 `tech_category`와 별도로 `primary_stack`, `secondary_stack`, `stack_matches`가 추가됩니다.

## 핵심 디렉터리
- `src/`: 파이프라인 소스 코드
- `data/raw`: 원천 데이터
- `data/processed`: 전처리 데이터
- `outputs/`: 최종 결과 CSV, 트렌드 리포트, 메타데이터
- `docs/architecture_review.md`: 현재 구조 점검 및 개선 제안
- `docs/refactoring_plan.md`: 우선순위별 리팩터링 계획

## 실행 순서 (예시)
```bash
python src/ag_pipeline.py
python src/newsapi_pipeline.py
python src/pipeline.py \
  --newsapi-input data/processed/newsapi_processed.csv \
  --metadata outputs/metadata.json
```

SSAFY 한국어 뉴스 파일 사용 예시:
```bash
python src/ssafy_news_pipeline.py \
  --input data/raw/ssafy_dataset_news_2025_1st_half.csv \
  --output outputs/final_ssafy_tech_news.csv \
  --profile outputs/ssafy_profile.json
```

## 생성 산출물
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

## 참고
- 아키텍처 효율성 점검 및 개선안: `docs/architecture_review.md`
- 우선순위별 작업 계획: `docs/refactoring_plan.md`
