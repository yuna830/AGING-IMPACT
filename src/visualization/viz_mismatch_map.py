from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


# =========================================================
# 경로 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]

MISMATCH_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
    / "mismatch_for_visualization.csv"
)

BOUNDARY_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "boundary"
    / "bnd_sigungu_00_2025_2Q.shp"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "visualization"
    / "mismatch_map"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 한글 폰트
# =========================================================
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# =========================================================
# SGIS 시도 코드
# =========================================================
SIDO_CODE_MAP = {
    "11": "서울",
    "21": "부산",
    "22": "대구",
    "23": "인천",
    "24": "광주",
    "25": "대전",
    "26": "울산",
    "29": "세종",
    "31": "경기",
    "32": "강원",
    "33": "충북",
    "34": "충남",
    "35": "전북",
    "36": "전남",
    "37": "경북",
    "38": "경남",
    "39": "제주",
}


# =========================================================
# 일반시 하위구 → 시 단위 통합
# =========================================================
def normalize_region_name(name):
    name = str(name).strip()
    parts = name.split()

    if len(parts) >= 2 and parts[0].endswith("시"):
        return parts[0]

    return name


# =========================================================
# 데이터 불러오기
# =========================================================
mismatch = pd.read_csv(
    MISMATCH_PATH,
    dtype={"지역코드": str},
)

boundary = gpd.read_file(BOUNDARY_PATH)

boundary["SIGUNGU_CD"] = (
    boundary["SIGUNGU_CD"]
    .astype(str)
    .str.strip()
)

print("미스매치 데이터 지역 수:", len(mismatch))
print("원본 행정경계 수:", len(boundary))
print("경계 CRS:", boundary.crs)


# =========================================================
# 필요한 컬럼 검증
# =========================================================
required_columns = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "고령화수요점수_100",
    "인프라공급점수_100",
    "미스매치점수_100",
    "미스매치순위",
    "우선검토지역",
]

missing_columns = [
    col for col in required_columns
    if col not in mismatch.columns
]

if missing_columns:
    raise ValueError(
        f"필요한 컬럼이 없습니다: {missing_columns}"
    )


# =========================================================
# 우선검토지역 Boolean 정리
# =========================================================
# CSV에서 True/False가 문자열로 읽히는 경우까지 대응
if mismatch["우선검토지역"].dtype == object:
    mismatch["우선검토지역"] = (
        mismatch["우선검토지역"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "true": True,
            "false": False,
            "1": True,
            "0": False,
        })
    )

if mismatch["우선검토지역"].isna().any():
    raise ValueError(
        "우선검토지역 컬럼에 해석할 수 없는 값이 있습니다."
    )


# =========================================================
# SGIS 경계 → 시도 생성
# =========================================================
boundary["시도"] = (
    boundary["SIGUNGU_CD"]
    .str[:2]
    .map(SIDO_CODE_MAP)
)

if boundary["시도"].isna().any():
    print("\n[경고] 시도 변환 실패")
    print(
        boundary.loc[
            boundary["시도"].isna(),
            ["SIGUNGU_CD", "SIGUNGU_NM"],
        ]
    )


# =========================================================
# 252개 경계 → 분석 단위 229개
# =========================================================
boundary["지역명"] = boundary["SIGUNGU_NM"].apply(
    normalize_region_name
)

boundary.loc[
    boundary["시도"] == "세종",
    "지역명",
] = "세종특별자치시"

boundary_229 = boundary.dissolve(
    by=["시도", "지역명"],
    as_index=False,
)

print("통합 후 행정경계 수:", len(boundary_229))


# =========================================================
# 미스매치 데이터 결합
# =========================================================
map_df = boundary_229.merge(
    mismatch,
    on=["시도", "지역명"],
    how="left",
    validate="one_to_one",
)

matched = map_df["미스매치점수_100"].notna().sum()
unmatched = map_df["미스매치점수_100"].isna().sum()

print("미스매치 매칭 성공:", matched)
print("미스매치 미매칭:", unmatched)

if unmatched > 0:
    print("\n[미매칭 지역]")
    print(
        map_df.loc[
            map_df["미스매치점수_100"].isna(),
            ["시도", "지역명"],
        ].to_string(index=False)
    )

