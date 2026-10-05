import pandas as pd
import geopandas as gpd
from pathlib import Path

# -------------------------
# 경로
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "infrastructure"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
BOUNDARY_DIR = RAW_DIR / "boundary"

subway_path = RAW_DIR / "전체_도시철도역사정보_20260630.xlsx"
boundary_path = BOUNDARY_DIR / "bnd_sigungu_00_2025_2Q.shp"

# -------------------------
# 1. 도시철도 데이터
# -------------------------
df = pd.read_excel(
    subway_path,
    sheet_name="표준데이터 역사"
)

original_count = len(df)

print("원본 행 수:", original_count)

# -------------------------
# 2. 좌표 → 공간 데이터
# -------------------------
subway_geo = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["역경도"],
        df["역위도"]
    ),
    crs="EPSG:4326"
)

# -------------------------
# 3. 시군구 경계
# -------------------------
sigungu = gpd.read_file(boundary_path)

subway_geo = subway_geo.to_crs(sigungu.crs)

# -------------------------
# 4. 역 → 시군구 공간 매칭
# -------------------------
matched = gpd.sjoin(
    subway_geo,
    sigungu[
        ["SIGUNGU_CD", "SIGUNGU_NM", "geometry"]
    ],
    how="left",
    predicate="within"
)

print("\n시군구 매칭 성공:", matched["SIGUNGU_CD"].notna().sum())
print("시군구 매칭 실패:", matched["SIGUNGU_CD"].isna().sum())

# 성공 데이터만 사용
matched = matched.dropna(subset=["SIGUNGU_CD"]).copy()

# -------------------------
# 5. 시도명 생성
# -------------------------
sido_map = {
    "11": "서울특별시",
    "21": "부산광역시",
    "22": "대구광역시",
    "23": "인천광역시",
    "24": "광주광역시",
    "25": "대전광역시",
    "26": "울산광역시",
    "29": "세종특별자치시",
    "31": "경기도",
    "32": "강원특별자치도",
    "33": "충청북도",
    "34": "충청남도",
    "35": "전북특별자치도",
    "36": "전라남도",
    "37": "경상북도",
    "38": "경상남도",
    "39": "제주특별자치도"
}

matched["시도코드"] = (
    matched["SIGUNGU_CD"]
    .astype(str)
    .str[:2]
)

matched["시도명"] = matched["시도코드"].map(sido_map)
matched["시군구명"] = matched["SIGUNGU_NM"]

print("시도명 변환 실패:", matched["시도명"].isna().sum())

# -------------------------
# 6. 물리적 역사 기준 중복 제거
# 같은 시군구 + 같은 역사명 = 1개 역
# -------------------------
stations = matched.drop_duplicates(
    subset=["시도명", "시군구명", "역사명"]
).copy()

print("\n노선별 원본 행 수:", len(matched))
print("중복 제거 후 실제 역사 수:", len(stations))
print("중복 제거된 행 수:", len(matched) - len(stations))

# -------------------------
# 7. 시군구별 철도역 수
# -------------------------
subway_count = (
    stations
    .groupby(["시도명", "시군구명"])
    .size()
    .reset_index(name="철도역수")
    .sort_values(["시도명", "시군구명"])
)

# -------------------------
# 8. 저장
# -------------------------
output_path = PROCESSED_DIR / "subway_by_region.csv"

subway_count.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

# -------------------------
# 9. 검증
# -------------------------
print("\n철도역이 존재하는 지역 수:", len(subway_count))
print("철도역 총합:", subway_count["철도역수"].sum())

print("\n앞 30개:")
print(subway_count.head(30))

print("\n시도별 철도역 수:")
print(
    subway_count
    .groupby("시도명")["철도역수"]
    .sum()
    .sort_values(ascending=False)
)

print("\n저장 완료:", output_path)