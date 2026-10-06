from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SCALED_PATH = (
    BASE_DIR
    / "results"
    / "kmeans_preparation"
    / "kmeans_scaled_features.csv"
)

ORIGINAL_PATH = (
    BASE_DIR
    / "results"
    / "final_feature_selection"
    / "final_feature_candidates.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "kmeans_comparison"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 한글 폰트 설정
# ============================================================

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 데이터 불러오기
# ============================================================

print("\n========================================")
print("1. 데이터 불러오기")
print("========================================")

scaled_df = pd.read_csv(
    SCALED_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

original_df = pd.read_csv(
    ORIGINAL_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

scaled_df["지역코드"] = (
    scaled_df["지역코드"]
    .astype(str)
    .str.zfill(5)
)

original_df["지역코드"] = (
    original_df["지역코드"]
    .astype(str)
    .str.zfill(5)
)


print(
    f"표준화 데이터 지역 수: {len(scaled_df)}"
)

print(
    f"원본 데이터 지역 수: {len(original_df)}"
)


# ============================================================
# 분석 변수
# ============================================================

id_cols = [
    "지역코드",
    "시도",
    "지역명",
]

feature_cols = [
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년비율변화폭_2016_2025",
    "청년순이동률_2016_2025",
    "인구천명당_종사자수_2024",
    "사업체당_종사자수_2024",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]


# ============================================================
# 데이터 정렬 검증
# ============================================================

print("\n========================================")
print("2. 지역 정렬 검증")
print("========================================")

scaled_codes = scaled_df[
    "지역코드"
].tolist()

original_codes = original_df[
    "지역코드"
].tolist()

if scaled_codes != original_codes:
    raise ValueError(
        "표준화 데이터와 원본 데이터의 "
        "지역 순서가 일치하지 않습니다."
    )

print(
    "지역 순서 일치 확인 완료"
)


# ============================================================
# K-Means 입력값
# ============================================================

X = scaled_df[
    feature_cols
].to_numpy()


# ============================================================
# 비교할 K
# ============================================================

K_VALUES = [
    2,
    3,
    4,
]


# ============================================================
# PCA 준비
# ============================================================

pca = PCA(
    n_components=2,
)

pca_values = pca.fit_transform(
    X
)

pca_df = pd.DataFrame(
    {
        "지역코드": scaled_df["지역코드"],
        "시도": scaled_df["시도"],
        "지역명": scaled_df["지역명"],
        "PC1": pca_values[:, 0],
        "PC2": pca_values[:, 1],
    }
)

explained_variance = (
    pca.explained_variance_ratio_
)

print("\n========================================")
print("3. PCA 설명 분산")
print("========================================")

print(
    f"PC1: "
    f"{explained_variance[0] * 100:.2f}%"
)

print(
    f"PC2: "
    f"{explained_variance[1] * 100:.2f}%"
)

print(
    f"PC1 + PC2: "
    f"{explained_variance.sum() * 100:.2f}%"
)


# ============================================================
# K별 분석
# ============================================================

comparison_rows = []


for k in K_VALUES:

    print("\n")
    print("=" * 60)
    print(
        f"K = {k} 분석"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # K-Means
    # --------------------------------------------------------

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20,
    )

    labels = model.fit_predict(
        X
    )

    silhouette = silhouette_score(
        X,
        labels,
    )

    # --------------------------------------------------------
    # 군집 번호는 보기 좋게 1부터 시작
    # --------------------------------------------------------

    cluster_labels = (
        labels
        + 1
    )

    # --------------------------------------------------------
    # 표준화 데이터 결과
    # --------------------------------------------------------

    scaled_result = (
        scaled_df.copy()
    )

    scaled_result[
        "cluster"
    ] = cluster_labels

    # --------------------------------------------------------
    # 원본 데이터 결과
    # --------------------------------------------------------

    original_result = (
        original_df.copy()
    )

    original_result[
        "cluster"
    ] = cluster_labels

    # --------------------------------------------------------
    # 군집 크기
    # --------------------------------------------------------

    cluster_counts = (
        original_result[
            "cluster"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        f"\nSilhouette Score: "
        f"{silhouette:.4f}"
    )

    print(
        "\n군집별 지역 수:"
    )

    print(
        cluster_counts.to_string()
    )

    # --------------------------------------------------------
    # 비교 요약
    # --------------------------------------------------------

    comparison_rows.append(
        {
            "K": k,
            "SilhouetteScore": silhouette,
            "최소군집크기": int(
                cluster_counts.min()
            ),
            "최대군집크기": int(
                cluster_counts.max()
            ),
            "군집크기": str(
                cluster_counts.to_dict()
            ),
        }
    )

    # --------------------------------------------------------
    # 원본 값 기준 군집 평균
    # --------------------------------------------------------

    original_profile = (
        original_result
        .groupby(
            "cluster"
        )[feature_cols]
        .mean()
        .round(3)
    )

    print(
        "\n[원본 지표 기준 군집 평균]"
    )

    print(
        original_profile.to_string()
    )

    original_profile.to_csv(
        OUTPUT_DIR
        / f"k{k}_original_cluster_profile.csv",
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # 표준화 값 기준 군집 평균
    # --------------------------------------------------------

    scaled_profile = (
        scaled_result
        .groupby(
            "cluster"
        )[feature_cols]
        .mean()
        .round(3)
    )

    print(
        "\n[표준화 지표 기준 군집 평균]"
    )

    print(
        scaled_profile.to_string()
    )

    scaled_profile.to_csv(
        OUTPUT_DIR
        / f"k{k}_scaled_cluster_profile.csv",
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # 전체 지역 군집 결과 저장
    # --------------------------------------------------------

    cluster_result = (
        original_result[
            id_cols
            + ["cluster"]
            + feature_cols
        ]
        .sort_values(
            [
                "cluster",
                "시도",
                "지역명",
            ]
        )
    )

    cluster_result.to_csv(
        OUTPUT_DIR
        / f"k{k}_cluster_assignments.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # 군집별 지역 목록
    # --------------------------------------------------------

    region_list_rows = []

    for cluster_id in range(
        1,
        k + 1,
    ):

        cluster_regions = (
            cluster_result[
                cluster_result[
                    "cluster"
                ]
                == cluster_id
            ][
                [
                    "지역코드",
                    "시도",
                    "지역명",
                ]
            ]
        )

        print(
            f"\n[Cluster {cluster_id}]"
        )

        print(
            f"지역 수: "
            f"{len(cluster_regions)}"
        )

        print(
            cluster_regions
            .head(30)
            .to_string(
                index=False,
            )
        )

        for _, row in (
            cluster_regions.iterrows()
        ):

            region_list_rows.append(
                {
                    "cluster": cluster_id,
                    "지역코드":
                        row["지역코드"],
                    "시도":
                        row["시도"],
                    "지역명":
                        row["지역명"],
                }
            )

    region_list_df = pd.DataFrame(
        region_list_rows
    )

    region_list_df.to_csv(
        OUTPUT_DIR
        / f"k{k}_region_list.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # PCA 결과에 군집 추가
    # --------------------------------------------------------

    pca_result = (
        pca_df.copy()
    )

    pca_result[
        "cluster"
    ] = cluster_labels

    pca_result.to_csv(
        OUTPUT_DIR
        / f"k{k}_pca_coordinates.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # PCA 산점도
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(9, 7),
    )

    for cluster_id in range(
        1,
        k + 1,
    ):

        temp = pca_result[
            pca_result[
                "cluster"
            ]
            == cluster_id
        ]

        ax.scatter(
            temp["PC1"],
            temp["PC2"],
            label=(
                f"Cluster {cluster_id} "
                f"(n={len(temp)})"
            ),
            alpha=0.7,
        )

    ax.set_xlabel(
        f"PC1 "
        f"({explained_variance[0] * 100:.1f}%)"
    )

    ax.set_ylabel(
        f"PC2 "
        f"({explained_variance[1] * 100:.1f}%)"
    )

    ax.set_title(
        f"K-Means 군집 PCA 시각화 "
        f"(K={k})"
    )

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR
        / f"k{k}_pca_scatter.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    # --------------------------------------------------------
    # 군집 프로파일 그래프
    # --------------------------------------------------------

    profile_for_plot = (
        scaled_profile.T
    )

    fig, ax = plt.subplots(
        figsize=(12, 7),
    )

    for cluster_id in profile_for_plot.columns:

        ax.plot(
            profile_for_plot.index,
            profile_for_plot[
                cluster_id
            ],
            marker="o",
            label=(
                f"Cluster {cluster_id}"
            ),
        )

    ax.axhline(
        0,
        linewidth=1,
    )

    ax.set_ylabel(
        "표준화 평균값"
    )

    ax.set_title(
        f"군집별 특성 프로파일 "
        f"(K={k})"
    )

    ax.tick_params(
        axis="x",
        rotation=90,
    )

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR
        / f"k{k}_cluster_profile.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)


# ============================================================
# K 비교 결과 저장
# ============================================================

comparison_df = pd.DataFrame(
    comparison_rows
)

comparison_df.to_csv(
    OUTPUT_DIR
    / "k_comparison_summary.csv",
    index=False,
    encoding="utf-8-sig",
)


print("\n========================================")
print("4. K 비교 요약")
print("========================================")

print(
    comparison_df.to_string(
        index=False,
    )
)


# ============================================================
# PCA 로딩값
# ============================================================

loading_df = pd.DataFrame(
    pca.components_.T,
    index=feature_cols,
    columns=[
        "PC1_loading",
        "PC2_loading",
    ],
)

loading_df.to_csv(
    OUTPUT_DIR
    / "pca_loadings.csv",
    encoding="utf-8-sig",
)

print("\n========================================")
print("5. PCA 주요 변수")
print("========================================")

print(
    loading_df
    .round(3)
    .to_string()
)


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("K=2 / 3 / 4 비교 완료")
print("========================================")

print(
    f"결과 저장 위치:\n"
    f"{OUTPUT_DIR}"
)

print("\n생성 파일:")

for path in sorted(
    OUTPUT_DIR.iterdir()
):
    print(
        "-",
        path.name,
    )