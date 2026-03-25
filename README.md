# news_crawling

뉴스 데이터(AG News, NewsAPI, SSAFY 뉴스, GDELT)를 수집·정제하고  
기술 뉴스만 추출해 **기술 카테고리 + 기술 스택(entity)** 로 분류한 뒤  
트렌드 리포트를 생성하는 파이프라인입니다.

---

## <span style = "background-color: #fff5b1">1. 개요</span>

이 프로젝트는 다음 과정을 자동화합니다.

- 뉴스 데이터 수집 (NewsAPI, GDELT, SSAFY)
- 데이터 정규화 및 전처리
- 기술 뉴스 필터링 (이진 분류)
- 세부 기술 카테고리 분류
- 기술 스택(entity) 다중 태깅 추출
- 불필요/저품질 기사 제거
- 주간/월간 기술 스택 트렌드 리포트 생성

---

## <span style = "background-color: #fff5b1">2. 전체 파이프라인 흐름</span>

AG 학습
→ 뉴스 수집 (NewsAPI / GDELT / SSAFY)
→ 전처리 및 공통 스키마 정규화
→ 기술 기사 필터링 (이진 분류)
→ 불확실 기사 제거
→ 불필요 기사/중복/저신호 기사 제거
→ 기술 카테고리 + 다중 stack/entity 분류
→ 기술 스택별 트렌드 리포트 생성

---

## <span style = "background-color: #fff5b1">3. 프로젝트 구조</span>

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

## <span style = "background-color: #fff5b1">4. 환경 설정</span>

의존성 설치

```text
python -m pip install -r requirements.txt
```

기본 import 검증

```text
python -c "import dotenv, joblib, numpy, pandas, psycopg2, requests, sentence_transformers, sklearn, torch; print('imports ok')"

```

## <span style = "background-color: #fff5b1">5. Quick Start</span>

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

## <span style = "background-color: #fff5b1">📊 6. Technology Taxonomy</span>

본 프로젝트는 다양한 뉴스 데이터(AG News, NewsAPI, GDELT 등)를 기반으로  
기술 관련 뉴스를 분류하고, **기술 스택별 트렌드 분석**을 수행합니다.

---

### 🎯 설계 기준

- 실제 산업에서 사용되는 기술 스택 기준으로 분류
- 뉴스 제목/본문만으로도 태깅 가능하도록 단순화
- 중복 카테고리 제거 (언어 vs 프레임워크)
- AI/데이터 영역은 별도 축으로 분리

---

### 🧩 Taxonomy Overview

총 8개의 핵심 대분류와 예외 처리용 `Other Tech`로 구성됩니다.

1. Programming Languages
2. Frameworks
3. Data & AI
4. Databases & Storage
5. Infrastructure & Cloud
6. Data Engineering & Messaging
7. DevOps & CI/CD
8. Collaboration & Tools (Optional)

---

### 1️⃣ Programming Languages

> 프로그래밍 언어 자체

**Languages**

- Java, Python, JavaScript, TypeScript
- C++, C#, Go, Rust
- Kotlin, Swift, Dart

**Optional Tags**

- `#OOP` `#Functional` `#Compiled` `#Interpreted` `#Systems`

---

### 2️⃣ Frameworks

#### 🔹 Backend

- Spring
- Django
- FastAPI
- Express
- NestJS
- Ruby on Rails

#### 🔹 Frontend

- React
- Vue
- Angular
- Svelte
- Next.js

#### 🔹 Mobile

- Flutter
- React Native
- iOS SDK
- Android SDK

---

### 3️⃣ Data & AI

#### 🔹 ML / DL Framework

- PyTorch
- TensorFlow
- Scikit-learn

#### 🔹 Data Processing

- Pandas
- NumPy

#### 🔹 LLM / Generative AI

- OpenAI
- HuggingFace
- LangChain

#### 🔹 MLOps

- MLflow
- Kubeflow

---

### 4️⃣ Databases & Storage

#### 🔹 RDBMS

- PostgreSQL
- MySQL
- Oracle

#### 🔹 NoSQL

- MongoDB
- Cassandra
- DynamoDB

#### 🔹 Cache / In-Memory

