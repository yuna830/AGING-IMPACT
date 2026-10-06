from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

AB_PATH = (
    BASE_DIR
    / "results"
    / "ab_merge"
    / "ab_dataset.csv"
)

CLUSTER_PATH = (
    BASE_DIR
    / "results"
    / "final_kmeans"
    / "cluster_for_visualization.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
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

df = pd.read_csv(
    AB_PATH,
    encoding="utf-8-sig",
    dtype={
        "지역코드": str,
    },
)

cluster_df = pd.read_csv(
    CLUSTER_PATH,
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

cluster_df["지역코드"] = (
    cluster_df["지역코드"]
    .astype(str)
    .str.zfill(5)
)

print(
    f"A+B 데이터 지역 수: {len(df)}"
)

print(
    f"군집 데이터 지역 수: {len(cluster_df)}"
)


# ============================================================
# 군집 정보 결합
# ============================================================

df = df.merge(
    cluster_df[
        [
            "지역코드",
            "cluster",
            "cluster_name",
        ]
    ],
    on="지역코드",
    how="left",
    validate="one_to_one",
)

if df["cluster"].isna().any():
    raise ValueError(
        "군집이 매칭되지 않은 지역이 존재합니다."
    )

print(
    "군집 정보 결합 완료"
)


# ============================================================
# 분석 변수
# ============================================================

aging_cols = [
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
]

infra_cols = [
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

context_cols = [
    "청년순이동률_2016_2025",
    "인구증감률_2016_2025",
    "인구천명당_종사자수_2024",
]


# ============================================================
# 강원 고성군 버스 결측 처리
# ============================================================

print("\n========================================")
print("2. 강원 고성군 버스 결측 처리")
print("========================================")

df[
    "버스지표_보완여부"
] = False

goseong_mask = (
    (df["시도"] == "강원")
    & (df["지역명"] == "고성군")
)

gangwon_bus_median = (
    df.loc[
        (df["시도"] == "강원")
        & (~goseong_mask),
        "노인천명당_버스정류장수",
    ]
    .dropna()
    .median()
)

print(
    "강원 지역 버스정류장 지표 중앙값:",
    round(
        gangwon_bus_median,
        3,
    ),
)

df.loc[
    goseong_mask,
    "노인천명당_버스정류장수",
] = gangwon_bus_median

df.loc[
    goseong_mask,
    "버스지표_보완여부",
] = True

print(
    df.loc[
        goseong_mask,
        [
            "지역코드",
            "시도",
            "지역명",
            "노인천명당_버스정류장수",
            "버스지표_보완여부",
        ],
    ].to_string(
        index=False,
    )
)


# ============================================================
# 결측치 검증
# ============================================================

print("\n========================================")
print("3. 분석 변수 결측치 확인")
print("========================================")

required_cols = (
    aging_cols
    + infra_cols
)

missing = (
    df[required_cols]
    .isna()
    .sum()
)

print(
    missing
)

if missing.sum() != 0:
    raise ValueError(
        "미스매치 계산용 변수에 결측치가 남아 있습니다."
    )


# ============================================================
# 백분위 점수 생성
# ============================================================

print("\n========================================")
print("4. 고령화 수요 점수 생성")
print("========================================")

# 값이 높을수록 수요가 높은 것으로 해석
df[
    "고령화율_백분위"
] = (
    df["고령화율_2025"]
    .rank(
        pct=True,
        method="average",
    )
)

df[
    "고령화변화폭_백분위"
] = (
    df[
        "고령화율변화폭_2016_2025"
    ]
    .rank(
        pct=True,
        method="average",
    )
)

df[
    "고령화수요점수"
] = (
    df[
        [
            "고령화율_백분위",
            "고령화변화폭_백분위",
        ]
    ]
    .mean(
        axis=1,
    )
)

print(
    df[
        [
            "지역코드",
            "시도",
            "지역명",
            "고령화율_2025",
            "고령화율변화폭_2016_2025",
            "고령화수요점수",
        ]
    ]
    .sort_values(
        "고령화수요점수",
        ascending=False,
    )
    .head(10)
    .to_string(
        index=False,
    )
)


# ============================================================
# 인프라 백분위
# ============================================================

print("\n========================================")
print("5. 생활 인프라 공급 점수 생성")
print("========================================")

infra_percentile_cols = []

for col in infra_cols:

    percentile_col = (
        f"{col}_백분위"
    )

    df[
        percentile_col
    ] = (
        df[col]
        .rank(
            pct=True,
            method="average",
        )
    )

    infra_percentile_cols.append(
        percentile_col
    )


df[
    "인프라공급점수"
] = (
    df[
        infra_percentile_cols
    ]
    .mean(
        axis=1,
    )
)


print(
    df[
        [
            "지역코드",
            "시도",
            "지역명",
            "인프라공급점수",
        ]
    ]
    .sort_values(
        "인프라공급점수",
        ascending=False,
    )
    .head(10)
    .to_string(
        index=False,
    )
)


# ============================================================
# 전체 미스매치 점수
# ============================================================

print("\n========================================")
print("6. 전체 미스매치 점수 계산")
print("========================================")

df[
    "미스매치점수"
] = (
    df["고령화수요점수"]
    - df["인프라공급점수"]
)


# 보기 편하게 0~100 형태 추가
df[
    "고령화수요점수_100"
] = (
    df["고령화수요점수"]
    * 100
)

df[
    "인프라공급점수_100"
] = (
    df["인프라공급점수"]
    * 100
)

df[
    "미스매치점수_100"
] = (
    df["미스매치점수"]
    * 100
)


# ============================================================
# 인프라 분야별 미스매치
# ============================================================

print("\n========================================")
print("7. 분야별 미스매치 점수")
print("========================================")

sector_map = {
    "병원": "노인천명당_병원수_백분위",
    "약국": "노인천명당_약국수_백분위",
    "복지": "노인천명당_복지시설수_백분위",
    "버스": "노인천명당_버스정류장수_백분위",
    "철도": "노인천명당_철도역수_백분위",
}

sector_gap_cols = []

for sector, percentile_col in (
    sector_map.items()
):

    gap_col = (
        f"{sector}_미스매치점수"
    )

    df[
        gap_col
    ] = (
        df["고령화수요점수"]
        - df[percentile_col]
    )

    sector_gap_cols.append(
        gap_col
    )


# ============================================================
# 미스매치 순위
# ============================================================

df[
    "미스매치순위"
] = (
    df["미스매치점수"]
    .rank(
        ascending=False,
        method="min",
    )
    .astype(int)
)


# ============================================================
# 우선 검토 지역 구분
# ============================================================

"""
상위 25% 고령화 수요이면서
전체 인프라 공급이 하위 50%인 지역을
우선 검토 지역으로 정의.

이는 절대적인 '취약지역' 판정이 아니라
본 분석 내 상대적 우선 검토 후보임.
"""

aging_threshold = (
    df["고령화수요점수"]
    .quantile(
        0.75
    )
)

infra_threshold = (
    df["인프라공급점수"]
    .quantile(
        0.50
    )
)

df[
    "우선검토지역"
] = (
    (
        df[
            "고령화수요점수"
        ]
        >= aging_threshold
    )
    & (
        df[
            "인프라공급점수"
        ]
        <= infra_threshold
    )
)


print(
    "고령화 수요 상위 25% 기준:",
    round(
        aging_threshold,
        3,
    ),
)

print(
    "인프라 공급 하위 50% 기준:",
    round(
        infra_threshold,
        3,
    ),
)

print(
    "우선 검토 지역 수:",
    int(
        df[
            "우선검토지역"
        ].sum()
    ),
)


# ============================================================
# 최종 순위 출력
# ============================================================

print("\n========================================")
print("8. 전체 미스매치 상위 20개 지역")
print("========================================")

ranking_cols = [
    "미스매치순위",
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년순이동률_2016_2025",
    "고령화수요점수_100",
    "인프라공급점수_100",
    "미스매치점수_100",
    "우선검토지역",
]

ranking_df = (
    df[
        ranking_cols
    ]
    .sort_values(
        "미스매치순위"
    )
)

print(
    ranking_df
    .head(20)
    .round(3)
    .to_string(
        index=False,
    )
)


# ============================================================
# 우선 검토 지역
# ============================================================

print("\n========================================")
print("9. 우선 검토 지역")
print("========================================")

priority_df = (
    df[
        df[
            "우선검토지역"
        ]
    ]
    .copy()
    .sort_values(
        "미스매치점수",
        ascending=False,
    )
)

priority_cols = [
    "지역코드",
    "시도",
    "지역명",
    "cluster",
    "cluster_name",
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년순이동률_2016_2025",
    "인구증감률_2016_2025",
    "고령화수요점수_100",
    "인프라공급점수_100",
    "미스매치점수_100",
    "병원_미스매치점수",
    "약국_미스매치점수",
    "복지_미스매치점수",
    "버스_미스매치점수",
    "철도_미스매치점수",
]

print(
    priority_df[
        priority_cols
    ]
    .head(30)
    .round(3)
    .to_string(
        index=False,
    )
)


# ============================================================
# 군집별 미스매치 특성
# ============================================================

print("\n========================================")
print("10. 군집별 미스매치 평균")
print("========================================")

cluster_mismatch = (
    df
    .groupby(
        [
            "cluster",
            "cluster_name",
        ]
    )[
        [
            "고령화수요점수_100",
            "인프라공급점수_100",
            "미스매치점수_100",
        ]
        + sector_gap_cols
    ]
    .mean()
    .round(3)
)

print(
    cluster_mismatch.to_string()
)

cluster_mismatch.to_csv(
    OUTPUT_DIR
    / "cluster_mismatch_summary.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 분야별 미스매치 상위 지역 저장
# ============================================================

sector_ranking_rows = []

for sector in sector_map:

    gap_col = (
        f"{sector}_미스매치점수"
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
                gap_col,
            ]
        ]
        .sort_values(
            gap_col,
            ascending=False,
        )
        .head(20)
        .copy()
    )

    temp[
        "인프라분야"
    ] = sector

    temp = temp.rename(
        columns={
            gap_col:
                "분야별미스매치점수"
        }
    )

    sector_ranking_rows.append(
        temp
    )


sector_ranking_df = pd.concat(
    sector_ranking_rows,
    ignore_index=True,
)

sector_ranking_df.to_csv(
    OUTPUT_DIR
    / "sector_mismatch_top20.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 전체 결과 저장
# ============================================================

final_cols = [
    "지역코드",
    "시도",
    "지역명",

    "cluster",
    "cluster_name",

    "고령화율_2025",
    "고령화율변화폭_2016_2025",

    "청년순이동률_2016_2025",
    "인구증감률_2016_2025",
    "인구천명당_종사자수_2024",

    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",

    "고령화수요점수_100",
    "인프라공급점수_100",
    "미스매치점수_100",
    "미스매치순위",

    "병원_미스매치점수",
    "약국_미스매치점수",
    "복지_미스매치점수",
    "버스_미스매치점수",
    "철도_미스매치점수",

    "우선검토지역",
    "버스지표_보완여부",
]

final_result = (
    df[
        final_cols
    ]
    .sort_values(
        "미스매치순위"
    )
)

final_result.to_csv(
    OUTPUT_DIR
    / "final_mismatch_analysis.csv",
    index=False,
    encoding="utf-8-sig",
)


priority_df[
    priority_cols
].to_csv(
    OUTPUT_DIR
    / "priority_mismatch_regions.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# B 담당 시각화용 파일
# ============================================================

visualization_cols = [
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

df[
    visualization_cols
].to_csv(
    OUTPUT_DIR
    / "mismatch_for_visualization.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 산점도
# ============================================================

fig, ax = plt.subplots(
    figsize=(9, 7),
)

ax.scatter(
    df["인프라공급점수_100"],
    df["고령화수요점수_100"],
    alpha=0.7,
)

ax.axvline(
    infra_threshold * 100,
    linestyle="--",
    linewidth=1,
)

ax.axhline(
    aging_threshold * 100,
    linestyle="--",
    linewidth=1,
)

ax.set_xlabel(
    "생활 인프라 공급 점수"
)

ax.set_ylabel(
    "고령화 수요 점수"
)

ax.set_title(
    "고령화 수요와 생활 인프라 공급 수준"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "01_aging_demand_vs_infrastructure.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 미스매치 상위 20개 그래프
# ============================================================

top20 = (
    df
    .sort_values(
        "미스매치점수_100",
        ascending=False,
    )
    .head(20)
    .copy()
)

top20[
    "지역표시"
] = (
    top20["시도"]
    + " "
    + top20["지역명"]
)


fig, ax = plt.subplots(
    figsize=(10, 8),
)

ax.barh(
    top20[
        "지역표시"
    ][::-1],
    top20[
        "미스매치점수_100"
    ][::-1],
)

ax.set_xlabel(
    "미스매치 점수"
)

ax.set_title(
    "생활 인프라 미스매치 상위 20개 지역"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR
    / "02_mismatch_top20.png",
    dpi=200,
    bbox_inches="tight",
)

plt.close(fig)


# ============================================================
# 요약 파일
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "mismatch_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - 생활 인프라 미스매치 분석\n"
    )

    f.write(
        "=" * 60
        + "\n\n"
    )

    f.write(
        "미스매치 산식\n"
    )

    f.write(
        "고령화 수요 점수 = "
        "고령화율 백분위와 "
        "고령화율 변화폭 백분위 평균\n"
    )

    f.write(
        "인프라 공급 점수 = "
        "병원·약국·복지·버스·철도 "
        "백분위 평균\n"
    )

    f.write(
        "미스매치 점수 = "
        "고령화 수요 점수 - "
        "인프라 공급 점수\n\n"
    )

    f.write(
        f"분석 지역 수: {len(df)}\n"
    )

    f.write(
        f"우선 검토 지역 수: "
        f"{len(priority_df)}\n\n"
    )

    f.write(
        "[미스매치 상위 20개]\n"
    )

    f.write(
        ranking_df
        .head(20)
        .round(3)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[군집별 미스매치 평균]\n"
    )

    f.write(
        cluster_mismatch.to_string()
    )

    f.write(
        "\n\n주의\n"
    )

    f.write(
        "본 미스매치 점수는 분석 대상 229개 지역 내 "
        "상대적 수준을 비교하기 위한 지표이며, "
        "절대적인 지역 취약성 판정 기준이 아님.\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("생활 인프라 미스매치 분석 완료")
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