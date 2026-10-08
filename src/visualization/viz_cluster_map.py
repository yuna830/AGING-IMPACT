from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


# =========================================================
# 경로 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]

CLUSTER_PATH = (
    BASE_DIR
    / "results"
    / "final_kmeans"
    / "cluster_for_visualization.csv"
)

# SGIS 시군구 경계
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
    / "cluster_map"
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
# 분석 단위 지역명 변환
# =========================================================
def normalize_region_name(name):
    """
    일반시의 하위 행정구를 분석 단위인 시 단위로 통합한다.

    예:
    수원시 장안구 -> 수원시
    청주시 흥덕구 -> 청주시
    창원시 성산구 -> 창원시

    광역시의 중구, 동구 등은 그대로 유지한다.
    """
    name = str(name).strip()
    parts = name.split()

    if len(parts) >= 2 and parts[0].endswith("시"):
        return parts[0]

    return name


# =========================================================
# 데이터 불러오기
# =========================================================
cluster = pd.read_csv(
    CLUSTER_PATH,
    dtype={"지역코드": str},
)

boundary = gpd.read_file(BOUNDARY_PATH)

boundary["SIGUNGU_CD"] = (
    boundary["SIGUNGU_CD"]
    .astype(str)
    .str.strip()
)

print("클러스터 지역 수:", len(cluster))
print("원본 행정경계 수:", len(boundary))
print("경계 CRS:", boundary.crs)


# =========================================================
# SGIS 경계에 시도 정보 생성
# =========================================================
boundary["시도"] = (
    boundary["SIGUNGU_CD"]
    .str[:2]
    .map(SIDO_CODE_MAP)
)

if boundary["시도"].isna().any():
    print("\n[경고] 시도 변환 실패 코드")
    print(
        boundary.loc[
            boundary["시도"].isna(),
            ["SIGUNGU_CD", "SIGUNGU_NM"],
        ]
    )


# =========================================================
# 252개 경계를 분석 단위 229개로 변환
# =========================================================
boundary["지역명"] = boundary["SIGUNGU_NM"].apply(
    normalize_region_name
)

# 세종 명칭을 분석 데이터에 맞춤
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
# 클러스터 데이터 결합
# =========================================================
map_df = boundary_229.merge(
    cluster,
    on=["시도", "지역명"],
    how="left",
    validate="one_to_one",
)


# =========================================================
# 결합 검증
# =========================================================
matched = map_df["cluster"].notna().sum()
unmatched = map_df["cluster"].isna().sum()

print("클러스터 매칭 성공:", matched)
print("클러스터 미매칭:", unmatched)

if unmatched > 0:
    print("\n[미매칭 지역]")
    print(
        map_df.loc[
            map_df["cluster"].isna(),
            ["시도", "지역명"],
        ].to_string(index=False)
    )

if len(map_df) != 229 or matched != 229:
    raise ValueError(
        "행정경계와 클러스터 데이터가 229개 모두 "
        "매칭되지 않았습니다."
    )


# =========================================================
# 클러스터 확인
# =========================================================
print("\n클러스터별 지역 수")
print(
    map_df.groupby(
        ["cluster", "cluster_name"]
    ).size()
)


# =========================================================
# 클러스터 색상
# =========================================================
# 발표 자료에서 서로 확실하게 구분되도록 3색 사용
CLUSTER_COLORS = {
    1: "#4C78A8",
    2: "#E45756",
    3: "#59A14F",
}

CLUSTER_LABELS = {
    1: "일반도시_중간형",
    2: "고령화_청년유출형",
    3: "경제활동_청년유입형",
}

map_df["plot_color"] = map_df["cluster"].map(
    CLUSTER_COLORS
)


# =========================================================
# 전국 K=3 군집 지도
# =========================================================
fig, ax = plt.subplots(figsize=(11, 13))

map_df.plot(
    ax=ax,
    color=map_df["plot_color"],
    edgecolor="white",
    linewidth=0.35,
)

ax.set_title(
    "전국 시군구 K-Means 군집 분포 (K=3)",
    fontsize=18,
    fontweight="bold",
    pad=18,
)

ax.axis("off")


# =========================================================
# 범례
# =========================================================
legend_handles = [
    Patch(
        facecolor=CLUSTER_COLORS[cluster_id],
        edgecolor="none",
        label=f"Cluster {cluster_id} | "
              f"{CLUSTER_LABELS[cluster_id]}",
    )
    for cluster_id in [1, 2, 3]
]

ax.legend(
    handles=legend_handles,
    title="군집 유형",
    loc="lower left",
    fontsize=10,
    title_fontsize=11,
    frameon=True,
)


# =========================================================
# 저장
# =========================================================
plt.tight_layout()

output_path = OUTPUT_DIR / "cluster_map_k3.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# =========================================================
# 지도용 결합 데이터도 저장
# =========================================================
map_data_path = (
    OUTPUT_DIR
    / "cluster_map_data.csv"
)

map_df.drop(
    columns=["geometry", "plot_color"]
).to_csv(
    map_data_path,
    index=False,
    encoding="utf-8-sig",
)


print("\n===== 군집 지도 생성 완료 =====")
print("지도:", output_path)
print("결합 데이터:", map_data_path)