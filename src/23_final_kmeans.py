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
    / "final_kmeans"
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
print("1. 최종 K-Means 데이터 불러오기")
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
# 변수 정의
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
print("2. 지역 순서 검증")
print("========================================")

if (
    scaled_df["지역코드"].tolist()
    != original_df["지역코드"].tolist()
):
    raise ValueError(
        "표준화 데이터와 원본 데이터의 지역 순서가 다릅니다."
    )

print("지역 순서 일치 확인 완료")


# ============================================================
# 최종 K 설정
# ============================================================

FINAL_K = 3

X = scaled_df[
    feature_cols
].to_numpy()


# ============================================================
# K-Means 실행
# ============================================================

print("\n========================================")
print("3. 최종 K-Means 실행")
print("========================================")

model = KMeans(
    n_clusters=FINAL_K,
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

# 보기 편하게 cluster 번호를 1부터 시작
cluster_labels = (
    labels
    + 1
)

print(
    f"최종 K: {FINAL_K}"
)

print(
    f"Silhouette Score: "
    f"{silhouette:.4f}"
)


# ============================================================
# 군집 결과 부여
# ============================================================

scaled_result = (
    scaled_df.copy()
)

original_result = (
    original_df.copy()
)

scaled_result[
    "cluster"
] = cluster_labels

original_result[
    "cluster"
] = cluster_labels


# ============================================================
# 군집별 크기
# ============================================================

print("\n========================================")
print("4. 군집별 지역 수")
print("========================================")

cluster_counts = (
    original_result[
        "cluster"
    ]
    .value_counts()
    .sort_index()
)

print(
    cluster_counts.to_string()
)


# ============================================================
# 군집별 원본 평균
# ============================================================

print("\n========================================")
print("5. 군집별 원본 지표 평균")
print("========================================")

original_profile = (
    original_result
    .groupby(
        "cluster"
    )[feature_cols]
    .mean()
    .round(3)
)

print(
    original_profile.to_string()
)

original_profile.to_csv(
    OUTPUT_DIR
    / "final_cluster_profile_original.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 군집별 표준화 평균
# ============================================================

print("\n========================================")
print("6. 군집별 표준화 지표 평균")
print("========================================")

scaled_profile = (
    scaled_result
    .groupby(
        "cluster"
    )[feature_cols]
    .mean()
    .round(3)
)

print(
    scaled_profile.to_string()
)

scaled_profile.to_csv(
    OUTPUT_DIR
    / "final_cluster_profile_scaled.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 임시 군집 이름 지정
# ============================================================

"""
현재 평균 특성을 바탕으로 한 임시 이름.

최종 보고서에서는
미스매치 분석 결과까지 확인한 뒤
표현을 조금 더 다듬을 수 있음.
"""

cluster_name_map = {
    1: "일반도시_중간형",
    2: "고령화_청년유출형",
    3: "경제활동_청년유입형",
}

original_result[
    "cluster_name"
] = (
    original_result[
        "cluster"
    ]
    .map(
        cluster_name_map
    )
)


# ============================================================
# 군집 설명 생성
# ============================================================

cluster_description_map = {
    1: (
        "고령화 수준이 비교적 낮고, "
        "청년 이동과 경제활동이 중간 수준인 지역"
    ),
    2: (
        "고령화 수준과 고령화 진행 속도가 높고, "
        "청년 순유출이 크게 나타나는 지역"
    ),
    3: (
        "고령화 수준이 낮고, "
        "청년 순유입과 경제활동 수준이 높은 지역"
    ),
}

original_result[
    "cluster_description"
] = (
    original_result[
        "cluster"
    ]
    .map(
        cluster_description_map
    )
)


# ============================================================
# 최종 지역별 군집 결과
# ============================================================

final_cluster_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "cluster_description",
] + feature_cols

final_cluster_result = (
    original_result[
        final_cluster_cols
    ]
    .sort_values(
        [
            "cluster",
            "시도",
            "지역명",
        ]
    )
)

final_cluster_result.to_csv(
    OUTPUT_DIR
    / "final_cluster_assignments.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# B 담당 전달용 간단 CSV
# ============================================================

b_share_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
]

b_share_df = (
    final_cluster_result[
        b_share_cols
    ]
    .copy()
)

b_share_df.to_csv(
    OUTPUT_DIR
    / "cluster_for_visualization.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 군집별 지역 목록
# ============================================================

region_list_rows = []

for cluster_id in range(
    1,
    FINAL_K + 1,
):

    temp = (
        final_cluster_result[
            final_cluster_result[
                "cluster"
            ]
            == cluster_id
        ][
            [
                "지역코드",
                "시도",
                "지역명",
                "cluster",
                "cluster_name",
            ]
        ]
    )

    print("\n")
    print(
        f"[Cluster {cluster_id}] "
        f"{cluster_name_map[cluster_id]}"
    )

    print(
        f"지역 수: {len(temp)}"
    )

    print(
        temp
        .head(30)
        .to_string(
            index=False,
        )
    )

    region_list_rows.append(
        temp
    )

region_list_df = pd.concat(
    region_list_rows,
    ignore_index=True,
)

region_list_df.to_csv(
    OUTPUT_DIR
    / "final_cluster_region_list.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# PCA 시각화
# ============================================================

print("\n========================================")
print("7. PCA 시각화")
print("========================================")

pca = PCA(
    n_components=2,
)

pca_values = (
    pca.fit_transform(
        X
    )
)

pca_df = pd.DataFrame(
    {
        "지역코드":
            scaled_df["지역코드"],
        "시도":
            scaled_df["시도"],
        "지역명":
            scaled_df["지역명"],
        "PC1":
            pca_values[:, 0],
        "PC2":
            pca_values[:, 1],
        "cluster":
            cluster_labels,
    }
)

pca_df[
    "cluster_name"
] = (
    pca_df[
        "cluster"
    ]
    .map(
        cluster_name_map
    )
)

pca_df.to_csv(
    OUTPUT_DIR
    / "final_pca_coordinates.csv",
    index=False,
    encoding="utf-8-sig",
)


explained_variance = (
    pca.explained_variance_ratio_
)

print(
    f"PC1 설명력: "
    f"{explained_variance[0] * 100:.2f}%"
)

print(
    f"PC2 설명력: "
    f"{explained_variance[1] * 100:.2f}%"
)

print(
    f"누적 설명력: "
    f"{explained_variance.sum() * 100:.2f}%"
)


fig, ax = plt.subplots(
    figsize=(9, 7),
)

for cluster_id in range(
    1,
    FINAL_K + 1,
):

    temp = pca_df[
        pca_df[
            "cluster"
        ]
        == cluster_id
    ]

    ax.scatter(
        temp["PC1"],
        temp["PC2"],
        label=(
            f"{cluster_name_map[cluster_id]} "
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
    "지역 유형 K-Means 군집 결과 (K=3)"
)

ax.legend()

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "final_kmeans_pca.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 군집 프로파일 그래프
# ============================================================

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
            cluster_name_map[
                cluster_id
            ]
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
    "군집별 주요 특성 프로파일"
)

ax.tick_params(
    axis="x",
    rotation=90,
)

ax.legend()

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "final_cluster_profile.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 군집 요약 테이블
# ============================================================

summary_rows = []

for cluster_id in range(
    1,
    FINAL_K + 1,
):

    row = {
        "cluster":
            cluster_id,
        "cluster_name":
            cluster_name_map[
                cluster_id
            ],
        "지역수":
            int(
                cluster_counts.loc[
                    cluster_id
                ]
            ),
    }

    for col in feature_cols:
        row[col] = (
            original_profile
            .loc[
                cluster_id,
                col,
            ]
        )

    summary_rows.append(
        row
    )


cluster_summary_df = pd.DataFrame(
    summary_rows
)

cluster_summary_df.to_csv(
    OUTPUT_DIR
    / "final_cluster_summary.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 요약 TXT
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "final_kmeans_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - 최종 K-Means 결과\n"
    )

    f.write(
        "=" * 60
        + "\n\n"
    )

    f.write(
        f"최종 K: {FINAL_K}\n"
    )

    f.write(
        f"Silhouette Score: "
        f"{silhouette:.4f}\n\n"
    )

    f.write(
        "[군집별 지역 수]\n"
    )

    f.write(
        cluster_counts.to_string()
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[군집 이름]\n"
    )

    for cluster_id, name in (
        cluster_name_map.items()
    ):
        f.write(
            f"Cluster {cluster_id}: "
            f"{name}\n"
        )

    f.write(
        "\n[군집별 원본 평균]\n"
    )

    f.write(
        original_profile.to_string()
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[군집별 표준화 평균]\n"
    )

    f.write(
        scaled_profile.to_string()
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[PCA 설명력]\n"
    )

    f.write(
        f"PC1: "
        f"{explained_variance[0] * 100:.2f}%\n"
    )

    f.write(
        f"PC2: "
        f"{explained_variance[1] * 100:.2f}%\n"
    )

    f.write(
        f"누적: "
        f"{explained_variance.sum() * 100:.2f}%\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("최종 K-Means 완료")
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