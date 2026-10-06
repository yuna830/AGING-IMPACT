from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import PowerTransformer
from sklearn.preprocessing import StandardScaler


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "results"
    / "final_feature_selection"
    / "final_feature_candidates.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "kmeans_preparation"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 그래프 설정
# ============================================================

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 데이터 불러오기
# ============================================================

print("\n========================================")
print("1. K-Means 후보 데이터 불러오기")
print("========================================")

df = pd.read_csv(
    INPUT_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

print(
    f"지역 수: {len(df):,}"
)

print(
    f"컬럼 수: {len(df.columns):,}"
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
    # 고령화
    "고령화율_2025",
    "고령화율변화폭_2016_2025",

    # 인구구조 / 이동
    "청년비율변화폭_2016_2025",
    "청년순이동률_2016_2025",

    # 경제
    "인구천명당_종사자수_2024",
    "사업체당_종사자수_2024",

    # 생활 인프라
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]


missing_cols = [
    col
    for col in feature_cols
    if col not in df.columns
]

if missing_cols:
    raise ValueError(
        "필요한 컬럼이 없습니다: "
        + ", ".join(missing_cols)
    )


# ============================================================
# 결측치 확인
# ============================================================

print("\n========================================")
print("2. 결측치 확인")
print("========================================")

missing = (
    df[feature_cols]
    .isna()
    .sum()
)

print(
    missing
)

if missing.sum() != 0:
    raise ValueError(
        "K-Means 입력 데이터에 결측치가 있습니다."
    )


# ============================================================
# 원본 왜도 계산
# ============================================================

print("\n========================================")
print("3. 원본 변수 왜도")
print("========================================")

original_skew = (
    df[feature_cols]
    .skew()
)

skew_df = pd.DataFrame(
    {
        "변수": feature_cols,
        "변환전_왜도": [
            original_skew[col]
            for col in feature_cols
        ],
    }
)

skew_df[
    "변환전_절대왜도"
] = (
    skew_df[
        "변환전_왜도"
    ].abs()
)

print(
    skew_df
    .sort_values(
        "변환전_절대왜도",
        ascending=False,
    )
    .to_string(
        index=False,
    )
)


# ============================================================
# Yeo-Johnson 변환 대상 선정
# ============================================================

"""
절대 왜도 >= 1.0인 변수는
분포가 상당히 비대칭이라고 보고
Yeo-Johnson 변환 적용.

Yeo-Johnson은 음수 값도 처리할 수 있으므로
청년순이동률처럼 음수가 존재하는 변수에도 사용 가능.
"""

SKEW_THRESHOLD = 1.0

transform_cols = [
    col
    for col in feature_cols
    if abs(original_skew[col]) >= SKEW_THRESHOLD
]


print("\n========================================")
print("4. Yeo-Johnson 변환 대상")
print("========================================")

for col in transform_cols:
    print(
        f"- {col} "
        f"(왜도: {original_skew[col]:.3f})"
    )


# ============================================================
# 변환용 데이터 복사
# ============================================================

transformed_df = df.copy()


# ============================================================
# Yeo-Johnson 변환
# ============================================================

power_transformer = PowerTransformer(
    method="yeo-johnson",
    standardize=False,
)

transformed_values = (
    power_transformer
    .fit_transform(
        transformed_df[
            transform_cols
        ]
    )
)

transformed_df[
    transform_cols
] = transformed_values


# ============================================================
# 변환 후 왜도
# ============================================================

print("\n========================================")
print("5. 변환 후 왜도")
print("========================================")

after_skew = (
    transformed_df[
        feature_cols
    ]
    .skew()
)

skew_df[
    "변환후_왜도"
] = [
    after_skew[col]
    for col in feature_cols
]

skew_df[
    "변환후_절대왜도"
] = (
    skew_df[
        "변환후_왜도"
    ].abs()
)

skew_df[
    "변환여부"
] = skew_df[
    "변수"
].apply(
    lambda x: (
        "Yeo-Johnson"
        if x in transform_cols
        else "원본 유지"
    )
)

skew_df = skew_df.sort_values(
    "변환전_절대왜도",
    ascending=False,
)

print(
    skew_df.to_string(
        index=False,
    )
)

skew_df.to_csv(
    OUTPUT_DIR
    / "skewness_before_after.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# Yeo-Johnson lambda 값 저장
# ============================================================

lambda_df = pd.DataFrame(
    {
        "변수": transform_cols,
        "YeoJohnson_lambda":
            power_transformer.lambdas_,
    }
)

lambda_df.to_csv(
    OUTPUT_DIR
    / "yeojohnson_lambdas.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# StandardScaler
# ============================================================

print("\n========================================")
print("6. StandardScaler 적용")
print("========================================")

scaler = StandardScaler()

scaled_values = (
    scaler.fit_transform(
        transformed_df[
            feature_cols
        ]
    )
)

scaled_df = pd.DataFrame(
    scaled_values,
    columns=feature_cols,
)

scaled_df = pd.concat(
    [
        df[id_cols]
        .reset_index(
            drop=True,
        ),

        scaled_df,
    ],
    axis=1,
)


print(
    "\n표준화 후 평균:"
)

print(
    scaled_df[
        feature_cols
    ]
    .mean()
    .round(6)
)

print(
    "\n표준화 후 표준편차:"
)

print(
    scaled_df[
        feature_cols
    ]
    .std(
        ddof=0,
    )
    .round(6)
)


scaled_df.to_csv(
    OUTPUT_DIR
    / "kmeans_scaled_features.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# K-Means 입력 배열
# ============================================================

X = scaled_df[
    feature_cols
].to_numpy()


# ============================================================
# K = 2 ~ 8 평가
# ============================================================

print("\n========================================")
print("7. 군집 수 K 탐색")
print("========================================")

results = []

for k in range(
    2,
    9,
):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20,
    )

    labels = model.fit_predict(
        X
    )

    inertia = model.inertia_

    silhouette = silhouette_score(
        X,
        labels,
    )

    cluster_counts = (
        pd.Series(labels)
        .value_counts()
        .sort_index()
        .to_dict()
    )

    min_cluster_size = min(
        cluster_counts.values()
    )

    max_cluster_size = max(
        cluster_counts.values()
    )

    results.append(
        {
            "K": k,
            "Inertia": inertia,
            "SilhouetteScore": silhouette,
            "최소군집크기": min_cluster_size,
            "최대군집크기": max_cluster_size,
            "군집크기": str(
                cluster_counts
            ),
        }
    )

    print(
        f"K={k} | "
        f"Inertia={inertia:.3f} | "
        f"Silhouette={silhouette:.4f} | "
        f"Cluster sizes={cluster_counts}"
    )


k_results = pd.DataFrame(
    results
)

k_results.to_csv(
    OUTPUT_DIR
    / "k_selection_results.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# Silhouette 최고 K
# ============================================================

best_row = (
    k_results
    .sort_values(
        "SilhouetteScore",
        ascending=False,
    )
    .iloc[0]
)

best_k = int(
    best_row["K"]
)

best_score = float(
    best_row[
        "SilhouetteScore"
    ]
)


print("\n========================================")
print("8. Silhouette 기준 최고 K")
print("========================================")

print(
    f"K = {best_k}"
)

print(
    f"Silhouette Score = "
    f"{best_score:.4f}"
)


# ============================================================
# Elbow 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 6),
)

ax.plot(
    k_results["K"],
    k_results["Inertia"],
    marker="o",
)

ax.set_xlabel(
    "군집 수 K"
)

ax.set_ylabel(
    "Inertia"
)

ax.set_title(
    "K-Means Elbow Method"
)

ax.set_xticks(
    k_results["K"]
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "01_elbow_method.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# Silhouette 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 6),
)

ax.plot(
    k_results["K"],
    k_results[
        "SilhouetteScore"
    ],
    marker="o",
)

ax.set_xlabel(
    "군집 수 K"
)

ax.set_ylabel(
    "Silhouette Score"
)

ax.set_title(
    "K-Means Silhouette Score"
)

ax.set_xticks(
    k_results["K"]
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "02_silhouette_score.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 스케일러 정보 저장
# ============================================================

scaler_df = pd.DataFrame(
    {
        "변수": feature_cols,
        "평균": scaler.mean_,
        "표준편차": scaler.scale_,
    }
)

scaler_df.to_csv(
    OUTPUT_DIR
    / "standard_scaler_parameters.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 변환 전/후 비교 데이터 저장
# ============================================================

comparison_df = df[
    id_cols
].copy()

for col in feature_cols:

    comparison_df[
        f"{col}_원본"
    ] = df[col]

    comparison_df[
        f"{col}_변환"
    ] = transformed_df[col]

    comparison_df[
        f"{col}_표준화"
    ] = scaled_df[col]


comparison_df.to_csv(
    OUTPUT_DIR
    / "feature_transformation_comparison.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 요약 파일
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "kmeans_preparation_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - K-Means 전처리 및 K 탐색\n"
    )

    f.write(
        "=" * 60
        + "\n\n"
    )

    f.write(
        f"분석 지역 수: {len(df)}\n"
    )

    f.write(
        f"입력 변수 수: {len(feature_cols)}\n"
    )

    f.write(
        f"왜도 변환 기준: |skew| >= "
        f"{SKEW_THRESHOLD}\n\n"
    )

    f.write(
        "[Yeo-Johnson 변환 변수]\n"
    )

    for col in transform_cols:
        f.write(
            f"- {col}\n"
        )

    f.write(
        "\n[왜도 변환 전/후]\n"
    )

    f.write(
        skew_df.to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[K 탐색 결과]\n"
    )

    f.write(
        k_results.to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[Silhouette 기준 최고 K]\n"
    )

    f.write(
        f"K = {best_k}\n"
    )

    f.write(
        f"Silhouette Score = "
        f"{best_score:.4f}\n"
    )

    f.write(
        "\n주의:\n"
    )

    f.write(
        "Silhouette Score가 가장 높은 K를 "
        "자동으로 최종 군집 수로 확정하지 않음.\n"
    )

    f.write(
        "Elbow 결과, 군집 크기, "
        "지역 특성의 해석 가능성을 함께 고려하여 "
        "최종 K를 결정.\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("K-Means 전처리 및 K 탐색 완료")
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