if len(map_df) != 229 or matched != 229:
    raise ValueError(
        "행정경계와 미스매치 데이터가 "
        "229개 모두 매칭되지 않았습니다."
    )


# =========================================================
# 기본 통계
# =========================================================
priority_count = int(
    map_df["우선검토지역"].sum()
)

print("\n미스매치 점수 범위:")
print(
    map_df["미스매치점수_100"].describe()
)

print("\n우선검토지역 수:", priority_count)


# =========================================================
# 1. 미스매치 점수 지도
# =========================================================
fig, ax = plt.subplots(figsize=(11, 13))

map_df.plot(
    column="미스매치점수_100",
    cmap="YlOrRd",
    linewidth=0.3,
    edgecolor="white",
    legend=True,
    ax=ax,
    legend_kwds={
        "label": "미스매치 점수",
        "shrink": 0.65,
    },
)

ax.set_title(
    "전국 시군구 고령화 수요-인프라 공급 미스매치",
    fontsize=18,
    fontweight="bold",
    pad=18,
)

ax.axis("off")

plt.tight_layout()

score_map_path = (
    OUTPUT_DIR
    / "mismatch_score_map.png"
)

plt.savefig(
    score_map_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("[완료] 미스매치 점수 지도")


# =========================================================
# 2. 우선검토지역 강조 지도
# =========================================================
fig, ax = plt.subplots(figsize=(11, 13))

# 전체 지역 배경
map_df.plot(
    ax=ax,
    color="#E6E6E6",
    edgecolor="white",
    linewidth=0.3,
)

# 우선검토지역
priority_df = map_df[
    map_df["우선검토지역"] == True
].copy()

priority_df.plot(
    ax=ax,
    color="#D62728",
    edgecolor="white",
    linewidth=0.45,
)

ax.set_title(
    "고령화 수요 대비 인프라 공급 우선검토지역",
    fontsize=18,
    fontweight="bold",
    pad=18,
)

ax.axis("off")

legend_handles = [
    Patch(
        facecolor="#D62728",
        edgecolor="none",
        label=f"우선검토지역 ({priority_count}개)",
    ),
    Patch(
        facecolor="#E6E6E6",
        edgecolor="none",
        label="기타 지역",
    ),
]

ax.legend(
    handles=legend_handles,
    loc="lower left",
    title="지역 구분",
    fontsize=10,
    title_fontsize=11,
    frameon=True,
)

plt.tight_layout()

priority_map_path = (
    OUTPUT_DIR
    / "priority_regions_map.png"
)

plt.savefig(
    priority_map_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print("[완료] 우선검토지역 지도")


# =========================================================
# 3. 우선검토지역 목록 저장
# =========================================================
priority_columns = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "고령화수요점수_100",
    "인프라공급점수_100",
    "미스매치점수_100",
    "미스매치순위",
]

priority_table = (
    priority_df[priority_columns]
    .sort_values(
        "미스매치순위",
        ascending=True,
    )
)

priority_table_path = (
    OUTPUT_DIR
    / "priority_regions.csv"
)

priority_table.to_csv(
    priority_table_path,
    index=False,
    encoding="utf-8-sig",
)


# =========================================================
# 4. 지도 결합 데이터 저장
# =========================================================
map_data_path = (
    OUTPUT_DIR
    / "mismatch_map_data.csv"
)

map_df.drop(
    columns="geometry"
).to_csv(
    map_data_path,
    index=False,
    encoding="utf-8-sig",
)


# =========================================================
# 상위 20개 확인
# =========================================================
top20 = (
    map_df[
        [
            "시도",
            "지역명",
            "미스매치점수_100",
            "미스매치순위",
            "우선검토지역",
        ]
    ]
    .sort_values(
        "미스매치순위"
    )
    .head(20)
)

print("\n===== 미스매치 상위 20개 지역 =====")
print(top20.to_string(index=False))


print("\n===== 미스매치 지도 생성 완료 =====")
print("점수 지도:", score_map_path)
print("우선검토 지도:", priority_map_path)
print("우선검토지역 목록:", priority_table_path)
print("지도 결합 데이터:", map_data_path)