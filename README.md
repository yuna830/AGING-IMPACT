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

### A 담당 - 인구·이동·경제 데이터

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

### B 담당 - 생활 인프라 데이터

B 담당에서는 다음 데이터를 처리합니다.

- 병원
- 약국
- 노인복지시설
- 버스정류장
- 도시철도 역사

주요 데이터 기준:

```text
병원 / 약국: 2025-12-31
노인복지시설: 2025-12-31
버스정류장: 2025-10-31
도시철도 역사: 2026-06-30
행정경계: 2025년 2분기
```

도시철도 데이터는 분석에 적합한 2025년 기준 전국 통합 자료를 찾지 못해 2026-06-30 기준 자료를 사용했습니다.

---

## 분석 단위

A와 B 데이터의 최종 분석 단위는 동일한 **229개 시군구급 지역, 17개 시도**로 통일했습니다.

```text
229개 시군구급 지역
17개 시도
```

A 데이터에서는 행정구역 변경이 발생한 지역을 현재 분석 기준에 맞게 지역코드를 정리했습니다.

대표 사례:

```text
인천 남구 28170
→ 미추홀구 28177

경북 군위군 47720
→ 대구 군위군 27720
```

B 데이터에서는 원자료별로 서로 다른 시군구 표기를 A 데이터와 결합할 수 있도록 동일한 지역 단위로 표준화했습니다.

일반시의 행정구는 상위 시 단위로 통합했습니다.

대표 사례:

```text
수원시 장안구 → 수원시
고양시 덕양구 → 고양시
청주시 흥덕구 → 청주시
전주시 완산구 → 전주시
창원시 성산구 → 창원시
```

세종특별자치시는 `세종시`로 통일했습니다.

---

## 주요 분석 지표

### A - 인구·이동·경제 지표

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

### B - 생활 인프라 지표

B 데이터에서는 지역별 시설 수와 함께 65세 이상 인구를 기준으로 생활 인프라 공급 수준을 비교하기 위한 지표를 생성했습니다.

```text
노인천명당_병원수
노인천명당_약국수
노인천명당_복지시설수
노인천명당_버스정류장수
노인천명당_철도역수
```

계산식:

