# GDELT Tech News Analysis Output Guide

GDELT 뉴스 데이터를 대상으로 수행하는 아래 파이프라인의 **일별 산출물**, **파일별 역할**, **컬럼 정의**를 정리한 문서다.

> 기술 뉴스 판별 → 기술 카테고리 분류 → 기술 스택 태깅 → 트렌드 점수 산출

---

## 1. Pipeline Overview

```text
Raw GDELT Data
  ↓
data/processed/gdelt_processed.csv
  ↓
[1] Binary Tech Classification
  ↓
[2] Dev-Tech Rule Gate
  ↓
[3] Tech Category Classification
  ↓
[4] Stack Tagging
  ↓
[5] Stack Trend Score Aggregation
  ↓
outputs/*.csv
```

---

## 2. Daily Output Files

배치가 하루 1회 정상 수행되면 아래 파일들이 생성된다.

### 2.1 `gdelt_classified_all.csv`

```text
outputs/gdelt_classified_all.csv
```

최종적으로 **기술 뉴스로 판정된 전체 기사**를 저장하는 파일이다.

- 기술 스택이 명확히 태깅된 기사 포함
- 스택까지는 특정되지 않았지만 기술 뉴스로 분류된 기사 포함
- 운영/DB 적재용 기본 원본

---

### 2.2 `gdelt_classified_tracked_only.csv`

```text
outputs/gdelt_classified_tracked_only.csv
```

실제로 **추적 대상 기술 스택이 붙은 기사만 따로 분리한 파일**이다.

- `stack_labels`가 비어 있지 않은 기사만 포함
- 스택별 기사 조회, 리포트, 트렌드 집계 검증에 사용

---

### 2.3 `gdelt_stack_trend_scores.csv`

```text
outputs/gdelt_stack_trend_scores.csv
```

추적 대상 스택 기사들을 기준으로 **일간 / 주간 / 월간 트렌드 점수**를 계산한 결과 파일이다.

- 기술 스택별 랭킹
- 기간별 변화량 분석
- 대시보드 시계열 데이터

---

### 2.4 `gdelt_classified_debug.csv`

```text
outputs/gdelt_classified_debug.csv
```

분류 검증 및 오탐 분석용 디버그 파일이다.

- 왜 기술 뉴스로 통과했는지 확인
- 왜 특정 스택으로 태깅됐는지 확인
- 룰/임계값 조정 검토용

> 운영 서비스에서는 선택적으로만 저장하는 편이 낫다.

---

## 3. File Details

## 3.1 `gdelt_classified_all.csv`

최종적으로 기술 뉴스로 판정된 전체 기사 목록이다.

### Purpose

- 기술 뉴스 전체 보관
- DB 적재
- 검색 / 필터링 / 대시보드 기본 데이터
- 후속 검증용 기준 데이터

### Columns

