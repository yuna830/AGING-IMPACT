from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from libpysal.weights import Queen, W
from esda.moran import Moran, Moran_Local


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SHAPEFILE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "boundary"
    / "bnd_sigungu_00_2025_2Q.shp"
)

MISMATCH_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
    / "final_mismatch_analysis.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "spatial_analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 한글 폰트
# ============================================================

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# SGIS 시도 코드
# ============================================================

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


# ============================================================
# 분석 단위 지역명 변환
# ============================================================

def normalize_region_name(name: str) -> str:
    """
    일반시의 하위 행정구를 상위 시 단위로 통합.

    예:
    수원시 장안구 -> 수원시
    고양시 덕양구 -> 고양시
    청주시 흥덕구 -> 청주시
    전주시 완산구 -> 전주시
    창원시 성산구 -> 창원시

    광역시의 중구, 동구 등은 그대로 유지.
    """

    name = str(name).strip()
    parts = name.split()

    if (
        len(parts) >= 2
        and parts[0].endswith("시")
    ):
        return parts[0]

    return name


# ============================================================
# Queen + 최근접 이웃 보완 공간가중치
# ============================================================

def build_hybrid_weights(
    gdf: gpd.GeoDataFrame,
):
    """
    기본적으로 Queen Contiguity를 사용.

    단, Queen 기준 이웃이 하나도 없는 지역(island)에 대해서만
    중심점 기준 가장 가까운 지역 1개를 이웃으로 추가.

    추가 연결은 양방향으로 구성.
    """

    # --------------------------------------------------------
    # 1. 기본 Queen 가중치
    # --------------------------------------------------------

    queen_w = Queen.from_dataframe(
        gdf,
        ids=gdf.index.tolist(),
    )

    original_islands = list(
        queen_w.islands
    )

    # Queen neighbor dictionary 복사
    neighbors = {
        region_id: list(neighbor_list)
        for region_id, neighbor_list
        in queen_w.neighbors.items()
    }

    # --------------------------------------------------------
    # 2. 중심점 좌표 계산
    # --------------------------------------------------------

    centroids = (
        gdf.geometry.centroid
    )

    coords = np.column_stack(
        [
            centroids.x.to_numpy(),
            centroids.y.to_numpy(),
        ]
    )

    added_links = []

    # --------------------------------------------------------
    # 3. island에 대해서만 최근접 지역 추가
    # --------------------------------------------------------

    for island_id in original_islands:

        island_coord = coords[
            island_id
        ]

        distances = np.sqrt(
            np.sum(
                (
                    coords
                    - island_coord
                )
                ** 2,
                axis=1,
            )
        )

        # 자기 자신 제외
        distances[
            island_id
        ] = np.inf

        nearest_id = int(
            np.argmin(
                distances
            )
        )

        nearest_distance = float(
            distances[
                nearest_id
            ]
        )

        # island -> nearest
        if (
            nearest_id
            not in neighbors[
                island_id
            ]
        ):
            neighbors[
                island_id
            ].append(
                nearest_id
            )

        # nearest -> island
        if (
            island_id
            not in neighbors[
                nearest_id
            ]
        ):
            neighbors[
                nearest_id
            ].append(
                island_id
            )

        added_links.append(
            {
                "island_index":
                    island_id,

                "island_시도":
                    gdf.loc[
                        island_id,
                        "시도",
                    ],

                "island_지역명":
                    gdf.loc[
                        island_id,
                        "지역명",
                    ],

                "nearest_index":
                    nearest_id,

                "nearest_시도":
                    gdf.loc[
                        nearest_id,
                        "시도",
                    ],

                "nearest_지역명":
                    gdf.loc[
                        nearest_id,
                        "지역명",
                    ],

                "중심점거리_m":
                    nearest_distance,
            }
        )

    # --------------------------------------------------------
    # 4. 새로운 가중치 행렬 생성
    # --------------------------------------------------------

    hybrid_w = W(
        neighbors=neighbors
    )

    # Row-standardization
    hybrid_w.transform = "r"

    links_df = pd.DataFrame(
        added_links
    )

    return (
        hybrid_w,
        original_islands,
        links_df,
    )


