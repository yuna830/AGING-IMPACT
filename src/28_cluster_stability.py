from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


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

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "cluster_stability"
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
# 분석 설정
# ============================================================

K_VALUES = [
    2,
    3,
    4,
]

# 반복 실행할 seed
RANDOM_SEEDS = list(
    range(
        0,
        100,
    )
)

# 기존 최종 군집과 동일한 기준 모델
REFERENCE_SEED = 42

# 기존 분석과 동일하게 설정
N_INIT = 20


# ============================================================
# 분석 변수
# ============================================================

ID_COLS = [
    "지역코드",
    "시도",
    "지역명",
]

FEATURE_COLS = [
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
# 1. 입력 파일 확인
# ============================================================

print("\n========================================")
print("1. 입력 파일 확인")
print("========================================")

if not SCALED_PATH.exists():
    raise FileNotFoundError(
        f"파일이 없습니다:\n{SCALED_PATH}"
    )

print(
    "[OK]",
    SCALED_PATH.relative_to(
        BASE_DIR
    ),
)


# ============================================================
# 2. 데이터 불러오기
# ============================================================

print("\n========================================")
print("2. 데이터 불러오기")
print("========================================")

df = pd.read_csv(
    SCALED_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

df["지역코드"] = (
    df["지역코드"]
    .astype(str)
    .str.zfill(5)
)

print(
    f"지역 수: {len(df)}"
)

print(
    f"분석 변수 수: {len(FEATURE_COLS)}"
)


# ============================================================
# 3. 컬럼 검증
# ============================================================

print("\n========================================")
print("3. 컬럼 및 결측치 검증")
print("========================================")

missing_cols = [
    col
    for col in FEATURE_COLS
    if col not in df.columns
]

if missing_cols:
    raise ValueError(
        "필요한 컬럼이 없습니다:\n"
        + "\n".join(
            missing_cols
        )
    )

missing_values = (
    df[
        FEATURE_COLS
    ]
    .isna()
    .sum()
)

if (
    missing_values.sum()
    > 0
):

    print(
        missing_values[
            missing_values
            > 0
        ]
    )

    raise ValueError(
        "군집 안정성 분석 입력 데이터에 "
        "결측치가 있습니다."
    )

print(
    "분석 변수 및 결측치 검증 완료"
)


# ============================================================
# 4. K-Means 입력 배열
# ============================================================

X = (
    df[
        FEATURE_COLS
    ]
    .to_numpy()
)


# ============================================================
# 5. 기준 군집 생성
# ============================================================

print("\n========================================")
print("4. 기준 군집 생성")
print("========================================")

reference_labels = {}

for k in K_VALUES:

    reference_model = KMeans(
        n_clusters=k,
        random_state=REFERENCE_SEED,
        n_init=N_INIT,
    )

    labels = (
        reference_model
        .fit_predict(
            X
        )
    )

    reference_labels[
        k
    ] = labels

    counts = (
        pd.Series(
            labels
        )
        .value_counts()
        .sort_index()
        .to_dict()
    )

    print(
        f"K={k} | "
        f"기준 seed={REFERENCE_SEED} | "
        f"군집 크기={counts}"
    )


# ============================================================
# 6. 반복 K-Means + 기준 군집 대비 ARI
# ============================================================

print("\n========================================")
print("5. Random seed 반복 검증")
print("========================================")

run_rows = []

all_labels = {
    k: {}
    for k in K_VALUES
}

for k in K_VALUES:

    print(
        f"\n[K={k}]"
    )

    reference = (
        reference_labels[
            k
        ]
    )

    for seed in RANDOM_SEEDS:

        model = KMeans(
            n_clusters=k,
            random_state=seed,
            n_init=N_INIT,
        )

        labels = (
            model
            .fit_predict(
                X
            )
        )

        all_labels[
            k
        ][
            seed
        ] = labels

        ari = adjusted_rand_score(
            reference,
            labels,
        )

        run_rows.append(
            {
                "K":
                    k,

                "random_state":
                    seed,

                "reference_seed":
                    REFERENCE_SEED,

                "ARI_vs_reference":
                    ari,

                "inertia":
                    model.inertia_,
            }
        )


run_df = pd.DataFrame(
    run_rows
)

run_df.to_csv(
    OUTPUT_DIR
    / "stability_runs.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 7. K별 기준 군집 대비 안정성 요약
# ============================================================

print("\n========================================")
print("6. 기준 군집 대비 ARI 요약")
print("========================================")

summary_rows = []

for k in K_VALUES:

    temp = (
        run_df[
            run_df[
                "K"
            ]
            == k
        ]
    )

    row = {
        "K":
            k,

        "실행횟수":
            len(temp),

        "ARI_평균":
            temp[
                "ARI_vs_reference"
            ].mean(),

        "ARI_표준편차":
            temp[
                "ARI_vs_reference"
            ].std(),

        "ARI_최소":
            temp[
                "ARI_vs_reference"
            ].min(),

        "ARI_중앙값":
            temp[
                "ARI_vs_reference"
            ].median(),

        "ARI_최대":
            temp[
                "ARI_vs_reference"
            ].max(),

        "ARI_0.9이상_비율":
            (
                temp[
                    "ARI_vs_reference"
                ]
                >= 0.9
            ).mean(),

        "ARI_1.0_비율":
            (
                np.isclose(
                    temp[
                        "ARI_vs_reference"
                    ],
                    1.0,
                )
            ).mean(),
    }

    summary_rows.append(
        row
    )


summary_df = pd.DataFrame(
    summary_rows
)

print(
    summary_df
    .round(4)
    .to_string(
        index=False
    )
)

summary_df.to_csv(
    OUTPUT_DIR
    / "stability_summary_reference.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 8. 모든 seed 쌍 간 Pairwise ARI
# ============================================================

print("\n========================================")
print("7. Seed 쌍 간 Pairwise ARI 계산")
print("========================================")

pairwise_rows = []

for k in K_VALUES:

    seeds = list(
        all_labels[
            k
        ].keys()
    )

    for i in range(
        len(seeds)
    ):

        for j in range(
            i + 1,
            len(seeds),
        ):

            seed_a = seeds[
                i
            ]

            seed_b = seeds[
                j
            ]

            labels_a = (
                all_labels[
                    k
                ][
                    seed_a
                ]
            )

            labels_b = (
                all_labels[
                    k
                ][
                    seed_b
                ]
            )

            ari = adjusted_rand_score(
                labels_a,
                labels_b,
            )

            pairwise_rows.append(
                {
                    "K":
                        k,

                    "seed_a":
                        seed_a,

                    "seed_b":
                        seed_b,

                    "pairwise_ARI":
                        ari,
                }
            )


pairwise_df = pd.DataFrame(
    pairwise_rows
)

pairwise_df.to_csv(
    OUTPUT_DIR
    / "pairwise_ari.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 9. Pairwise ARI 요약
# ============================================================

print("\n========================================")
print("8. Pairwise ARI 요약")
print("========================================")

pairwise_summary_rows = []

for k in K_VALUES:

    temp = (
        pairwise_df[
            pairwise_df[
                "K"
            ]
            == k
        ]
    )

    pairwise_summary_rows.append(
        {
            "K":
                k,

            "비교쌍수":
                len(temp),

            "Pairwise_ARI_평균":
                temp[
                    "pairwise_ARI"
                ].mean(),

            "Pairwise_ARI_표준편차":
                temp[
                    "pairwise_ARI"
                ].std(),

            "Pairwise_ARI_최소":
                temp[
                    "pairwise_ARI"
                ].min(),

            "Pairwise_ARI_중앙값":
                temp[
                    "pairwise_ARI"
                ].median(),

            "Pairwise_ARI_최대":
                temp[
                    "pairwise_ARI"
                ].max(),

            "ARI_0.9이상_비율":
                (
                    temp[
                        "pairwise_ARI"
                    ]
                    >= 0.9
                ).mean(),
        }
    )


pairwise_summary_df = pd.DataFrame(
    pairwise_summary_rows
)

print(
    pairwise_summary_df
    .round(4)
    .to_string(
        index=False
    )
)

pairwise_summary_df.to_csv(
    OUTPUT_DIR
    / "stability_summary_pairwise.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 10. 군집별 지역 배정 일치율
# ============================================================

print("\n========================================")
print("9. 지역별 군집 안정성 계산")
print("========================================")

region_stability_rows = []

for k in K_VALUES:

    reference = (
        reference_labels[
            k
        ]
    )

    seeds = list(
        all_labels[
            k
        ].keys()
    )

    for region_idx in range(
        len(df)
    ):

        reference_cluster = (
            reference[
                region_idx
            ]
        )

        same_count = 0

        for seed in seeds:

            labels = (
                all_labels[
                    k
                ][
                    seed
                ]
            )

            # 주의:
            # K-Means cluster 번호는 seed마다
            # 서로 뒤바뀔 수 있으므로
            # 단순 label 번호 비교는 신뢰할 수 없음.
            #
            # 따라서 이 값은 참고용으로만 저장.
            if (
                labels[
                    region_idx
                ]
                == reference_cluster
            ):
                same_count += 1

        region_stability_rows.append(
            {
                "K":
                    k,

                "지역코드":
                    df.loc[
                        region_idx,
                        "지역코드",
                    ],

                "시도":
                    df.loc[
                        region_idx,
                        "시도",
                    ],

                "지역명":
                    df.loc[
                        region_idx,
                        "지역명",
                    ],

                "reference_cluster_raw":
                    int(
                        reference_cluster
                    ),

                "raw_label_match_rate":
                    same_count
                    / len(
                        seeds
                    ),
            }
        )


region_stability_df = pd.DataFrame(
    region_stability_rows
)

region_stability_df.to_csv(
    OUTPUT_DIR
    / "region_raw_label_stability.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 11. ARI 분포 그래프
# ============================================================

print("\n========================================")
print("10. ARI 분포 그래프")
print("========================================")

fig, ax = plt.subplots(
    figsize=(9, 6)
)

plot_data = [
    run_df.loc[
        run_df[
            "K"
        ]
        == k,
        "ARI_vs_reference",
    ].to_numpy()
    for k in K_VALUES
]

ax.boxplot(
    plot_data,
    tick_labels=[
        f"K={k}"
        for k in K_VALUES
    ],
)

ax.axhline(
    0.9,
    linestyle="--",
    linewidth=1,
)

ax.set_title(
    "K-Means 군집 안정성 비교"
)

ax.set_xlabel(
    "군집 수 K"
)

ax.set_ylabel(
    "Adjusted Rand Index"
)

ax.set_ylim(
    0,
    1.05,
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "01_ari_stability_boxplot.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 12. 평균 ARI 비교 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 6)
)

ax.bar(
    summary_df[
        "K"
    ].astype(str),
    summary_df[
        "ARI_평균"
    ],
)

ax.set_title(
    "K별 평균 군집 안정성"
)

ax.set_xlabel(
    "군집 수 K"
)

ax.set_ylabel(
    "평균 ARI"
)

ax.set_ylim(
    0,
    1.05,
)

for index, row in (
    summary_df
    .reset_index(
        drop=True
    )
    .iterrows()
):

    ax.text(
        index,
        row[
            "ARI_평균"
        ]
        + 0.02,
        f"{row['ARI_평균']:.3f}",
        ha="center",
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "02_mean_ari_by_k.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 13. Pairwise ARI 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 6)
)

ax.bar(
    pairwise_summary_df[
        "K"
    ].astype(str),
    pairwise_summary_df[
        "Pairwise_ARI_평균"
    ],
)

ax.set_title(
    "K별 Pairwise ARI 평균"
)

ax.set_xlabel(
    "군집 수 K"
)

ax.set_ylabel(
    "Pairwise ARI 평균"
)

ax.set_ylim(
    0,
    1.05,
)

for index, row in (
    pairwise_summary_df
    .reset_index(
        drop=True
    )
    .iterrows()
):

    ax.text(
        index,
        row[
            "Pairwise_ARI_평균"
        ]
        + 0.02,
        (
            f"{row['Pairwise_ARI_평균']:.3f}"
        ),
        ha="center",
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "03_pairwise_ari_by_k.png",
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# 14. 최종 요약 TXT
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "cluster_stability_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - K-Means 군집 안정성 검증\n"
    )

    f.write(
        "=" * 70
        + "\n\n"
    )

    f.write(
        "[분석 설정]\n"
    )

    f.write(
        f"분석 지역 수: "
        f"{len(df)}\n"
    )

    f.write(
        f"분석 변수 수: "
        f"{len(FEATURE_COLS)}\n"
    )

    f.write(
        "비교 K: "
        + ", ".join(
            map(
                str,
                K_VALUES,
            )
        )
        + "\n"
    )

    f.write(
        f"random_state 반복 수: "
        f"{len(RANDOM_SEEDS)}회\n"
    )

    f.write(
        f"기준 seed: "
        f"{REFERENCE_SEED}\n"
    )

    f.write(
        f"K-Means n_init: "
        f"{N_INIT}\n"
    )

    f.write(
        "안정성 지표: "
        "Adjusted Rand Index (ARI)\n\n"
    )

    f.write(
        "[기준 군집 대비 ARI]\n"
    )

    f.write(
        summary_df
        .round(4)
        .to_string(
            index=False
        )
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[Seed 쌍 간 Pairwise ARI]\n"
    )

    f.write(
        pairwise_summary_df
        .round(4)
        .to_string(
            index=False
        )
    )

    f.write(
        "\n\n"
    )

    # K=3 결과 별도 강조
    k3_reference = (
        summary_df[
            summary_df[
                "K"
            ]
            == 3
        ]
        .iloc[0]
    )

    k3_pairwise = (
        pairwise_summary_df[
            pairwise_summary_df[
                "K"
            ]
            == 3
        ]
        .iloc[0]
    )

    f.write(
        "[K=3 핵심 결과]\n"
    )

    f.write(
        f"기준 군집 대비 평균 ARI: "
        f"{k3_reference['ARI_평균']:.4f}\n"
    )

    f.write(
        f"기준 군집 대비 최소 ARI: "
        f"{k3_reference['ARI_최소']:.4f}\n"
    )

    f.write(
        f"ARI >= 0.9 비율: "
        f"{k3_reference['ARI_0.9이상_비율'] * 100:.1f}%\n"
    )

    f.write(
        f"완전 동일 군집(ARI=1) 비율: "
        f"{k3_reference['ARI_1.0_비율'] * 100:.1f}%\n"
    )

    f.write(
        f"Pairwise 평균 ARI: "
        f"{k3_pairwise['Pairwise_ARI_평균']:.4f}\n"
    )

    f.write(
        f"Pairwise 최소 ARI: "
        f"{k3_pairwise['Pairwise_ARI_최소']:.4f}\n"
    )


# ============================================================
# 15. 완료
# ============================================================

print("\n========================================")
print("군집 안정성 검증 완료")
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