| Column                    | Example                                                            | Description                                    |
| ------------------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| `article_datetime`        | `2026-03-24 01:30:00+00:00`                                        | 기사 발행 시각을 datetime으로 정규화한 값      |
| `article_date`            | `2026-03-24`                                                       | 기사 발행 일자                                 |
| `article_week`            | `2026-W13`                                                         | ISO 주차 기준 주간 값                          |
| `article_month`           | `2026-03`                                                          | 월 단위 집계용 값                              |
| `classification_type`     | `tracked_stack`, `other_tech`                                      | 추적 스택 기사인지 기타 기술 기사인지 구분     |
| `tech_bucket`             | `Tracked Stack`, `Other Tech`                                      | 분류 타입의 표시용 이름                        |
| `tech_category`           | `Programming Languages`                                            | 기사 기술 대분류                               |
| `tech_category_score`     | `0.83`                                                             | 대분류 1순위 점수                              |
| `tech_category_score_gap` | `0.11`                                                             | 1순위와 2순위의 점수 차이                      |
| `top2_category`           | `Backend Frameworks`                                               | 대분류 2순위 후보                              |
| `top2_score`              | `0.72`                                                             | 대분류 2순위 점수                              |
| `primary_stack`           | `Python`                                                           | 최종 대표 기술 스택                            |
| `stack_labels`            | `Python\|FastAPI`                                                  | 기사에서 감지된 기술 스택 목록                 |
| `stack_label_count`       | `2`                                                                | 감지된 스택 개수                               |
| `matched_devtech_aliases` | `Python, FastAPI`                                                  | 룰 기반 게이트에서 탐지된 alias 기반 스택 목록 |
| `matched_devtech_reasons` | `Python:ambiguous_with_context \| FastAPI:non_ambiguous_alias_hit` | 룰 통과 이유 요약                              |
| `is_tech_score`           | `0.91`                                                             | binary classifier가 예측한 기술 뉴스 확률      |
| `is_tech`                 | `1`                                                                | binary classifier 기준 기술 뉴스 여부          |
| `is_devtech`              | `1`                                                                | dev-tech rule gate 통과 여부                   |
| `final_is_devtech`        | `1`                                                                | 최종 기술 뉴스 채택 여부                       |
| `title`                   | 문자열                                                             | 기사 제목                                      |
| `description`             | 문자열                                                             | 기사 요약                                      |
| `content`                 | 문자열                                                             | 기사 본문                                      |
| `url`                     | URL                                                                | 기사 원문 링크                                 |
| `published_at`            | 원본 날짜 문자열                                                   | 원본 데이터셋의 날짜 값                        |
| `source`                  | `gdelt`                                                            | 데이터 출처                                    |

### Notes

#### `classification_type`

- `tracked_stack`: 추적 중인 기술 스택이 하나 이상 붙은 기사
- `other_tech`: 기술 뉴스는 맞지만 특정 스택으로 연결되지 않은 기사

#### `primary_stack`

- `stack_labels` 중 대표성이 가장 높다고 판단된 스택
- 확신이 낮으면 `Unspecified`가 될 수 있음

#### `stack_labels`

다중 태깅이 가능하다.

예시:

- `Python|FastAPI`
- `Docker|Kubernetes`
- `PyTorch|Python`

---

## 3.2 `gdelt_classified_tracked_only.csv`

`gdelt_classified_all.csv` 중에서 실제로 추적 중인 기술 스택이 붙은 기사만 분리한 파일이다.

### Inclusion Rule

- `tech_bucket != "Other Tech"`
- 즉, `stack_labels`가 비어 있지 않은 기사만 포함

### Purpose

- 기술 스택별 기사 목록 조회
- 스택별 리포트 생성
- 특정 스택 뉴스만 별도 저장
- 트렌드 점수 계산 입력 데이터

### Key Columns

| Column              | Description    |
| ------------------- | -------------- |
| `article_datetime`  | 기사 시각      |
| `article_date`      | 기사 날짜      |
| `article_week`      | 기사 주차      |
| `article_month`     | 기사 월        |
| `tech_category`     | 기술 대분류    |
| `primary_stack`     | 대표 스택      |
| `stack_labels`      | 전체 스택 태그 |
| `stack_label_count` | 스택 태그 개수 |
| `title`             | 기사 제목      |
| `description`       | 기사 요약      |
| `content`           | 기사 본문      |
| `url`               | 원문 링크      |
| `source`            | 출처           |

> 이 파일의 컬럼 구조는 기본적으로 `gdelt_classified_all.csv`와 동일하다.

---

## 3.3 `gdelt_stack_trend_scores.csv`

기술 스택별로 **일간 / 주간 / 월간 트렌드 점수**를 계산한 파일이다.

### Purpose

- 스택별 트렌드 랭킹
- 특정 기술의 상승/하락 추세 파악
- 기간별 관심도 비교
- 대시보드 시계열 데이터

### Columns

