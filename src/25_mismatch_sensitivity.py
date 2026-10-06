from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
    / "final_mismatch_analysis.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "mismatch_sensitivity"
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
print("1. 미스매치 분석 데이터 불러오기")
print("========================================")

df = pd.read_csv(
    INPUT_PATH,
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
    f"컬럼 수: {len(df.columns)}"
)


# ============================================================
# 필요한 컬럼 확인
# ============================================================

required_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",

    "고령화수요점수_100",

    "병원_미스매치점수",
    "약국_미스매치점수",
    "복지_미스매치점수",
    "버스_미스매치점수",
    "철도_미스매치점수",
]

missing_cols = [
    col
    for col in required_cols
    if col not in df.columns
]

if missing_cols:
    raise ValueError(
        "필요한 컬럼이 없습니다: "
        + ", ".join(missing_cols)
    )


# ============================================================
# 인프라 백분위 복원
# ============================================================

"""
분야별 미스매치 점수:

분야별 미스매치
= 고령화수요점수
- 해당 인프라 백분위

이므로,

인프라 백분위
= 고령화수요점수
- 분야별 미스매치

로 복원 가능.
"""

print("\n========================================")
print("2. 인프라 백분위 복원")
print("========================================")

df[
    "고령화수요점수"
] = (
    df[
        "고령화수요점수_100"
    ]
    / 100
)

sector_gap_map = {
    "병원": "병원_미스매치점수",
    "약국": "약국_미스매치점수",
    "복지": "복지_미스매치점수",
    "버스": "버스_미스매치점수",
    "철도": "철도_미스매치점수",
}


for sector, gap_col in sector_gap_map.items():

    percentile_col = (
        f"{sector}_인프라백분위"
    )

    df[
        percentile_col
    ] = (
        df[
            "고령화수요점수"
        ]
        - df[
            gap_col
        ]
    )


infra_percentile_cols = [
    "병원_인프라백분위",
    "약국_인프라백분위",
    "복지_인프라백분위",
    "버스_인프라백분위",
    "철도_인프라백분위",
]


print(
    df[
        infra_percentile_cols
    ]
    .describe()
    .round(3)
)


# ============================================================
# 가중치 시나리오 정의
# ============================================================

SCENARIOS = {

    "균등가중치": {
        "병원": 0.20,
        "약국": 0.20,
        "복지": 0.20,
        "버스": 0.20,
        "철도": 0.20,
    },

    "의료강조": {
        "병원": 0.30,
        "약국": 0.30,
        "복지": 0.20,
        "버스": 0.10,
        "철도": 0.10,
    },

    "교통강조": {
        "병원": 0.15,
        "약국": 0.15,
        "복지": 0.20,
        "버스": 0.25,
        "철도": 0.25,
    },

    "철도영향축소": {
        "병원": 0.25,
        "약국": 0.25,
        "복지": 0.25,
        "버스": 0.20,
        "철도": 0.05,
    },
}


# ============================================================
# 가중치 검증
# ============================================================

print("\n========================================")
print("3. 가중치 검증")
print("========================================")

for scenario_name, weights in SCENARIOS.items():

    weight_sum = sum(
        weights.values()
    )

    if abs(
        weight_sum
        - 1.0
    ) > 1e-9:

        raise ValueError(
            f"{scenario_name}의 "
            f"가중치 합이 1이 아닙니다: "
            f"{weight_sum}"
        )

    print(
        f"{scenario_name}: "
        f"{weight_sum:.2f}"
    )


# ============================================================
# 시나리오별 미스매치 계산
# ============================================================

print("\n========================================")
print("4. 시나리오별 미스매치 계산")
print("========================================")

scenario_score_cols = {}

