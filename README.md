# news_crawling

뉴스 데이터(AG News, NewsAPI)를 수집/정제하고, 기술 뉴스만 추출해 세부 기술 카테고리로 분류하는 파이프라인입니다.

## 파이프라인 개요
1. **AG 학습 (`src/ag_pipeline.py`)**
   - AG News를 기반으로 Sci/Tech vs Non-Tech 이진분류기 학습
2. **NewsAPI 수집/전처리 (`src/newsapi_pipeline.py`)**
   - NewsAPI에서 기사 수집 후 공통 스키마로 정규화
3. **통합 추론 (`src/pipeline.py`)**
   - AG + NewsAPI 데이터 전처리
   - 이진분류기 추론으로 tech 기사 필터링
   - 임베딩 유사도 기반 세부 기술 카테고리 분류

## 핵심 디렉터리
- `src/`: 파이프라인 소스 코드
- `data/raw`: 원천 데이터
- `data/processed`: 전처리 데이터
- `outputs/`: 최종 결과 CSV
- `docs/architecture_review.md`: 현재 구조 점검 및 개선 제안

## 실행 순서 (예시)
```bash
python src/ag_pipeline.py
python src/newsapi_pipeline.py
python src/pipeline.py
```

## 참고
아키텍처 효율성 점검 및 개선안은 아래 문서를 확인하세요.
- `docs/architecture_review.md`