| Column                    | Example                 | Description                                   |
| ------------------------- | ----------------------- | --------------------------------------------- |
| `period_type`             | `daily`                 | 집계 기간 단위 (`daily`, `weekly`, `monthly`) |
| `period_value`            | `2026-03-24`            | 실제 기간 값                                  |
| `stack_category`          | `Programming Languages` | 기술 스택 대분류                              |
| `stack_subgroup`          | `Languages`             | 기술 스택 세부 그룹                           |
| `stack_name`              | `Python`                | 기술 스택명                                   |
| `article_count`           | `18`                    | 해당 기간 해당 스택으로 집계된 기사 수        |
| `unique_article_count`    | `17`                    | URL 기준 중복 제거 기사 수                    |
| `weighted_article_sum`    | `14.5`                  | 다중 스택 기사 가중치 반영 합계               |
| `period_total_weight`     | `120.0`                 | 해당 기간 전체 스택 기사 가중치 총합          |
| `share_ratio`             | `0.1208`                | 해당 기간 전체 대비 해당 스택 점유율          |
| `avg_binary_score`        | `0.87`                  | 해당 스택 기사들의 평균 기술 뉴스 확률        |
| `event_hit_count`         | `6`                     | 이벤트성 키워드가 감지된 기사 수              |
| `event_ratio`             | `0.33`                  | 이벤트 기사 비율                              |
| `share_score`             | `2.17`                  | 점유율 기반 점수                              |
| `volume_score`            | `5.60`                  | 기사량 기반 점수                              |
| `event_score`             | `0.66`                  | 이벤트성 기사 비율 기반 점수                  |
| `confidence_score`        | `1.74`                  | 평균 기술 뉴스 확률 기반 점수                 |
| `trend_score_raw`         | `10.17`                 | 원시 트렌드 점수 합계                         |
| `trend_score_30`          | `10.17`                 | 최대 30점 기준 최종 트렌드 점수               |
| `previous_trend_score_30` | `9.48`                  | 이전 기간 점수                                |
| `score_delta`             | `0.69`                  | 이전 기간 대비 변화량                         |
| `score_delta_pct`         | `7.28`                  | 이전 기간 대비 변화율(%)                      |

### Trend Score Formula

```text
trend_score_raw
= share_score
+ volume_score
+ event_score
+ confidence_score
```

최종 점수는 아래처럼 최대 30점으로 제한된다.

```text
trend_score_30 = min(trend_score_raw, 30)
```

### Score Meaning

- `share_score`: 전체 기사량 중 해당 스택 점유율
- `volume_score`: 절대 기사량
- `event_score`: 릴리즈 / 패치 / 업그레이드 / 마이그레이션 등 이벤트성 기사 비중
- `confidence_score`: binary classifier가 해당 기사들을 기술 뉴스답게 본 정도

---

## 0. 전체 계산 흐름 요약

```text
   trend_score_raw = share_score + volume_score + event_score + confidence_score

   trend_score_30 = min(trend_score_raw, 30)
```

---

## 1. share_score (점유율 점수)

해당 기간 동안 전체 기사 대비 특정 스택이 차지하는 비율이다.

```text
share_ratio = weighted_article_sum / 전체 스택 기사 총합
share_score = log1p(share_ratio * 100) * 2
```

### 왜 필요한가

- 단순 기사 수가 아니라 **시장 내 점유율**을 반영
- 특정 기간에 특정 기술이 얼마나 “비중 있게 등장했는지” 측정

---

## 1-1. weighted_article_sum (중요 개념)

다중 스택 기사로 인해 볼륨이 과도하게 증가하는 것을 방지하기 위한 가중치이다.

### 공식

```text
weight = 1 / number_of_stacks
```

### 왜 필요한가

- 하나의 기사가 여러 스택을 동시에 부풀리는 문제 방지
- 트렌드 왜곡 방지

---