```text
시설 수 / 65세 이상 인구 × 1,000
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

## B 생활 인프라 전처리 결과

### 의료 인프라

건강보험심사평가원 요양기관 개설 현황을 활용했습니다.

병원은 다음 요양종별을 포함했습니다.

- 상급종합병원
- 종합병원
- 병원
- 요양병원
- 정신병원

약국은 별도로 집계했습니다.

```text
병원: 3,380개
약국: 25,497개
```

### 노인복지 인프라

다음 6개 시설 유형을 분석에 사용했습니다.

- 노인주거복지시설
- 노인의료복지시설
- 노인여가복지시설
- 재가노인복지시설
- 노인일자리지원기관
- 학대피해노인 전용쉼터

6개 유형을 합산하여 `노인복지시설수`를 생성했습니다.

```text
노인복지시설수: 97,193개
```

치매전담형 장기요양기관은 다른 시설 유형과의 중복 가능성을 고려하여 합계에서 제외했습니다.

노인일자리지원기관의 경우 보고서 내 광역단위 총계는 223개이나 시군구별 시설수 합계는 224개로 1개 차이가 확인되었습니다.  
본 분석은 시군구 단위 분석을 목적으로 하므로 시군구별 원자료에 기재된 값을 기준으로 사용했습니다.

### 버스정류장

전국 버스정류장 위치정보의 위·경도 좌표와 2025년 2분기 시군구 행정경계를 공간 결합하여 행정구역을 표준화했습니다.

```text
원본 정류장: 227,065개
좌표 존재: 227,060개
공간 매칭 성공: 227,004개
제외: 61개 (약 0.03%)
```

좌표 결측 또는 행정경계와 매칭되지 않은 정류장은 분석에서 제외했습니다.

선택한 원자료에서 강원특별자치도 고성군에 해당하는 버스정류장 자료가 확인되지 않아 해당 지역은 실제 정류장이 0개인 경우와 구분하기 위해 결측값으로 유지했습니다.

### 도시철도

도시철도 원자료는 동일 역사가 노선별로 중복될 수 있어 `시도명 + 시군구명 + 역사명`을 기준으로 중복을 제거했습니다.

```text
원본: 1,099행
중복 제거: 99행
최종 도시철도 역사: 1,000개
```

도시철도 역사가 존재하지 않는 지역은 0으로 처리했습니다.

---

## 프로젝트 구조

```text
AGING-IMPACT/
│
├─ data/
│  ├─ raw/
│  │  ├─ business/
│  │  ├─ census_2024/
│  │  ├─ employee/
│  │  ├─ migration/
│  │  ├─ population/
│  │  └─ infrastructure/
│  │
│  └─ processed/
│     ├─ a_dataset_merged.csv
│     ├─ a_dataset_features.csv
│     ├─ medical_by_region.csv
│     ├─ bus_by_region.csv
│     ├─ subway_by_region.csv
│     └─ welfare_by_region.csv
│
├─ docs/
│  ├─ README_A.md
│  ├─ README_B.md
│  ├─ data_dictionary_a.md
│  └─ data_dictionary_b.md
│
├─ results/
│  ├─ a_eda/
│  ├─ a_outliers/
│  ├─ a_sido_summary/
│  ├─ a_feature_selection/
│  └─ b_infrastructure/
│     └─ b_infrastructure.csv
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
│  ├─ 12_prepare_analysis_dataset.py
│  ├─ 13_medical.py
│  ├─ 14_bus.py
│  ├─ 15_subway.py
│  ├─ 16_welfare.py
│  └─ 17_merge_b.py
│
├─ .gitignore
├─ requirements.txt
└─ README.md
```

※ 버스정류장과 도시철도 지역 매칭에 사용한 시군구 행정경계 Shapefile은 파일 용량으로 인해 저장소에 포함하지 않았습니다.

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

## B 데이터 실행 순서

```powershell
python .\src\13_medical.py
python .\src\14_bus.py
python .\src\15_subway.py
python .\src\16_welfare.py
python .\src\17_merge_b.py
```

B 담당 상세 전처리 및 분석 내용은 아래 문서에서 확인할 수 있습니다.

```text
docs/README_B.md
```

B 데이터 컬럼 정의:

```text
docs/data_dictionary_b.md
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

### A 분석 후보 데이터

```text
results/a_feature_selection/a_analysis_full.csv
results/a_feature_selection/a_analysis_reduced.csv
```

### B 생활 인프라 전처리 데이터

```text
data/processed/medical_by_region.csv
data/processed/bus_by_region.csv
data/processed/subway_by_region.csv
data/processed/welfare_by_region.csv
```

### B 생활 인프라 통합 데이터

```text
results/b_infrastructure/b_infrastructure.csv
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
- pdfplumber

---

## 현재 진행 상태

### 데이터 구축 및 전처리

- [x] 인구 데이터 수집 및 전처리
- [x] 청년 이동 데이터 수집 및 전처리
- [x] 경제 데이터 수집 및 보완
- [x] 생활 인프라 데이터 수집 및 전처리
- [x] 행정구역 코드 및 지역 단위 정리
- [x] A 데이터 통합
- [x] A 파생변수 생성
- [x] B 생활 인프라 데이터 통합
- [x] 노인 천 명당 생활 인프라 지표 생성

### 탐색 및 분석 준비

- [x] A 데이터 EDA
- [x] 이상치 검증
- [x] 시도별 요약
- [x] A 분석 후보 변수 정리
- [ ] A·B 데이터 최종 결합
- [ ] 최종 분석 변수 선정

### 최종 분석

- [ ] StandardScaler 적용
- [ ] K-Means 군집분석
- [ ] 군집 특성 해석
- [ ] 지도 시각화
- [ ] 최종 미스매치 분석

---

## 문서

### A 담당

상세 전처리 및 분석 문서:

```text
docs/README_A.md
```

데이터 사전:

```text
docs/data_dictionary_a.md
```

### B 담당

상세 전처리 및 분석 문서:

```text
docs/README_B.md
```

데이터 사전:

```text
docs/data_dictionary_b.md
```