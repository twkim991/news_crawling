# news_crawling

뉴스 데이터(AG News, NewsAPI)를 수집/정제하고, 기술 뉴스만 추출해 세부 기술 카테고리로 분류하는 파이프라인입니다.

## 환경 설정
이 저장소의 실행 코드는 모두 Python으로 작성되어 있습니다. 기존의 `package.json`에 있던 npm 의존성은 실제 런타임과 맞지 않았기 때문에, 현재는 `requirements.txt`를 기준으로 Python 패키지를 설치하도록 정리했습니다.

```bash
npm run setup
```

설치 후 아래 명령으로 핵심 Python 의존성이 모두 준비되었는지 확인할 수 있습니다.

```bash
npm run check:imports
```

## 파이프라인 개요
1. **AG 학습 (`src/ag_pipeline.py`)**
   - AG News를 기반으로 Sci/Tech vs Non-Tech 이진분류기 학습
2. **NewsAPI 수집/전처리 (`src/newsapi_pipeline.py`)**
   - NewsAPI에서 기사 수집 후 공통 스키마로 정규화
3. **통합 추론 (`src/pipeline.py`)**
   - AG + NewsAPI 데이터 전처리
   - 이진분류기 추론으로 tech 기사 필터링
   - 임베딩 유사도 기반 세부 기술 카테고리 분류
4. **SSAFY 한국어 뉴스 분석 (`src/ssafy_news_pipeline.py`)**
   - CSV 컬럼 구조 자동 매핑(한/영 컬럼 대응, `|` 구분자/멀티라인 본문 대응)
   - 스키마/결측 비율 프로파일 JSON 생성
   - 이진분류 확률 기반 `tech_score`, `is_uncertain` 추가
   - 품질 플래그 기반 저품질/불확실 기사 제거 후 제로샷 세부분류

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

SSAFY 한국어 뉴스 파일 사용 예시:
```bash
python src/ssafy_news_pipeline.py \
  --input data/raw/ssafy_dataset_news_2025_1st_half.csv \
  --output outputs/final_ssafy_tech_news.csv \
  --profile outputs/ssafy_profile.json
```

## 참고
아키텍처 효율성 점검 및 개선안은 아래 문서를 확인하세요.
- `docs/architecture_review.md`