# ============================================================
# 1. 입력 파일 확인
# ============================================================

print("\n========================================")
print("1. 입력 파일 확인")
print("========================================")

for path in [
    SHAPEFILE_PATH,
    MISMATCH_PATH,
]:

    if not path.exists():

        raise FileNotFoundError(
            f"필요한 파일이 없습니다:\n{path}"
        )

    print(
        "[OK]",
        path.relative_to(
            BASE_DIR
        ),
    )


# ============================================================
# 2. 데이터 불러오기
# ============================================================

print("\n========================================")
print("2. 데이터 불러오기")
print("========================================")

boundary = gpd.read_file(
    SHAPEFILE_PATH
)

mismatch = pd.read_csv(
    MISMATCH_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

mismatch["지역코드"] = (
    mismatch[
        "지역코드"
    ]
    .astype(str)
    .str.zfill(5)
)

print(
    f"원본 경계 수: "
    f"{len(boundary)}"
)

print(
    f"미스매치 분석 지역 수: "
    f"{len(mismatch)}"
)

print(
    f"경계 CRS: "
    f"{boundary.crs}"
)


# ============================================================
# 3. SGIS 시도 정보 생성
# ============================================================

print("\n========================================")
print("3. SGIS 시도 정보 생성")
print("========================================")

boundary["SIGUNGU_CD"] = (
    boundary[
        "SIGUNGU_CD"
    ]
    .astype(str)
    .str.strip()
)

boundary["시도"] = (
    boundary[
        "SIGUNGU_CD"
    ]
    .str[:2]
    .map(
        SIDO_CODE_MAP
    )
)

failed_sido = boundary[
    boundary[
        "시도"
    ].isna()
]

print(
    f"시도 변환 실패 수: "
    f"{len(failed_sido)}"
)

if len(failed_sido) > 0:

    print(
        failed_sido[
            [
                "SIGUNGU_CD",
                "SIGUNGU_NM",
            ]
        ].to_string(
            index=False
        )
    )

    raise ValueError(
        "시도 코드 변환 실패"
    )


# ============================================================
# 4. 분석 단위 지역명 변환
# ============================================================

print("\n========================================")
print("4. 분석 단위 지역명 변환")
print("========================================")

boundary["지역명"] = (
    boundary[
        "SIGUNGU_NM"
    ]
    .apply(
        normalize_region_name
    )
)

# 세종 명칭 통일
boundary.loc[
    boundary[
        "시도"
    ]
    == "세종",
    "지역명",
] = "세종특별자치시"


# ============================================================
# 5. 252개 → 229개 분석 단위
# ============================================================

print("\n========================================")
print("5. 252개 경계를 229개 분석 단위로 통합")
print("========================================")

boundary_229 = (
    boundary
    .dissolve(
        by=[
            "시도",
            "지역명",
        ],
        as_index=False,
    )
)

print(
    f"통합 후 경계 수: "
    f"{len(boundary_229)}"
)

if (
    len(boundary_229)
    != 229
):

    raise ValueError(
        "통합 후 경계 수가 "
        f"229개가 아닙니다: "
        f"{len(boundary_229)}"
    )


# ============================================================
# 6. 미스매치 데이터 결합
# ============================================================

print("\n========================================")
print("6. 미스매치 데이터 결합")
print("========================================")

gdf = boundary_229.merge(
    mismatch,
    on=[
        "시도",
        "지역명",
    ],
    how="left",
    validate="one_to_one",
)

matched = int(
    gdf[
        "미스매치점수_100"
    ]
    .notna()
    .sum()
)

unmatched = int(
    gdf[
        "미스매치점수_100"
    ]
    .isna()
    .sum()
)

print(
    f"최종 경계 수: "
    f"{len(gdf)}"
)

print(
    f"미스매치 매칭 성공: "
    f"{matched}"
)

print(
    f"미스매치 미매칭: "
    f"{unmatched}"
)

if unmatched > 0:

    print(
        "\n[미매칭 지역]"
    )

    print(
        gdf.loc[
            gdf[
                "미스매치점수_100"
            ]
            .isna(),
            [
                "시도",
                "지역명",
            ],
        ]
        .to_string(
            index=False
        )
    )

if (
    len(gdf) != 229
    or matched != 229
):

    raise ValueError(
        "행정경계와 미스매치 데이터가 "
        "229개 모두 매칭되지 않았습니다."
    )

print(
    "229 / 229 지역 매칭 완료"
)


# ============================================================
# 7. Geometry 검증
# ============================================================

print("\n========================================")
print("7. geometry 검증")
print("========================================")

invalid_count = int(
    (
        ~gdf.geometry.is_valid
    ).sum()
)

print(
    f"유효하지 않은 geometry 수: "
    f"{invalid_count}"
)

if invalid_count > 0:

    gdf[
        "geometry"
    ] = (
        gdf.geometry
        .buffer(0)
    )

    print(
        "buffer(0) 방식으로 geometry 보정"
    )


# ============================================================
# 8. Queen + 최근접 이웃 보완
# ============================================================

print("\n========================================")
print("8. Queen + 최근접 이웃 보완")
print("========================================")

gdf = (
    gdf
    .reset_index(
        drop=True
    )
)

(
    w,
    original_islands,
    added_links_df,
) = build_hybrid_weights(
    gdf
)

print(
    f"기존 Queen island 수: "
    f"{len(original_islands)}"
)

if len(original_islands) > 0:

    print(
        "\n[기존 Queen island]"
    )

    print(
        gdf.loc[
            original_islands,
            [
                "시도",
                "지역명",
            ],
        ]
        .to_string(
            index=False
        )
    )


# ============================================================
# 9. 추가된 최근접 연결 확인
# ============================================================

print("\n========================================")
print("9. Island 최근접 연결")
print("========================================")

if not added_links_df.empty:

    display_links = (
        added_links_df[
            [
                "island_시도",
                "island_지역명",
                "nearest_시도",
                "nearest_지역명",
                "중심점거리_m",
            ]
        ]
        .copy()
    )

    display_links[
        "중심점거리_km"
    ] = (
        display_links[
            "중심점거리_m"
        ]
        / 1000
    )

    print(
        display_links[
            [
                "island_시도",
                "island_지역명",
                "nearest_시도",
                "nearest_지역명",
                "중심점거리_km",
            ]
        ]
        .round(
            {
                "중심점거리_km": 2,
            }
        )
        .to_string(
            index=False
        )
    )


# ============================================================
# 10. 보정 후 공간가중치 검증
# ============================================================

print("\n========================================")
print("10. 보정 후 공간가중치 검증")
print("========================================")

final_neighbor_counts = np.array(
    [
        len(
            w.neighbors[i]
        )
        for i in gdf.index
    ]
)

final_islands = list(
    w.islands
)

print(
    f"평균 이웃 수: "
    f"{final_neighbor_counts.mean():.2f}"
)

print(
    f"최소 이웃 수: "
    f"{final_neighbor_counts.min()}"
)

print(
    f"최대 이웃 수: "
    f"{final_neighbor_counts.max()}"
)

print(
    f"보정 후 island 수: "
    f"{len(final_islands)}"
)

print(
    f"연결 컴포넌트 수: "
    f"{w.n_components}"
)

if len(final_islands) > 0:

    print(
        "\n[보정 후에도 이웃이 없는 지역]"
    )

    print(
        gdf.loc[
            final_islands,
            [
                "시도",
                "지역명",
            ],
        ]
        .to_string(
            index=False
        )
    )

else:

    print(
        "모든 지역이 최소 1개 이상의 이웃을 가짐"
    )


# ============================================================
# 11. 최근접 연결 정보 저장
# ============================================================

added_links_df.to_csv(
    OUTPUT_DIR
    / "island_knn_links.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 12. Global Moran's I
# ============================================================

print("\n========================================")
print("11. Global Moran's I")
print("========================================")

y = (
    gdf[
        "미스매치점수_100"
    ]
    .astype(float)
    .to_numpy()
)

moran = Moran(
    y,
    w,
    permutations=9999,
)

print(
    f"Moran's I: "
    f"{moran.I:.6f}"
)

print(
    f"Expected I: "
    f"{moran.EI:.6f}"
)

print(
    f"Permutation p-value: "
    f"{moran.p_sim:.6f}"
)

print(
    f"z-score: "
    f"{moran.z_sim:.6f}"
)


# ============================================================
# 13. 표준화 미스매치 + Spatial Lag
# ============================================================

print("\n========================================")
print("12. Moran Scatterplot 데이터 생성")
print("========================================")

z = (
    y - y.mean()
) / y.std(
    ddof=0
)

spatial_lag = np.zeros(
    len(gdf)
)

for i in gdf.index:

    neighbors = (
        w.neighbors[i]
    )

    weights = (
        w.weights[i]
    )

    spatial_lag[i] = sum(
        weight
        * z[neighbor]
        for neighbor, weight
        in zip(
            neighbors,
            weights,
        )
    )


scatter_df = pd.DataFrame(
    {
        "지역코드":
            gdf[
                "지역코드"
            ],

        "시도":
            gdf[
                "시도"
            ],

        "지역명":
            gdf[
                "지역명"
            ],

        "미스매치점수_100":
            y,

        "미스매치표준화값":
            z,

        "공간지연값":
            spatial_lag,
    }
)

scatter_df.to_csv(
    OUTPUT_DIR
    / "moran_scatter_data.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 14. Moran Scatterplot
# ============================================================

print("\n========================================")
print("13. Moran Scatterplot 생성")
print("========================================")

fig, ax = plt.subplots(
    figsize=(10, 8)
)

ax.scatter(
    z,
    spatial_lag,
    alpha=0.7,
    s=35,
)

ax.axhline(
    0,
    linewidth=1,
)

ax.axvline(
    0,
    linewidth=1,
)

x_line = np.linspace(
    z.min(),
    z.max(),
    100,
)

ax.plot(
    x_line,
    moran.I
    * x_line,
    linestyle="--",
    linewidth=2,
)

ax.set_title(
    "미스매치 점수 Moran Scatterplot",
    fontsize=15,
)

ax.set_xlabel(
    "표준화 미스매치 점수"
)

ax.set_ylabel(
    "공간 지연값"
)

ax.text(
    0.02,
    0.97,
    (
        f"Moran's I = "
        f"{moran.I:.3f}\n"
        f"Permutation p = "
        f"{moran.p_sim:.4f}"
    ),
    transform=ax.transAxes,
    verticalalignment="top",
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "01_moran_scatterplot.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 15. Local Moran's I
# ============================================================

print("\n========================================")
print("14. Local Moran's I (LISA)")
print("========================================")

lisa = Moran_Local(
    y,
    w,
    permutations=9999,
)


# ============================================================
# 16. LISA 유형 분류
# ============================================================

quadrant_map = {
    1: "HH",
    2: "LH",
    3: "LL",
    4: "HL",
}

gdf[
    "LISA_사분면"
] = [
    quadrant_map.get(
        int(q),
        "NA",
    )
    for q in lisa.q
]

gdf[
    "LISA_I"
] = lisa.Is

gdf[
    "LISA_p값"
] = lisa.p_sim

gdf[
    "LISA_유의"
] = (
    gdf[
        "LISA_p값"
    ]
    < 0.05
)

gdf[
    "LISA_유형"
] = np.where(
    gdf[
        "LISA_유의"
    ],
    gdf[
        "LISA_사분면"
    ],
    "Not Significant",
)


# ============================================================
# 17. LISA 유형별 개수
# ============================================================

print("\n========================================")
print("15. LISA 유형별 개수")
print("========================================")

lisa_counts = (
    gdf[
        "LISA_유형"
    ]
    .value_counts()
)

print(
    lisa_counts.to_string()
)


# ============================================================
# 18. High-High 지역
# ============================================================

print("\n========================================")
print("16. High-High 지역")
print("========================================")

hh_df = (
    gdf[
        gdf[
            "LISA_유형"
        ]
        == "HH"
    ][
        [
            "지역코드",
            "시도",
            "지역명",
            "cluster",
            "cluster_name",
            "미스매치순위",
            "미스매치점수_100",
            "LISA_I",
            "LISA_p값",
        ]
    ]
    .sort_values(
        "미스매치점수_100",
        ascending=False,
    )
)

if len(hh_df) > 0:

    print(
        hh_df
        .round(4)
        .to_string(
            index=False
        )
    )

else:

    print(
        "유의한 High-High 지역 없음"
    )


# ============================================================
# 19. Low-Low / HL / LH도 각각 저장 가능하도록 분리
# ============================================================

ll_df = (
    gdf[
        gdf[
            "LISA_유형"
        ]
        == "LL"
    ]
    .copy()
)

hl_df = (
    gdf[
        gdf[
            "LISA_유형"
        ]
        == "HL"
    ]
    .copy()
)

lh_df = (
    gdf[
        gdf[
            "LISA_유형"
        ]
        == "LH"
    ]
    .copy()
)


# ============================================================
# 20. LISA 전체 결과 저장
# ============================================================

lisa_result_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "미스매치순위",
    "미스매치점수_100",
    "고령화수요점수_100",
    "인프라공급점수_100",
    "LISA_I",
    "LISA_p값",
    "LISA_사분면",
    "LISA_유의",
    "LISA_유형",
]

lisa_results = (
    gdf[
        lisa_result_cols
    ]
    .copy()
)

lisa_results.to_csv(
    OUTPUT_DIR
    / "lisa_results.csv",
    index=False,
    encoding="utf-8-sig",
)

hh_df.to_csv(
    OUTPUT_DIR
    / "high_high_regions.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 21. LISA 지도
# ============================================================

print("\n========================================")
print("17. LISA 지도 생성")
print("========================================")

COLOR_MAP = {
    "HH": "#D73027",
    "LL": "#4575B4",
    "HL": "#FDAE61",
    "LH": "#74ADD1",
    "Not Significant": "#D9D9D9",
}

LABEL_MAP = {
    "HH": "High-High",
    "LL": "Low-Low",
    "HL": "High-Low",
    "LH": "Low-High",
    "Not Significant": "Not Significant",
}

fig, ax = plt.subplots(
    figsize=(11, 13)
)

for category in [
    "Not Significant",
    "LL",
    "LH",
    "HL",
    "HH",
]:

    subset = gdf[
        gdf[
            "LISA_유형"
        ]
        == category
    ]

    if subset.empty:
        continue

    subset.plot(
        ax=ax,
        color=COLOR_MAP[
            category
        ],
        edgecolor="white",
        linewidth=0.35,
        label=LABEL_MAP[
            category
        ],
    )

ax.set_title(
    "생활 인프라 미스매치 LISA Cluster Map",
    fontsize=17,
    fontweight="bold",
    pad=15,
)

ax.axis(
    "off"
)

ax.legend(
    title="LISA 유형 (p < 0.05)",
    loc="lower left",
    fontsize=9,
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "02_lisa_cluster_map.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 22. Moran permutation distribution
# ============================================================

print("\n========================================")
print("18. Moran permutation 분포 저장")
print("========================================")

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.hist(
    moran.sim,
    bins=40,
    alpha=0.8,
)

ax.axvline(
    moran.I,
    linewidth=2,
    label=(
        f"Observed I = "
        f"{moran.I:.3f}"
    ),
)

ax.axvline(
    moran.EI,
    linestyle="--",
    linewidth=2,
    label=(
        f"Expected I = "
        f"{moran.EI:.3f}"
    ),
)

ax.set_title(
    "Global Moran's I Permutation Distribution"
)

ax.set_xlabel(
    "Moran's I"
)

ax.set_ylabel(
    "Frequency"
)

ax.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "03_moran_permutation_distribution.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 23. 공간통계 요약
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "spatial_analysis_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - 공간 통계 분석\n"
    )

    f.write(
        "=" * 70
        + "\n\n"
    )

    # --------------------------------------------------------
    # 분석 방법
    # --------------------------------------------------------

    f.write(
        "[분석 방법]\n"
    )

    f.write(
        "기본 공간 가중치: "
        "Queen Contiguity\n"
    )

    f.write(
        "Queen 기준 이웃이 없는 지역: "
        "중심점 기준 최근접 지역 1개 연결\n"
    )

    f.write(
        "최근접 연결: 양방향 처리\n"
    )

    f.write(
        "공간 가중치 표준화: "
        "Row-standardized\n"
    )

    f.write(
        "Permutation 횟수: 9,999회\n"
    )

    f.write(
        "LISA 유의수준: p < 0.05\n\n"
    )

    # --------------------------------------------------------
    # Queen 보완
    # --------------------------------------------------------

    f.write(
        "[Queen 최근접 보완]\n"
    )

    f.write(
        f"기존 Queen island 수: "
        f"{len(original_islands)}\n"
    )

    f.write(
        f"보정 후 island 수: "
        f"{len(final_islands)}\n"
    )

    f.write(
        f"공간가중치 연결 컴포넌트 수: "
        f"{w.n_components}\n\n"
    )

    if not added_links_df.empty:

        f.write(
            "[추가된 최근접 연결]\n"
        )

        temp_links = (
            added_links_df[
                [
                    "island_시도",
                    "island_지역명",
                    "nearest_시도",
                    "nearest_지역명",
                    "중심점거리_m",
                ]
            ]
            .copy()
        )

        temp_links[
            "중심점거리_km"
        ] = (
            temp_links[
                "중심점거리_m"
            ]
            / 1000
        )

        f.write(
            temp_links[
                [
                    "island_시도",
                    "island_지역명",
                    "nearest_시도",
                    "nearest_지역명",
                    "중심점거리_km",
                ]
            ]
            .round(
                {
                    "중심점거리_km":
                        2,
                }
            )
            .to_string(
                index=False
            )
        )

        f.write(
            "\n\n"
        )

    # --------------------------------------------------------
    # Global Moran
    # --------------------------------------------------------

    f.write(
        "[Global Moran's I]\n"
    )

    f.write(
        f"Moran's I: "
        f"{moran.I:.6f}\n"
    )

    f.write(
        f"Expected I: "
        f"{moran.EI:.6f}\n"
    )

    f.write(
        f"Permutation p-value: "
        f"{moran.p_sim:.6f}\n"
    )

    f.write(
        f"z-score: "
        f"{moran.z_sim:.6f}\n\n"
    )

    # --------------------------------------------------------
    # LISA
    # --------------------------------------------------------

    f.write(
        "[LISA 유형별 지역 수]\n"
    )

    f.write(
        lisa_counts.to_string()
    )

    f.write(
        "\n\n"
    )

    f.write(
        f"High-High: "
        f"{len(hh_df)}개\n"
    )

    f.write(
        f"Low-Low: "
        f"{len(ll_df)}개\n"
    )

    f.write(
        f"High-Low: "
        f"{len(hl_df)}개\n"
    )

    f.write(
        f"Low-High: "
        f"{len(lh_df)}개\n\n"
    )

    # --------------------------------------------------------
    # HH 상세
    # --------------------------------------------------------

    f.write(
        "[유의한 High-High 지역]\n"
    )

    if len(hh_df) > 0:

        f.write(
            hh_df
            .round(4)
            .to_string(
                index=False
            )
        )

    else:

        f.write(
            "없음"
        )

    f.write(
        "\n"
    )


# ============================================================
# 24. 분석 완료
# ============================================================

print("\n========================================")
print("공간 통계 분석 완료")
print("========================================")

print(
    f"결과 저장 위치:\n"
    f"{OUTPUT_DIR}"
)

print(
    "\n생성 파일:"
)

for path in sorted(
    OUTPUT_DIR.iterdir()
):

    print(
        "-",
        path.name,
    )