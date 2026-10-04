# AGING IMPACT

## 지역별 고령화 충격과 생활 인프라 미스매치 분석

지역별 고령화 수준과 인구 변화, 청년 이동, 경제활동, 생활 인프라 데이터를 결합하여  
고령화가 빠르게 진행되는 지역에서 나타나는 구조적 변화와 생활 인프라의 불균형을 분석하는 프로젝트입니다.

---

## 프로젝트 목표

본 프로젝트에서는 다음 질문을 중심으로 분석합니다.

- 고령화가 빠르게 진행되는 지역은 어디인가?
- 고령화 지역에서 청년 순유출과 인구 감소가 함께 나타나는가?
- 지역의 경제활동 수준은 고령화 및 인구 변화와 어떤 관계가 있는가?
- 고령화 수준에 비해 의료·복지·교통 인프라가 부족한 지역은 어디인가?
- 여러 지표를 종합했을 때 지역은 어떤 유형으로 구분되는가?

---

## 데이터 구성

### A 담당

A 담당에서는 다음 데이터를 처리합니다.

- 주민등록인구
- 청년인구
- 고령인구
- 청년 전입 / 전출 / 순이동
- 사업체수
- 종사자수

주요 분석 기간:

```text
인구 / 이동: 2016~2025
경제 데이터: 2024
```

### 생활 인프라 데이터

추후 다음 데이터와 결합할 예정입니다.

- 병원
- 약국
- 노인복지시설
- 버스정류장
- 철도 / 지하철 관련 시설

---

## 분석 단위

현재 A 데이터 기준 분석지역:

```text
229개 시군구급 지역
17개 시도
```

행정구역 변경이 발생한 지역은 현재 분석 기준에 맞게 지역코드를 정리했습니다.

대표 사례:

```text
인천 남구 28170
→ 미추홀구 28177

경북 군위군 47720
→ 대구 군위군 27720
```

---

## 주요 분석 지표

현재 A 데이터에서 생성한 주요 지표는 다음과 같습니다.

```text
고령화율_2025
고령화율변화폭_2016_2025

청년비율_2025
청년비율변화폭_2016_2025

인구증감률_2016_2025

청년순이동률_2016_2025

인구천명당_사업체수_2024
인구천명당_종사자수_2024
사업체당_종사자수_2024
```

---

## 현재 주요 분석 결과

A 데이터 기준 탐색적 분석에서 다음과 같은 관계가 확인되었습니다.

### 인구증감률 ↔ 청년순이동률

```text
r = 0.901
```

청년 순유입이 많은 지역일수록 전체 인구도 증가하는 강한 경향이 나타났습니다.

### 고령화율 ↔ 청년비율

```text
r = -0.877
```

고령화율이 높은 지역일수록 청년 비율이 낮은 경향이 나타났습니다.

### 고령화율 변화폭 ↔ 청년순이동률

```text
r = -0.789
```

고령화가 빠르게 진행된 지역일수록 청년 순유출이 함께 나타나는 경향이 확인되었습니다.

상관관계는 인과관계를 의미하지 않으며, 최종 해석은 생활 인프라 데이터 결합 이후 진행할 예정입니다.

---

## 프로젝트 구조

```text
AGING-IMPACT/
│
├─ data/
│  ├─ raw/
│  └─ processed/
│
├─ docs/
│  ├─ README_A.md
│  └─ data_dictionary_a.md
│
├─ results/
│  ├─ a_eda/
│  ├─ a_outliers/
│  ├─ a_sido_summary/
│  └─ a_feature_selection/
│
├─ src/
│  ├─ 01_check_raw_data.py
│  ├─ 02_preprocess_a.py
│  ├─ 03_preprocess_population.py
│  ├─ 04_check_population.py
│  ├─ 05_preprocess_migration.py
│  ├─ 06_patch_economy_from_census.py
│  ├─ 07_merge_a_dataset.py
│  ├─ 08_create_a_features.py
│  ├─ 09_eda_a.py
│  ├─ 10_check_a_outliers.py
│  ├─ 11_sido_summary.py
│  └─ 12_prepare_analysis_dataset.py
│
├─ .gitignore
├─ requirements.txt
└─ README.md
```

---

## 실행 환경

Python 가상환경을 사용하는 것을 권장합니다.

Windows PowerShell 기준:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## A 데이터 실행 순서

```powershell
python .\src\01_check_raw_data.py
python .\src\02_preprocess_a.py
python .\src\03_preprocess_population.py
python .\src\04_check_population.py
python .\src\05_preprocess_migration.py
python .\src\06_patch_economy_from_census.py
python .\src\07_merge_a_dataset.py
python .\src\08_create_a_features.py
python .\src\09_eda_a.py
python .\src\10_check_a_outliers.py
python .\src\11_sido_summary.py
python .\src\12_prepare_analysis_dataset.py
```

A 담당 상세 전처리 및 분석 내용은 아래 문서에서 확인할 수 있습니다.

```text
docs/README_A.md
```

A 데이터 컬럼 정의:

```text
docs/data_dictionary_a.md
```

---

## 주요 산출물

### A 기본 통합 데이터

```text
data/processed/a_dataset_merged.csv
```

### A 파생변수 포함 분석 데이터

```text
data/processed/a_dataset_features.csv
```

### 분석 후보 데이터

```text
results/a_feature_selection/a_analysis_full.csv
results/a_feature_selection/a_analysis_reduced.csv
```

---

## 기술 스택

- Python
- Pandas
- NumPy
- Matplotlib
- OpenPyXL
- Scikit-learn
- GeoPandas
- Folium

---

## 현재 진행 상태

- [x] 인구 데이터 수집 및 전처리
- [x] 청년 이동 데이터 수집 및 전처리
- [x] 경제 데이터 수집 및 보완
- [x] 행정구역 코드 정리
- [x] A 데이터 통합
- [x] 파생변수 생성
- [x] EDA
- [x] 이상치 검증
- [x] 시도별 요약
- [x] 분석 후보 변수 정리
- [ ] 생활 인프라 데이터 결합
- [ ] 최종 분석 변수 선정
- [ ] StandardScaler 적용
- [ ] K-Means 군집분석
- [ ] 군집 특성 해석
- [ ] 지도 시각화
- [ ] 최종 미스매치 분석

---

## 문서

A 담당 상세 문서:

```text
docs/README_A.md
```

A 데이터 사전:

```text
docs/data_dictionary_a.md
```