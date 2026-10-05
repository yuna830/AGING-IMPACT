import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def normalize_sigungu(name, sido=None):
    name = str(name).strip()

    # 세종은 시군구 하위구분이 없는 단층제
    if sido == "세종특별자치시":
        return "세종시"

    parts = name.split()

    # 일반시의 행정구 → 상위 시로 통합
    if len(parts) >= 2 and parts[0].endswith("시"):
        return parts[0]

    return name


# ==================================================
# 1. 데이터 불러오기
# ==================================================

medical = pd.read_csv(
    PROCESSED_DIR / "medical_by_region.csv"
)

bus = pd.read_csv(
    PROCESSED_DIR / "bus_by_region.csv"
)

subway = pd.read_csv(
    PROCESSED_DIR / "subway_by_region.csv"
)

welfare = pd.read_csv(
    PROCESSED_DIR / "welfare_by_region.csv"
)


# ==================================================
# 2. 의료 / 버스 / 철도 지역 단위 통일
# ==================================================

for df in [medical, bus, subway]:
    df["시군구명"] = df.apply(
        lambda row: normalize_sigungu(
            row["시군구명"],
            row["시도명"]
        ),
        axis=1
    )


medical = (
    medical
    .groupby(
        ["시도명", "시군구명"],
        as_index=False
    )[["병원수", "약국수"]]
    .sum()
)


bus = (
    bus
    .groupby(
        ["시도명", "시군구명"],
        as_index=False
    )["버스정류장수"]
    .sum()
)


subway = (
    subway
    .groupby(
        ["시도명", "시군구명"],
        as_index=False
    )["철도역수"]
    .sum()
)


# ==================================================
# 3. 복지 데이터를 기준으로 병합
# ==================================================

result = welfare.merge(
    medical,
    on=["시도명", "시군구명"],
    how="left"
)

result = result.merge(
    bus,
    on=["시도명", "시군구명"],
    how="left"
)

result = result.merge(
    subway,
    on=["시도명", "시군구명"],
    how="left"
)


# ==================================================
# 4. 결측값 처리
# ==================================================

# 도시철도역이 매칭되지 않은 지역은
# 도시철도역이 없는 지역이므로 0 처리
result["철도역수"] = (
    result["철도역수"]
    .fillna(0)
    .astype(int)
)

# 강원 고성군 버스정류장 수는
# 원자료에 데이터가 없어 결측값(NaN)으로 유지


# ==================================================
# 5. 노인 인구 1,000명당 인프라 지표
# ==================================================

result["노인천명당_병원수"] = (
    result["병원수"]
    / result["65세이상인구"]
    * 1000
)

result["노인천명당_약국수"] = (
    result["약국수"]
    / result["65세이상인구"]
    * 1000
)

result["노인천명당_복지시설수"] = (
    result["노인복지시설수"]
    / result["65세이상인구"]
    * 1000
)

result["노인천명당_버스정류장수"] = (
    result["버스정류장수"]
    / result["65세이상인구"]
    * 1000
)

result["노인천명당_철도역수"] = (
    result["철도역수"]
    / result["65세이상인구"]
    * 1000
)


# 보기 좋게 소수점 3자리
rate_cols = [
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수"
]

result[rate_cols] = result[rate_cols].round(3)


# ==================================================
# 6. 최종 컬럼 순서
# ==================================================

final_cols = [
    "시도명",
    "시군구명",
    "65세이상인구",

    "병원수",
    "약국수",

    "주거복지시설수",
    "의료복지시설수",
    "여가복지시설수",
    "재가복지시설수",
    "노인일자리지원기관수",
    "학대피해노인쉼터수",
    "노인복지시설수",

    "버스정류장수",
    "철도역수",

    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수"
]

result = result[final_cols]


# ==================================================
# 7. 최종 저장
# ==================================================

OUTPUT_DIR = BASE_DIR / "results" / "b_infrastructure"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_path = OUTPUT_DIR / "b_infrastructure.csv"

result.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 8. 최종 검증
# ==================================================

print("\n===== B 최종 데이터 =====")

print("지역 수:", len(result))

print("\n결측치:")
print(result.isna().sum())

print("\n시설 총합:")
print(
    result[
        [
            "병원수",
            "약국수",
            "노인복지시설수",
            "버스정류장수",
            "철도역수"
        ]
    ].sum()
)

print("\n강원 고성군 확인:")
print(
    result[
        (result["시도명"] == "강원특별자치도")
        & (result["시군구명"] == "고성군")
    ].to_string(index=False)
)

print("\n샘플:")
print(result.head(10).to_string(index=False))

print("\n저장 완료:")
print(output_path)