- Redis
- Memcached

#### 🔹 Search / Index

- Elasticsearch
- OpenSearch

---

### 5️⃣ Infrastructure & Cloud

#### 🔹 Cloud Providers

- AWS
- Google Cloud
- Azure
- Naver Cloud

#### 🔹 Containers & Orchestration

- Docker
- Kubernetes

#### 🔹 Serverless / Edge

- AWS Lambda
- Cloudflare Workers

#### 🔹 CDN / Edge Platform

- Cloudflare
- Vercel

---

### 6️⃣ Data Engineering & Messaging

#### 🔹 Streaming / Messaging

- Kafka
- RabbitMQ
- ActiveMQ

#### 🔹 Big Data Processing

- Spark
- Flink
- Hadoop

#### 🔹 Workflow / Orchestration

- Airflow
- Prefect

---

### 7️⃣ DevOps & CI/CD

#### 🔹 CI/CD

- GitHub Actions
- GitLab CI
- Jenkins
- ArgoCD

#### 🔹 Monitoring / Observability

- Prometheus
- Grafana
- Datadog

#### 🔹 Logging

- ELK Stack

#### 🔹 Infrastructure as Code

- Terraform
- Ansible

---

### 8️⃣ Collaboration & Tools (Optional)

#### 🔹 Version Control

- Git
- GitHub
- GitLab

#### 🔹 Project / Documentation

- Jira
- Confluence
- Notion

#### 🔹 API Tools

- Swagger (OpenAPI)
- Postman

---

### 🧠 How It Is Used

뉴스 데이터는 다음 단계로 처리됩니다:

1. 기술 뉴스 여부 필터링
2. 다중 라벨 분류 (Multi-label classification)
3. 카테고리별 빈도 집계
4. 기술 트렌드 분석

---

### 🧪 Example

"OpenAI releases new GPT model on Azure"

→ Data & AI (LLM)
→ Infrastructure & Cloud (Azure)

---

### ⚠️ Notes

- 하나의 뉴스는 여러 카테고리에 동시에 포함될 수 있음
- UI 라이브러리 (Redux, Tailwind 등)는 노이즈를 줄이기 위해 제외
- 과도한 세분화는 모델 성능 저하를 유발할 수 있음

---

### 📦 Example Structure (for code)

```python
taxonomy = {
  "languages": [...],
  "frameworks": {
    "backend": [...],
    "frontend": [...],
    "mobile": [...]
  },
  "data_ai": [...],
}

```

## <span style = "background-color: #fff5b1">7. 실행 가이드</span>

| 목적            | 실행                                    |
| --------------- | --------------------------------------- |
| AG 모델 학습    | python -m src.ag_pipeline               |
| NewsAPI 수집    | python -m src.newsapi_pipeline          |
| GDELT 수집      | python -m src.gdelt_pipeline            |
| GDELT 분석      | python -m src.gdelt_analysis_pipeline   |
| NewsAPI 분석    | python -m src.newsapi_analysis_pipeline |
| SSAFY 처리      | python -m src.ssafy_news_pipeline       |
| 통합 파이프라인 | python -m src.pipeline                  |

## <span style = "background-color: #fff5b1">8. 상세 실행 예시</span>

### AG 학습

```bash
python -m src.ag_pipeline
```

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

## <span style = "background-color: #fff5b1">9. GDELT 수집 메모</span>

- 15분 단위 GKG 파일 기반
- 파일 수 많음 → max-files 제한 권장
- 중복 기사 및 노이즈 존재
- 후처리 필터링 필요

---

## <span style = "background-color: #fff5b1">10. 주의사항</span>

- GDELT 데이터는 노이즈가 많음
- NewsAPI는 요청 제한 존재
- SSAFY CSV는 컬럼 구조 변동 가능
- 대량 데이터 시 디스크 용량 확인 필요

---

## <span style = "background-color: #fff5b1">11. 주요 산출물</span>

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

## <span style = "background-color: #fff5b1">12. 참고 문서</span>

- docs/architecture_review.md
- docs/refactoring_plan.md
- docs/gdelt_source_strategy.md
- docs/lean_operating_roadmap.md
