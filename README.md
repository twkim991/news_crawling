# news_crawling

뉴스 데이터(AG News, NewsAPI, SSAFY 뉴스)를 수집/정제하고, 기술 뉴스만 추출해 세부 기술 카테고리로 분류한 뒤 기술 스택 트렌드 리포트를 생성하는 파이프라인입니다.

## 파이프라인 개요
1. **AG 학습 (`src/ag_pipeline.py`)**
   - AG News를 기반으로 Sci/Tech vs Non-Tech 이진분류기 학습
2. **NewsAPI 수집/전처리 (`src/newsapi_pipeline.py`)**
   - NewsAPI에서 기사 수집 후 공통 스키마로 정규화
3. **운영 추론 + 트렌드 생성 (`src/pipeline.py`)**
   - NewsAPI/SSAFY 운영 데이터 전처리
   - 이진분류기 추론으로 tech 기사 필터링
   - 불확실 기사 제거 후 세부 기술 카테고리 분류
   - 주간/월간 기술 카테고리 트렌드 CSV 및 실행 메타데이터 생성
4. **SSAFY 한국어 뉴스 분석 (`src/ssafy_news_pipeline.py`)**
   - CSV 컬럼 구조 자동 매핑(한/영 컬럼 대응, `|` 구분자/멀티라인 본문 대응)
   - 스키마/결측 비율 프로파일 JSON 생성
   - 이진분류 확률 기반 `tech_score`, `is_uncertain` 추가
   - 품질 플래그 기반 저품질/불확실 기사 제거 후 제로샷 세부분류

## 핵심 디렉터리
- `src/`: 파이프라인 소스 코드
- `data/raw`: 원천 데이터
- `data/processed`: 전처리 데이터
- `outputs/`: 최종 결과 CSV, 트렌드 리포트, 메타데이터
- `docs/architecture_review.md`: 현재 구조 점검 및 개선 제안

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

NewsAPI + SSAFY 운영 데이터 통합 추론 예시:
```bash
python src/pipeline.py \
  --newsapi-input data/processed/newsapi_processed.csv \
  --ssafy-input outputs/final_ssafy_tech_news.csv \
  --output-dir outputs \
  --metadata outputs/metadata.json
```

## 생성 산출물
- `outputs/final_tech_news_<source>.csv`: 소스별 최종 기술 뉴스
- `outputs/tech_weekly_trends.csv`: 주간 기술 카테고리 기사 수
- `outputs/tech_monthly_trends.csv`: 월간 기술 카테고리 기사 수
- `outputs/metadata.json`: 실행 파라미터/입력/행 수/카테고리 분포 메타데이터

## 참고
아키텍처 효율성 점검 및 개선안은 아래 문서를 확인하세요.
- `docs/architecture_review.md`