for scenario_name, weights in SCENARIOS.items():

    infra_score_col = (
        f"{scenario_name}_인프라공급점수"
    )

    mismatch_col = (
        f"{scenario_name}_미스매치점수"
    )

    rank_col = (
        f"{scenario_name}_순위"
    )

    weighted_infra = (
        df[
            "병원_인프라백분위"
        ]
        * weights["병원"]
        +
        df[
            "약국_인프라백분위"
        ]
        * weights["약국"]
        +
        df[
            "복지_인프라백분위"
        ]
        * weights["복지"]
        +
        df[
            "버스_인프라백분위"
        ]
        * weights["버스"]
        +
        df[
            "철도_인프라백분위"
        ]
        * weights["철도"]
    )

    df[
        infra_score_col
    ] = weighted_infra

    df[
        mismatch_col
    ] = (
        df[
            "고령화수요점수"
        ]
        - df[
            infra_score_col
        ]
    )

    df[
        rank_col
    ] = (
        df[
            mismatch_col
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    scenario_score_cols[
        scenario_name
    ] = {
        "infra": infra_score_col,
        "mismatch": mismatch_col,
        "rank": rank_col,
    }

    print(
        f"{scenario_name} 계산 완료"
    )


# ============================================================
# 기본안과 기존 미스매치 값 검증
# ============================================================

print("\n========================================")
print("5. 기본안 일치 검증")
print("========================================")

if "미스매치점수_100" in df.columns:

    df[
        "기존미스매치점수"
    ] = (
        df[
            "미스매치점수_100"
        ]
        / 100
    )

    difference = (
        df[
            "균등가중치_미스매치점수"
        ]
        - df[
            "기존미스매치점수"
        ]
    ).abs()

    print(
        "기존 분석과 균등가중치 "
        "최대 차이:",
        difference.max(),
    )

    if difference.max() > 1e-6:
        print(
            "주의: 기존 미스매치 결과와 "
            "균등가중치 결과에 차이가 있습니다."
        )
    else:
        print(
            "기존 미스매치 결과와 "
            "균등가중치 결과 일치"
        )


# ============================================================
# 순위 상관계수 계산
# ============================================================

print("\n========================================")
print("6. 기본안 대비 순위 상관계수")
print("========================================")

base_rank_col = (
    scenario_score_cols[
        "균등가중치"
    ][
        "rank"
    ]
)

rank_corr_rows = []

for scenario_name in SCENARIOS:

    rank_col = (
        scenario_score_cols[
            scenario_name
        ][
            "rank"
        ]
    )

    spearman_corr = (
        df[
            [
                base_rank_col,
                rank_col,
            ]
        ]
        .corr(
            method="spearman",
        )
        .iloc[
            0,
            1,
        ]
    )

    rank_corr_rows.append(
        {
            "시나리오":
                scenario_name,
            "균등가중치대비_순위상관":
                spearman_corr,
        }
    )


rank_corr_df = pd.DataFrame(
    rank_corr_rows
)

print(
    rank_corr_df
    .round(4)
    .to_string(
        index=False,
    )
)

rank_corr_df.to_csv(
    OUTPUT_DIR
    / "scenario_rank_correlations.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 시나리오별 상위 20개 추출
# ============================================================

print("\n========================================")
print("7. 시나리오별 상위 20개 지역")
print("========================================")

top20_rows = []

for scenario_name in SCENARIOS:

    mismatch_col = (
        scenario_score_cols[
            scenario_name
        ][
            "mismatch"
        ]
    )

    rank_col = (
        scenario_score_cols[
            scenario_name
        ][
            "rank"
        ]
    )

    temp = (
        df[
            [
                "지역코드",
                "시도",
                "지역명",
                "cluster",
                "cluster_name",
                "고령화수요점수",
                mismatch_col,
                rank_col,
            ]
        ]
        .sort_values(
            rank_col
        )
        .head(20)
        .copy()
    )

    temp[
        "시나리오"
    ] = scenario_name

    temp = temp.rename(
        columns={
            mismatch_col:
                "미스매치점수",
            rank_col:
                "순위",
        }
    )

    top20_rows.append(
        temp
    )

    print(
        f"\n[{scenario_name}]"
    )

    print(
        temp[
            [
                "순위",
                "시도",
                "지역명",
                "미스매치점수",
            ]
        ]
        .round(3)
        .to_string(
            index=False,
        )
    )


top20_df = pd.concat(
    top20_rows,
    ignore_index=True,
)

top20_df.to_csv(
    OUTPUT_DIR
    / "scenario_top20_regions.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 상위 20개 반복 등장 횟수 계산
# ============================================================

print("\n========================================")
print("8. 상위 20개 반복 등장 지역")
print("========================================")

appearance_count = (
    top20_df
    .groupby(
        [
            "지역코드",
            "시도",
            "지역명",
            "cluster",
            "cluster_name",
        ]
    )
    .size()
    .reset_index(
        name="상위20_등장횟수"
    )
)

appearance_count = (
    appearance_count
    .sort_values(
        [
            "상위20_등장횟수",
            "지역코드",
        ],
        ascending=[
            False,
            True,
        ],
    )
)


# 각 시나리오 순위 추가
for scenario_name in SCENARIOS:

    rank_col = (
        scenario_score_cols[
            scenario_name
        ][
            "rank"
        ]
    )

    rank_map = (
        df.set_index(
            "지역코드"
        )[
            rank_col
        ]
    )

    appearance_count[
        f"{scenario_name}_순위"
    ] = (
        appearance_count[
            "지역코드"
        ]
        .map(
            rank_map
        )
    )


appearance_count[
    "평균순위"
] = (
    appearance_count[
        [
            f"{name}_순위"
            for name in SCENARIOS
        ]
    ]
    .mean(
        axis=1
    )
)

appearance_count = (
    appearance_count
    .sort_values(
        [
            "상위20_등장횟수",
            "평균순위",
        ],
        ascending=[
            False,
            True,
        ],
    )
)


print(
    appearance_count
    .head(30)
    .round(2)
    .to_string(
        index=False,
    )
)

appearance_count.to_csv(
    OUTPUT_DIR
    / "top20_stability.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 안정적 핵심 미스매치 지역
# ============================================================

"""
4개 시나리오 모두에서
상위 20위 안에 등장한 지역을
안정적 핵심 미스매치 지역으로 정의.
"""

stable_regions = (
    appearance_count[
        appearance_count[
            "상위20_등장횟수"
        ]
        == len(
            SCENARIOS
        )
    ]
    .copy()
)

print("\n========================================")
print("9. 안정적 핵심 미스매치 지역")
print("========================================")

print(
    f"4개 시나리오 모두 상위 20위 "
    f"지역 수: {len(stable_regions)}"
)

print(
    stable_regions
    .round(2)
    .to_string(
        index=False,
    )
)

stable_regions.to_csv(
    OUTPUT_DIR
    / "stable_mismatch_regions.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 각 시나리오 Top20 중복률
# ============================================================

print("\n========================================")
print("10. 균등가중치 Top20 중복률")
print("========================================")

base_top20 = set(
    top20_df.loc[
        top20_df[
            "시나리오"
        ]
        == "균등가중치",
        "지역코드",
    ]
)

overlap_rows = []

for scenario_name in SCENARIOS:

    scenario_top20 = set(
        top20_df.loc[
            top20_df[
                "시나리오"
            ]
            == scenario_name,
            "지역코드",
        ]
    )

    overlap_count = len(
        base_top20
        & scenario_top20
    )

    overlap_rate = (
        overlap_count
        / 20
        * 100
    )

    overlap_rows.append(
        {
            "시나리오":
                scenario_name,
            "균등가중치Top20_중복지역수":
                overlap_count,
            "중복률":
                overlap_rate,
        }
    )


overlap_df = pd.DataFrame(
    overlap_rows
)

print(
    overlap_df
    .round(2)
    .to_string(
        index=False,
    )
)

overlap_df.to_csv(
    OUTPUT_DIR
    / "top20_overlap.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 전체 시나리오 결과 저장
# ============================================================

output_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "고령화수요점수",
]


for scenario_name in SCENARIOS:

    output_cols.extend(
        [
            scenario_score_cols[
                scenario_name
            ][
                "infra"
            ],
            scenario_score_cols[
                scenario_name
            ][
                "mismatch"
            ],
            scenario_score_cols[
                scenario_name
            ][
                "rank"
            ],
        ]
    )


df[
    output_cols
].to_csv(
    OUTPUT_DIR
    / "sensitivity_all_regions.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 반복 등장 횟수 그래프
# ============================================================

plot_df = (
    appearance_count
    .head(20)
    .copy()
)

plot_df[
    "지역표시"
] = (
    plot_df["시도"]
    + " "
    + plot_df["지역명"]
)


fig, ax = plt.subplots(
    figsize=(10, 8),
)

ax.barh(
    plot_df[
        "지역표시"
    ][::-1],
    plot_df[
        "상위20_등장횟수"
    ][::-1],
)

ax.set_xlabel(
    "4개 시나리오 중 Top20 등장 횟수"
)

ax.set_title(
    "가중치 변화에 따른 미스매치 상위지역 안정성"
)

ax.set_xlim(
    0,
    len(
        SCENARIOS
    )
    + 0.5,
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "01_top20_stability.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 순위 상관계수 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 6),
)

ax.bar(
    rank_corr_df[
        "시나리오"
    ],
    rank_corr_df[
        "균등가중치대비_순위상관"
    ],
)

ax.set_ylim(
    0,
    1.05,
)

ax.set_ylabel(
    "Spearman 순위 상관계수"
)

ax.set_title(
    "가중치 시나리오별 순위 안정성"
)

ax.tick_params(
    axis="x",
    rotation=20,
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "02_rank_correlation.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 요약 파일
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "sensitivity_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - 미스매치 민감도 분석\n"
    )

    f.write(
        "=" * 60
        + "\n\n"
    )

    f.write(
        "[가중치 시나리오]\n"
    )

    for scenario_name, weights in (
        SCENARIOS.items()
    ):

        f.write(
            f"\n{scenario_name}\n"
        )

        for sector, weight in (
            weights.items()
        ):

            f.write(
                f"- {sector}: "
                f"{weight:.2f}\n"
            )

    f.write(
        "\n\n"
    )

    f.write(
        "[균등가중치 대비 순위 상관]\n"
    )

    f.write(
        rank_corr_df
        .round(4)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[Top20 중복률]\n"
    )

    f.write(
        overlap_df
        .round(2)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    f.write(
        "[4개 시나리오 모두 Top20 지역]\n"
    )

    f.write(
        stable_regions
        .round(2)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n해석 기준\n"
    )

    f.write(
        "가중치를 변경해도 "
        "순위 상관계수가 높고 "
        "동일 지역이 반복적으로 "
        "상위권에 포함될수록 "
        "미스매치 결과가 특정 가중치 설정에 "
        "덜 의존한다고 해석할 수 있음.\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("미스매치 민감도 분석 완료")
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