## 2. volume_score (기사량 점수)

해당 스택이 얼마나 많이 언급되었는지를 반영한다.

```text
volume_score = log1p(해당 스택 기사 수) * 2
```

### 왜 필요한가

- 로그를 쓰는 이유는 **과도한 기사 수 폭증을 완화**하기 위함
- 점유율만 보면 전체 기사량이 적은 날에 왜곡됨
- 절대적인 관심도(언급량)를 함께 반영

---

## 3. event_score (이벤트 점수)

릴리즈, 업데이트, 패치, 마이그레이션 같은 **실제 기술 이벤트 발생 여부**를 반영한다.

```text
event_ratio = 이벤트 키워드 포함 기사 수 / 이벤트 기사 비율
event_score = event_ratio * 2
```

### 이벤트 키워드 예시

```text
release, launch, update, upgrade, patch, migrate, rollout
```

### 왜 필요한가

- 단순 언급이 아니라 **실제 변화가 있는 기술**을 강조
- 트렌드 상승 신호를 잡기 위한 지표

---

## 4. confidence_score (품질 점수)

해당 기사들이 얼마나 “기술 뉴스다운지”를 반영한다.

```text
confidence_score = binary classifier 평균 확률 * 2
```

### 왜 필요한가

- 노이즈 기사 제거
- 기술 관련성이 높은 기사일수록 점수 상승

---

## 8. 설계 의도 요약

이 트렌드 점수는 아래 4가지를 동시에 반영한다.

- **시장 점유율** (share)
- **절대 언급량** (volume)
- **실제 기술 이벤트 발생 여부** (event)
- **기사의 기술 관련성 품질** (confidence)

즉 단순 “기사 많이 나온 기술”이 아니라,

> 실제로 의미 있는 변화가 있고, 시장에서 비중 있게 언급되며, 기술적으로 확실한 뉴스

를 높은 점수로 만들기 위한 구조다.

---

## 3.4 `gdelt_classified_debug.csv`

분류 검증 및 오탐 분석용 파일이다.

### Purpose

- 오탐 기사 분석
- 누락 기사 분석
- alias 룰 검증
- ambiguous stack 판정 이유 확인
- threshold 조정 검토

### Key Columns

| Column                    | Description                            |
| ------------------------- | -------------------------------------- |
| `tech_category_score`     | 1순위 대분류 점수                      |
| `tech_category_score_gap` | 1순위-2순위 점수 차이                  |
| `top2_category`           | 2순위 대분류                           |
| `top2_score`              | 2순위 점수                             |
| `matched_devtech_aliases` | 룰 기반으로 잡힌 스택                  |
| `matched_devtech_reasons` | 룰 통과 이유 요약                      |
| `all_devtech_rule_logs`   | 전체 스택 판정 로그                    |
| `ambiguous_only_match`    | ambiguous 스택만으로 매칭되었는지 여부 |
| `is_tech_score`           | binary classifier 점수                 |
| `is_tech`                 | binary classifier 결과                 |
| `is_devtech`              | rule gate 결과                         |
| `final_is_devtech`        | 최종 채택 여부                         |

### Caution

`all_devtech_rule_logs`는 문자열 길이가 길어질 수 있다.  
운영 환경에서는 저장 용량과 I/O를 고려해 선택적으로만 유지하는 것이 좋다.

---

## 4. Output Naming Examples

출력 파일명은 `output_prefix` 정책에 따라 달라질 수 있다.

### Monthly Example

```text
outputs/2026_03/gdelt_2026_03_classified_all.csv
outputs/2026_03/gdelt_2026_03_classified_tracked_only.csv
outputs/2026_03/gdelt_2026_03_stack_trend_scores.csv
outputs/2026_03/gdelt_2026_03_classified_debug.csv
```

### Daily Example

