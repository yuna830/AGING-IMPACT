from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ============================================================
# 기본 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "results"
    / "ab_merge"
    / "ab_dataset.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "ab_eda"
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
print("1. A+B 통합 데이터 불러오기")
print("========================================")

df = pd.read_csv(
    INPUT_PATH,
    encoding="utf-8-sig",
)

print(f"지역 수: {len(df):,}")
print(f"컬럼 수: {len(df.columns):,}")


# ============================================================
# 분석 변수 정의
# ============================================================

analysis_cols = [
    # 인구 / 고령화
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년비율_2025",
    "청년비율변화폭_2016_2025",
    "인구증감률_2016_2025",
    "청년순이동률_2016_2025",

    # 경제
    "인구천명당_사업체수_2024",
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
    for col in analysis_cols
    if col not in df.columns
]

if missing_cols:
    raise ValueError(
        "분석에 필요한 컬럼이 없습니다: "
        + ", ".join(missing_cols)
    )

print("\n분석 변수:")
for col in analysis_cols:
    print("-", col)


# ============================================================
# 결측치 확인
# ============================================================

print("\n========================================")
print("2. 분석 변수 결측치 확인")
print("========================================")

missing_summary = (
    df[analysis_cols]
    .isna()
    .sum()
    .sort_values(
        ascending=False,
    )
)

print(missing_summary)

