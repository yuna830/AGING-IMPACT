import pandas as pd
import geopandas as gpd
from pathlib import Path

# ==================================================
# 경로 설정
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "infrastructure"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
BOUNDARY_DIR = RAW_DIR / "boundary"

bus_path = RAW_DIR / "국토교통부_전국 버스정류장 위치정보_20251031.csv"
boundary_path = BOUNDARY_DIR / "bnd_sigungu_00_2025_2Q.shp"


# ==================================================
# 1. 버스 데이터 불러오기
# ==================================================

bus = pd.read_csv(
    bus_path,
    encoding="cp949"
)

original_count = len(bus)

print("원본 정류장 수:", original_count)


# ==================================================
# 2. 강원 고성 원본 데이터 확인
# ==================================================

print("\n===== 원본 도시명에 '고성' 포함 데이터 =====")

goseong_original = bus[
    bus["도시명"]
    .astype(str)
    .str.contains("고성", na=False)
].copy()

if len(goseong_original) == 0:
    print("없음")
else:
    print(
        goseong_original[
            [
                "정류장명",
                "위도",
                "경도",
                "도시명",
                "관리도시명"
            ]
        ].head(30).to_string(index=False)
    )

print(
    "\n고성 포함 원본 행 수:",
    len(goseong_original)
)


# ==================================================
# 3. 좌표 결측 제거
# ==================================================

bus = bus.dropna(
    subset=["위도", "경도"]
).copy()

coordinate_count = len(bus)

print(
    "\n좌표 존재 정류장 수:",
    coordinate_count
)


# ==================================================
# 4. 좌표 → 공간 데이터
# ==================================================

bus_geo = gpd.GeoDataFrame(
    bus,
    geometry=gpd.points_from_xy(
        bus["경도"],
        bus["위도"]
    ),
    crs="EPSG:4326"
)


# ==================================================
# 5. 시군구 행정경계 불러오기
# ==================================================

sigungu = gpd.read_file(
    boundary_path
)

# 버스 좌표계를 행정경계 좌표계에 맞춤
bus_geo = bus_geo.to_crs(
    sigungu.crs
)


# ==================================================
# 6. 공간 결합
# ==================================================

matched_all = gpd.sjoin(
    bus_geo,
    sigungu[
        [
            "SIGUNGU_CD",
            "SIGUNGU_NM",
            "geometry"
        ]
    ],
    how="left",
    predicate="within"
)


# ==================================================
# 7. 공간 매칭 실패 데이터 확인
# ==================================================

unmatched = matched_all[
    matched_all["SIGUNGU_CD"].isna()
].copy()

print(
    "\n공간 매칭 실패 정류장 수:",
    len(unmatched)
)


# ==================================================
# 8. 고성 원본 데이터가 공간결합 후 어디로 갔는지 확인
# ==================================================

print("\n===== 공간결합 후 '고성' 원본 데이터 확인 =====")

goseong_after = matched_all[
    matched_all["도시명"]
    .astype(str)
    .str.contains("고성", na=False)
].copy()

if len(goseong_after) == 0:

    print("없음")

else:

    print(
        goseong_after[
            [
                "정류장명",
                "도시명",
                "관리도시명",
                "위도",
                "경도",
                "SIGUNGU_CD",
                "SIGUNGU_NM"
            ]
        ].head(50).to_string(index=False)
    )

    print(
        "\n고성 원본 데이터의 공간매칭 결과:"
    )

    print(
        goseong_after[
            "SIGUNGU_NM"
        ].value_counts(
            dropna=False
        )
    )


# ==================================================
# 9. 매칭 성공 데이터만 사용
# ==================================================

matched = matched_all.dropna(
    subset=["SIGUNGU_CD"]
).copy()


# ==================================================
# 10. SIGUNGU_CD → 시도명
# ==================================================

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

matched["시도명"] = (
    matched["시도코드"]
    .map(sido_map)
)

# 시군구 역시 행정경계 기준
matched["시군구명"] = (
    matched["SIGUNGU_NM"]
)


print(
    "\n시도명 변환 실패:",
    matched["시도명"].isna().sum()
)


# ==================================================
# 11. 시군구별 버스정류장 수
# ==================================================

bus_count = (
    matched
    .groupby(
        ["시도명", "시군구명"]
    )
    .size()
    .reset_index(
        name="버스정류장수"
    )
    .sort_values(
        ["시도명", "시군구명"]
    )
)


# ==================================================
# 12. 강원특별자치도 최종 결과 확인
# ==================================================

print("\n===== 최종 강원 버스 지역 =====")

print(
    bus_count[
        bus_count["시도명"]
        == "강원특별자치도"
    ].to_string(index=False)
)


# ==================================================
# 13. 저장
# ==================================================

output_path = (
    PROCESSED_DIR /
    "bus_by_region.csv"
)

bus_count.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 14. 최종 검증
# ==================================================

final_count = (
    bus_count["버스정류장수"]
    .sum()
)

print("\n===== 최종 검증 =====")

print(
    "원본 정류장 수:",
    original_count
)

print(
    "좌표 존재 정류장 수:",
    coordinate_count
)

print(
    "공간 매칭 성공:",
    len(matched)
)

print(
    "공간 매칭 실패:",
    len(unmatched)
)

print(
    "최종 사용 정류장 수:",
    final_count
)

print(
    "전체 제외 정류장 수:",
    original_count - final_count
)

print(
    "지역 수:",
    len(bus_count)
)

print(
    "\n시도별 지역 수:"
)

print(
    bus_count
    .groupby("시도명")
    .size()
)

print(
    "\n저장 완료:",
    output_path
)