```text
outputs/2026_03_24/gdelt_2026_03_24_classified_all.csv
outputs/2026_03_24/gdelt_2026_03_24_classified_tracked_only.csv
outputs/2026_03_24/gdelt_2026_03_24_stack_trend_scores.csv
outputs/2026_03_24/gdelt_2026_03_24_classified_debug.csv
```

즉, 실제 경로는 배치 정책에 따라 달라질 수 있지만 생성되는 결과 파일의 종류는 동일하다.

---

## 5. Recommended Usage

### For Production / DB Load

- `gdelt_classified_all.csv`
- `gdelt_classified_tracked_only.csv`
- `gdelt_stack_trend_scores.csv`

### For Validation / Debugging

- `gdelt_classified_debug.csv`

---

## 6. Recommended Columns to Keep

### Core Columns

| Column              | Why Keep It                |
| ------------------- | -------------------------- |
| `article_datetime`  | 시계열 정렬 및 최신순 정렬 |
| `article_date`      | 일 단위 집계               |
| `article_week`      | 주 단위 집계               |
| `article_month`     | 월 단위 집계               |
| `tech_category`     | 대분류 필터링              |
| `primary_stack`     | 대표 스택 조회             |
| `stack_labels`      | 다중 스택 분석             |
| `stack_label_count` | 다중 태깅 여부 확인        |
| `is_tech_score`     | 품질 점수 활용             |
| `title`             | 기사 식별                  |
| `url`               | 중복 제거 및 원문 연결     |
| `source`            | 출처 추적                  |

### Debug-Only Columns

| Column                    | Why Debug Only               |
| ------------------------- | ---------------------------- |
| `matched_devtech_reasons` | 운영 서비스보다는 검증용     |
| `all_devtech_rule_logs`   | 문자열이 길고 저장 비용이 큼 |
| `ambiguous_only_match`    | 룰 튜닝용                    |
| `top2_category`           | 모델 점검용                  |
| `top2_score`              | 모델 점검용                  |
| `tech_category_score_gap` | 모델 점검용                  |

---

## 7. Summary

이 파이프라인은 매일 아래 4종류의 결과를 생성한다.

1. **전체 기술 뉴스 결과**  
   `gdelt_classified_all.csv`

2. **추적 스택 기사만 분리한 결과**  
   `gdelt_classified_tracked_only.csv`

3. **기술 스택별 트렌드 점수 결과**  
   `gdelt_stack_trend_scores.csv`

4. **분류 / 오탐 검증용 디버그 결과**  
   `gdelt_classified_debug.csv`

핵심 역할은 아래와 같다.

- `classified_all`: 기술 뉴스 전체 원본
- `tracked_only`: 실제 추적 스택 기사만 분리한 결과
- `stack_trend_scores`: 스택별 집계 결과
- `debug`: 분류 품질 검증용 도구

---

## 8. Examples

### Example 1. `gdelt_classified_all.csv`

| article_date | tech_category         | primary_stack | stack_labels    | title                                 |
| ------------ | --------------------- | ------------- | --------------- | ------------------------------------- |
| 2026-03-24   | Programming Languages | Python        | Python\|FastAPI | Python 3.14 ecosystem update released |

### Example 2. `gdelt_classified_tracked_only.csv`

| article_date | primary_stack | stack_labels       | url                               |
| ------------ | ------------- | ------------------ | --------------------------------- |
| 2026-03-24   | Docker        | Docker\|Kubernetes | `https://example.com/article/123` |

### Example 3. `gdelt_stack_trend_scores.csv`

| period_type | period_value | stack_name | article_count | trend_score_30 | score_delta |
| ----------- | ------------ | ---------- | ------------- | -------------- | ----------- |
| daily       | 2026-03-24   | Python     | 18            | 10.17          | 0.69        |
| daily       | 2026-03-24   | React      | 13            | 8.92           | -0.34       |
| weekly      | 2026-W13     | Docker     | 42            | 15.48          | 2.11        |