missing_summary.to_csv(
    OUTPUT_DIR / "missing_summary.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 기술통계
# ============================================================

print("\n========================================")
print("3. 기술통계")
print("========================================")

summary = (
    df[analysis_cols]
    .describe()
    .T
)

print(summary)

summary.to_csv(
    OUTPUT_DIR / "descriptive_statistics.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 상관행렬
# ============================================================

print("\n========================================")
print("4. 상관관계 분석")
print("========================================")

corr = (
    df[analysis_cols]
    .corr(
        method="pearson",
    )
)

corr.to_csv(
    OUTPUT_DIR / "correlation_matrix.csv",
    encoding="utf-8-sig",
)

print(
    corr.round(3)
)


# ============================================================
# 상관계수 쌍 정리
# ============================================================

pairs = []

for i in range(len(analysis_cols)):
    for j in range(i + 1, len(analysis_cols)):
        col1 = analysis_cols[i]
        col2 = analysis_cols[j]

        value = corr.loc[
            col1,
            col2,
        ]

        pairs.append(
            {
                "변수1": col1,
                "변수2": col2,
                "상관계수": value,
                "절대상관계수": abs(value),
            }
        )

pair_df = pd.DataFrame(pairs)

pair_df = pair_df.sort_values(
    "절대상관계수",
    ascending=False,
)

pair_df.to_csv(
    OUTPUT_DIR / "correlation_pairs.csv",
    index=False,
    encoding="utf-8-sig",
)

print("\n상관계수 절대값 상위 20개:")
print(
    pair_df
    .head(20)
    .to_string(
        index=False,
    )
)


# ============================================================
# 상관행렬 히트맵
# ============================================================

fig, ax = plt.subplots(
    figsize=(15, 13),
)

im = ax.imshow(
    corr.values,
    aspect="auto",
)

ax.set_xticks(
    np.arange(
        len(analysis_cols)
    )
)

ax.set_yticks(
    np.arange(
        len(analysis_cols)
    )
)

ax.set_xticklabels(
    analysis_cols,
    rotation=90,
)

ax.set_yticklabels(
    analysis_cols,
)

for i in range(
    len(analysis_cols)
):
    for j in range(
        len(analysis_cols)
    ):
        value = corr.iloc[i, j]

        ax.text(
            j,
            i,
            f"{value:.2f}",
            ha="center",
            va="center",
            fontsize=7,
        )

ax.set_title(
    "A+B 전체 변수 상관행렬"
)

fig.colorbar(
    im,
    ax=ax,
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "01_correlation_heatmap.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 주요 산점도 생성 함수
# ============================================================

def save_scatter(
    x_col,
    y_col,
    filename,
    title,
):
    temp = df[
        [
            x_col,
            y_col,
            "시도",
            "지역명",
        ]
    ].dropna()

    fig, ax = plt.subplots(
        figsize=(8, 6),
    )

    ax.scatter(
        temp[x_col],
        temp[y_col],
        alpha=0.7,
    )

    ax.set_xlabel(
        x_col
    )

    ax.set_ylabel(
        y_col
    )

    corr_value = (
        temp[
            [
                x_col,
                y_col,
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    ax.set_title(
        f"{title}\n"
        f"Pearson r = {corr_value:.3f}"
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR
        / filename,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)


# ============================================================
# 고령화 ↔ 생활 인프라
# ============================================================

save_scatter(
    "고령화율_2025",
    "노인천명당_병원수",
    "02_aging_vs_hospital.png",
    "고령화율과 병원 공급 수준",
)

save_scatter(
    "고령화율_2025",
    "노인천명당_약국수",
    "03_aging_vs_pharmacy.png",
    "고령화율과 약국 공급 수준",
)

save_scatter(
    "고령화율_2025",
    "노인천명당_복지시설수",
    "04_aging_vs_welfare.png",
    "고령화율과 노인복지시설 공급 수준",
)

save_scatter(
    "고령화율_2025",
    "노인천명당_버스정류장수",
    "05_aging_vs_bus.png",
    "고령화율과 버스정류장 공급 수준",
)

save_scatter(
    "고령화율_2025",
    "노인천명당_철도역수",
    "06_aging_vs_subway.png",
    "고령화율과 도시철도역 공급 수준",
)


# ============================================================
# 고령화 변화 ↔ 생활 인프라
# ============================================================

save_scatter(
    "고령화율변화폭_2016_2025",
    "노인천명당_병원수",
    "07_aging_change_vs_hospital.png",
    "고령화 속도와 병원 공급 수준",
)

save_scatter(
    "고령화율변화폭_2016_2025",
    "노인천명당_복지시설수",
    "08_aging_change_vs_welfare.png",
    "고령화 속도와 노인복지시설 공급 수준",
)

save_scatter(
    "고령화율변화폭_2016_2025",
    "노인천명당_버스정류장수",
    "09_aging_change_vs_bus.png",
    "고령화 속도와 버스정류장 공급 수준",
)


# ============================================================
# 인구 변화 ↔ 생활 인프라
# ============================================================

save_scatter(
    "청년순이동률_2016_2025",
    "노인천명당_병원수",
    "10_youth_migration_vs_hospital.png",
    "청년순이동률과 병원 공급 수준",
)

save_scatter(
    "청년순이동률_2016_2025",
    "노인천명당_복지시설수",
    "11_youth_migration_vs_welfare.png",
    "청년순이동률과 노인복지시설 공급 수준",
)

save_scatter(
    "청년순이동률_2016_2025",
    "노인천명당_버스정류장수",
    "12_youth_migration_vs_bus.png",
    "청년순이동률과 버스정류장 공급 수준",
)

save_scatter(
    "인구증감률_2016_2025",
    "노인천명당_병원수",
    "13_population_change_vs_hospital.png",
    "인구증감률과 병원 공급 수준",
)

save_scatter(
    "인구증감률_2016_2025",
    "노인천명당_복지시설수",
    "14_population_change_vs_welfare.png",
    "인구증감률과 노인복지시설 공급 수준",
)


# ============================================================
# 생활 인프라 변수별 상위 / 하위 지역
# ============================================================

print("\n========================================")
print("5. 생활 인프라 상위 / 하위 지역")
print("========================================")

infra_cols = [
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

ranking_rows = []

for col in infra_cols:

    temp = df[
        [
            "지역코드",
            "시도",
            "지역명",
            col,
        ]
    ].dropna()

    top = (
        temp
        .nlargest(
            10,
            col,
        )
        .copy()
    )

    top["구분"] = "상위"

    bottom = (
        temp
        .nsmallest(
            10,
            col,
        )
        .copy()
    )

    bottom["구분"] = "하위"

    combined = pd.concat(
        [
            top,
            bottom,
        ],
        ignore_index=True,
    )

    combined["지표"] = col

    combined = combined.rename(
        columns={
            col: "값",
        }
    )

    ranking_rows.append(
        combined
    )

ranking_df = pd.concat(
    ranking_rows,
    ignore_index=True,
)

ranking_df.to_csv(
    OUTPUT_DIR
    / "infrastructure_rankings.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    ranking_df.head(30)
    .to_string(
        index=False,
    )
)


# ============================================================
# 고령화 수준 + 인프라 부족 후보 지역
# ============================================================

print("\n========================================")
print("6. 고령화·인프라 미스매치 사전 후보")
print("========================================")

aging_median = (
    df["고령화율_2025"]
    .median()
)

infra_medians = {
    col: df[col].median()
    for col in infra_cols
}

candidate = df.copy()

candidate[
    "고령화_상위"
] = (
    candidate[
        "고령화율_2025"
    ]
    >= aging_median
)

for col in infra_cols:
    candidate[
        f"{col}_부족"
    ] = (
        candidate[col]
        < infra_medians[col]
    )

infra_shortage_cols = [
    f"{col}_부족"
    for col in infra_cols
]

candidate[
    "인프라부족개수"
] = (
    candidate[
        infra_shortage_cols
    ]
    .sum(
        axis=1,
    )
)

pre_mismatch = candidate[
    candidate[
        "고령화_상위"
    ]
].copy()

pre_mismatch = (
    pre_mismatch
    .sort_values(
        [
            "인프라부족개수",
            "고령화율_2025",
        ],
        ascending=[
            False,
            False,
        ],
    )
)

pre_mismatch_cols = [
    "지역코드",
    "시도",
    "지역명",
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년순이동률_2016_2025",
    "인구증감률_2016_2025",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
    "인프라부족개수",
]

pre_mismatch[
    pre_mismatch_cols
].to_csv(
    OUTPUT_DIR
    / "preliminary_mismatch_candidates.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    pre_mismatch[
        pre_mismatch_cols
    ]
    .head(20)
    .to_string(
        index=False,
    )
)


# ============================================================
# 요약 파일 생성
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "eda_ab_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - A+B 통합 EDA 요약\n"
    )

    f.write(
        "=" * 50
        + "\n\n"
    )

    f.write(
        f"분석 지역 수: {len(df)}\n"
    )

    f.write(
        f"분석 변수 수: {len(analysis_cols)}\n\n"
    )

    f.write(
        "[결측치]\n"
    )

    f.write(
        missing_summary.to_string()
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[상관계수 절대값 상위 20개]\n"
    )

    f.write(
        pair_df
        .head(20)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[고령화·인프라 미스매치 사전 후보 상위 20개]\n"
    )

    f.write(
        pre_mismatch[
            pre_mismatch_cols
        ]
        .head(20)
        .to_string(
            index=False,
        )
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("A+B 통합 EDA 완료")
print("========================================")

print(
    f"결과 저장 위치:\n{OUTPUT_DIR}"
)

print("\n생성 파일:")

for path in sorted(
    OUTPUT_DIR.iterdir()
):
    print(
        "-",
        path.name,
    )