import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "infrastructure"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

file_path = RAW_DIR / "건강보험심사평가원_요양기관 개설 현황_20251231.csv"

df = pd.read_csv(file_path, encoding="cp949")

# 사용할 병원급 의료기관
hospital_types = [
    "상급종합병원",
    "종합병원",
    "병원",
    "요양병원",
    "정신병원"
]

# -------------------------
# 병원
# -------------------------
hospital = df[df["요양종별"].isin(hospital_types)]

hospital_count = (
    hospital
    .groupby(["시도명", "시군구명"])
    .size()
    .reset_index(name="병원수")
)

# -------------------------
# 약국
# -------------------------
pharmacy = df[df["요양종별"] == "약국"]

pharmacy_count = (
    pharmacy
    .groupby(["시도명", "시군구명"])
    .size()
    .reset_index(name="약국수")
)

# -------------------------
# 병원 + 약국 결합
# -------------------------
medical = pd.merge(
    hospital_count,
    pharmacy_count,
    on=["시도명", "시군구명"],
    how="outer"
)

medical[["병원수", "약국수"]] = (
    medical[["병원수", "약국수"]]
    .fillna(0)
    .astype(int)
)

medical = medical.sort_values(["시도명", "시군구명"])

# 저장
output_path = PROCESSED_DIR / "medical_by_region.csv"
medical.to_csv(output_path, index=False, encoding="utf-8-sig")

# 확인
print(medical.head(20))
print("\n지역 수:", len(medical))
print("병원 총합:", medical["병원수"].sum())
print("약국 총합:", medical["약국수"].sum())
print("\n저장 완료:", output_path)