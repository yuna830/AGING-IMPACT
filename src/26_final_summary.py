from pathlib import Path

import pandas as pd


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FINAL_CLUSTER_PATH = (
    BASE_DIR
    / "results"
    / "final_kmeans"
    / "final_cluster_assignments.csv"
)

CLUSTER_PROFILE_PATH = (
    BASE_DIR
    / "results"
    / "final_kmeans"
    / "final_cluster_profile_original.csv"
)

MISMATCH_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
    / "final_mismatch_analysis.csv"
)

PRIORITY_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_analysis"
    / "priority_mismatch_regions.csv"
)

STABLE_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_sensitivity"
    / "stable_mismatch_regions.csv"
)

RANK_CORR_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_sensitivity"
    / "scenario_rank_correlations.csv"
)

TOP20_OVERLAP_PATH = (
    BASE_DIR
    / "results"
    / "mismatch_sensitivity"
    / "top20_overlap.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "final_summary"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 데이터 로드 함수
# ============================================================

def read_csv_with_code(path: Path) -> pd.DataFrame:
    """
    지역코드가 있는 CSV 파일을 읽고
    지역코드를 5자리 문자열로 통일한다.
    """

    df = pd.read_csv(
        path,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    if "지역코드" in df.columns:
        df["지역코드"] = (
            df["지역코드"]
            .astype(str)
            .str.zfill(5)
        )

    return df


# ============================================================
# 입력 파일 존재 확인
# ============================================================

print("\n========================================")
print("1. 입력 파일 확인")
print("========================================")

required_files = [
    FINAL_CLUSTER_PATH,
    CLUSTER_PROFILE_PATH,
    MISMATCH_PATH,
    PRIORITY_PATH,
    STABLE_PATH,
    RANK_CORR_PATH,
    TOP20_OVERLAP_PATH,
]

for path in required_files:

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
# 데이터 불러오기
# ============================================================

print("\n========================================")
print("2. 결과 데이터 불러오기")
print("========================================")

cluster_df = read_csv_with_code(
    FINAL_CLUSTER_PATH
)

cluster_profile = pd.read_csv(
    CLUSTER_PROFILE_PATH,
    encoding="utf-8-sig",
)

mismatch_df = read_csv_with_code(
    MISMATCH_PATH
)

priority_df = read_csv_with_code(
    PRIORITY_PATH
)

stable_df = read_csv_with_code(
    STABLE_PATH
)

rank_corr_df = pd.read_csv(
    RANK_CORR_PATH,
    encoding="utf-8-sig",
)

overlap_df = pd.read_csv(
    TOP20_OVERLAP_PATH,
    encoding="utf-8-sig",
)

print(
    f"전체 분석 지역: {len(cluster_df)}"
)

print(
    f"미스매치 분석 지역: {len(mismatch_df)}"
)

print(
    f"우선 검토 지역: {len(priority_df)}"
)

print(
    f"안정적 핵심 지역: {len(stable_df)}"
)


# ============================================================
# 기본 검증
# ============================================================

print("\n========================================")
print("3. 결과 정합성 검증")
print("========================================")

if len(cluster_df) != 229:
    raise ValueError(
        "최종 군집 데이터의 지역 수가 "
        "229개가 아닙니다."
    )

if len(mismatch_df) != 229:
    raise ValueError(
        "미스매치 데이터의 지역 수가 "
        "229개가 아닙니다."
    )

if (
    cluster_df[
        "지역코드"
    ].nunique()
    != 229
):
    raise ValueError(
        "최종 군집 데이터 지역코드가 "
        "고유하지 않습니다."
    )

if (
    mismatch_df[
        "지역코드"
    ].nunique()
    != 229
):
    raise ValueError(
        "미스매치 데이터 지역코드가 "
        "고유하지 않습니다."
    )


cluster_codes = set(
    cluster_df[
        "지역코드"
    ]
)

mismatch_codes = set(
    mismatch_df[
        "지역코드"
    ]
)

if (
    cluster_codes
    != mismatch_codes
):
    raise ValueError(
        "군집분석과 미스매치 분석의 "
        "지역 구성이 다릅니다."
    )

print(
    "229개 지역 정합성 확인 완료"
)


# ============================================================
# 군집별 지역 수
# ============================================================

print("\n========================================")
print("4. 최종 군집 요약")
print("========================================")

cluster_counts = (
    cluster_df
    .groupby(
        [
            "cluster",
            "cluster_name",
        ]
    )
    .size()
    .reset_index(
        name="지역수"
    )
)

print(
    cluster_counts.to_string(
        index=False,
    )
)

cluster_counts.to_csv(
    OUTPUT_DIR
    / "01_cluster_counts.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 군집별 핵심 평균
# ============================================================

cluster_summary_cols = [
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


cluster_summary = (
    cluster_df
    .groupby(
        [
            "cluster",
            "cluster_name",
        ]
    )[
        cluster_summary_cols
    ]
    .mean()
    .round(3)
    .reset_index()
)

cluster_summary.to_csv(
    OUTPUT_DIR
    / "02_cluster_profiles.csv",
    index=False,
    encoding="utf-8-sig",
)

print("\n[군집별 주요 특성]")

print(
    cluster_summary.to_string(
        index=False,
    )
)


# ============================================================
# 미스매치 상위 20개
# ============================================================

print("\n========================================")
print("5. 미스매치 상위 20개")
print("========================================")

top20_cols = [
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
]

top20_df = (
    mismatch_df
    .sort_values(
        "미스매치순위"
    )
    .head(20)[
        top20_cols
    ]
    .copy()
)

top20_df.to_csv(
    OUTPUT_DIR
    / "03_mismatch_top20.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    top20_df
    .round(3)
    .to_string(
        index=False,
    )
)


# ============================================================
# 우선 검토 지역 정리
# ============================================================

print("\n========================================")
print("6. 우선 검토 지역")
print("========================================")

priority_summary_cols = [
    col
    for col in [
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
    if col in priority_df.columns
]

priority_summary = (
    priority_df[
        priority_summary_cols
    ]
    .sort_values(
        "미스매치점수_100",
        ascending=False,
    )
    .copy()
)

priority_summary.to_csv(
    OUTPUT_DIR
    / "04_priority_regions.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    f"우선 검토 지역 수: "
    f"{len(priority_summary)}"
)


# ============================================================
# 안정적 핵심 미스매치 지역
# ============================================================

print("\n========================================")
print("7. 민감도 분석 핵심 지역")
print("========================================")

stable_summary_cols = [
    col
    for col in [
        "지역코드",
        "시도",
        "지역명",
        "cluster",
        "cluster_name",
        "상위20_등장횟수",
        "균등가중치_순위",
        "의료강조_순위",
        "교통강조_순위",
        "철도영향축소_순위",
        "평균순위",
    ]
    if col in stable_df.columns
]

stable_summary = (
    stable_df[
        stable_summary_cols
    ]
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
    .copy()
)

stable_summary.to_csv(
    OUTPUT_DIR
    / "05_stable_mismatch_regions.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    f"4개 시나리오 모두 Top20 지역: "
    f"{len(stable_summary)}"
)

print(
    stable_summary.to_string(
        index=False,
    )
)


# ============================================================
# 민감도 분석 요약
# ============================================================

print("\n========================================")
print("8. 민감도 분석 요약")
print("========================================")

print(
    "\n[순위 상관계수]"
)

print(
    rank_corr_df
    .round(4)
    .to_string(
        index=False,
    )
)

print(
    "\n[Top20 중복률]"
)

print(
    overlap_df
    .round(2)
    .to_string(
        index=False,
    )
)


rank_corr_df.to_csv(
    OUTPUT_DIR
    / "06_sensitivity_rank_correlation.csv",
    index=False,
    encoding="utf-8-sig",
)

overlap_df.to_csv(
    OUTPUT_DIR
    / "07_sensitivity_top20_overlap.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 핵심 지역 여부를 229개 전체 데이터에 부여
# ============================================================

print("\n========================================")
print("9. 최종 통합 결과 생성")
print("========================================")

final_df = (
    mismatch_df.copy()
)

priority_codes = set(
    priority_df[
        "지역코드"
    ]
)

stable_codes = set(
    stable_df[
        "지역코드"
    ]
)

final_df[
    "최종_우선검토지역"
] = (
    final_df[
        "지역코드"
    ]
    .isin(
        priority_codes
    )
)

final_df[
    "민감도_핵심지역"
] = (
    final_df[
        "지역코드"
    ]
    .isin(
        stable_codes
    )
)


# ============================================================
# 안정적 핵심 지역 평균순위 결합
# ============================================================

if (
    "평균순위"
    in stable_df.columns
):

    stable_rank_map = (
        stable_df
        .set_index(
            "지역코드"
        )[
            "평균순위"
        ]
    )

    final_df[
        "민감도_평균순위"
    ] = (
        final_df[
            "지역코드"
        ]
        .map(
            stable_rank_map
        )
    )

else:

    final_df[
        "민감도_평균순위"
    ] = pd.NA


# ============================================================
# 최종 결과 순서
# ============================================================

final_df = (
    final_df
    .sort_values(
        [
            "민감도_핵심지역",
            "미스매치순위",
        ],
        ascending=[
            False,
            True,
        ],
    )
)


final_df.to_csv(
    OUTPUT_DIR
    / "08_final_analysis_dataset.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 핵심 숫자 계산
# ============================================================

total_regions = len(
    final_df
)

priority_count = int(
    final_df[
        "최종_우선검토지역"
    ].sum()
)

stable_count = int(
    final_df[
        "민감도_핵심지역"
    ].sum()
)


# ============================================================
# Cluster 2 집중도 계산
# ============================================================

top20_cluster_counts = (
    top20_df[
        "cluster"
    ]
    .value_counts()
    .sort_index()
)

stable_cluster_counts = (
    stable_summary[
        "cluster"
    ]
    .value_counts()
    .sort_index()
)

top20_cluster2_count = int(
    (
        top20_df[
            "cluster"
        ]
        == 2
    ).sum()
)

stable_cluster2_count = int(
    (
        stable_summary[
            "cluster"
        ]
        == 2
    ).sum()
)


# ============================================================
# 민감도 최소값 계산
# ============================================================

corr_col = (
    "균등가중치대비_순위상관"
)

if corr_col in rank_corr_df.columns:

    non_base_corr = (
        rank_corr_df.loc[
            rank_corr_df[
                "시나리오"
            ]
            != "균등가중치",
            corr_col,
        ]
    )

    min_rank_corr = float(
        non_base_corr.min()
    )

else:
    min_rank_corr = None


if "중복률" in overlap_df.columns:

    non_base_overlap = (
        overlap_df.loc[
            overlap_df[
                "시나리오"
            ]
            != "균등가중치",
            "중복률",
        ]
    )

    min_overlap = float(
        non_base_overlap.min()
    )

else:
    min_overlap = None


# ============================================================
# 핵심 결과 요약 테이블
# ============================================================

key_results = pd.DataFrame(
    [
        {
            "항목":
                "전체 분석 지역",
            "결과":
                total_regions,
            "설명":
                "2025 기준 시군구급 분석지역",
        },
        {
            "항목":
                "최종 군집 수",
            "결과":
                3,
            "설명":
                (
                    "일반도시_중간형 / "
                    "고령화_청년유출형 / "
                    "경제활동_청년유입형"
                ),
        },
        {
            "항목":
                "우선 검토 지역",
            "결과":
                priority_count,
            "설명":
                (
                    "고령화 수요 상위 25%이면서 "
                    "인프라 공급 하위 50%"
                ),
        },
        {
            "항목":
                "안정적 핵심 미스매치 지역",
            "결과":
                stable_count,
            "설명":
                (
                    "4개 가중치 시나리오 모두 "
                    "미스매치 Top20에 포함"
                ),
        },
        {
            "항목":
                "기본안 Top20의 Cluster 2 지역",
            "결과":
                top20_cluster2_count,
            "설명":
                (
                    "고령화_청년유출형에 "
                    "미스매치 상위지역 집중"
                ),
        },
        {
            "항목":
                "핵심지역의 Cluster 2 지역",
            "결과":
                stable_cluster2_count,
            "설명":
                (
                    "민감도 분석 안정지역의 "
                    "군집 특성"
                ),
        },
        {
            "항목":
                "민감도 최소 순위상관",
            "결과":
                (
                    round(
                        min_rank_corr,
                        4,
                    )
                    if min_rank_corr
                    is not None
                    else None
                ),
            "설명":
                (
                    "균등가중치 대비 "
                    "Spearman 순위 상관"
                ),
        },
        {
            "항목":
                "민감도 최소 Top20 중복률",
            "결과":
                (
                    round(
                        min_overlap,
                        2,
                    )
                    if min_overlap
                    is not None
                    else None
                ),
            "설명":
                (
                    "균등가중치 Top20 대비 "
                    "다른 시나리오의 최소 중복률(%)"
                ),
        },
    ]
)


key_results.to_csv(
    OUTPUT_DIR
    / "00_key_results.csv",
    index=False,
    encoding="utf-8-sig",
)


print("\n[핵심 결과]")

print(
    key_results.to_string(
        index=False,
    )
)


# ============================================================
# 최종 분석 요약 TXT
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "FINAL_ANALYSIS_SUMMARY.txt"
)


with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT\n"
    )

    f.write(
        "지역별 고령화 충격과 "
        "생활 인프라 미스매치 분석\n"
    )

    f.write(
        "=" * 70
        + "\n\n"
    )

    # --------------------------------------------------------
    # 분석 범위
    # --------------------------------------------------------

    f.write(
        "[1. 분석 범위]\n"
    )

    f.write(
        f"- 분석지역: "
        f"{total_regions}개 시군구급 지역\n"
    )

    f.write(
        "- 인구·청년 이동: "
        "2016~2025\n"
    )

    f.write(
        "- 경제 지표: 2024\n"
    )

    f.write(
        "- 생활 인프라: "
        "병원, 약국, 노인복지시설, "
        "버스정류장, 철도·도시철도역\n\n"
    )

    # --------------------------------------------------------
    # 군집 결과
    # --------------------------------------------------------

    f.write(
        "[2. 지역 유형 군집분석]\n"
    )

    f.write(
        "- 최종 K = 3\n"
    )

    for _, row in (
        cluster_counts.iterrows()
    ):

        f.write(
            f"- Cluster "
            f"{int(row['cluster'])}: "
            f"{row['cluster_name']} "
            f"({int(row['지역수'])}개 지역)\n"
        )

    f.write(
        "\n"
    )

    f.write(
        "Cluster 1은 상대적으로 고령화 수준이 낮고 "
        "청년 이동 및 경제활동이 중간 수준인 "
        "일반 도시형 지역으로 나타남.\n"
    )

    f.write(
        "Cluster 2는 고령화 수준과 고령화 진행 속도가 높고 "
        "청년 순유출이 크게 나타나는 지역군으로 분류됨.\n"
    )

    f.write(
        "Cluster 3은 상대적으로 고령화 수준이 낮으며 "
        "청년 순유입과 경제활동 수준이 높은 지역군으로 나타남.\n\n"
    )

    # --------------------------------------------------------
    # 미스매치 결과
    # --------------------------------------------------------

    f.write(
        "[3. 생활 인프라 미스매치]\n"
    )

    f.write(
        "고령화 수요 점수는 현재 고령화율과 "
        "2016~2025년 고령화율 변화폭의 "
        "백분위 평균으로 구성함.\n"
    )

    f.write(
        "생활 인프라 공급 점수는 "
        "노인 1,000명당 병원·약국·복지시설·"
        "버스정류장·철도역 수준의 "
        "백분위 평균으로 구성함.\n"
    )

    f.write(
        "미스매치 점수는 "
        "'고령화 수요 점수 - "
        "생활 인프라 공급 점수'로 정의함.\n\n"
    )

    f.write(
        f"- 우선 검토 지역: "
        f"{priority_count}개\n"
    )

    f.write(
        f"- 균등가중치 기준 "
        f"미스매치 Top20 중 "
        f"Cluster 2 지역: "
        f"{top20_cluster2_count}개\n\n"
    )

    f.write(
        "[미스매치 상위 20개]\n"
    )

    f.write(
        top20_df
        .round(3)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    # --------------------------------------------------------
    # 민감도 분석
    # --------------------------------------------------------

    f.write(
        "[4. 민감도 분석]\n"
    )

    f.write(
        "생활 인프라별 가중치 설정에 따른 "
        "결과 의존성을 확인하기 위해 "
        "균등가중치, 의료강조, 교통강조, "
        "철도영향축소 등 4개 시나리오를 비교함.\n\n"
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
        overlap_df
        .round(2)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    if (
        min_rank_corr
        is not None
    ):

        f.write(
            f"- 균등가중치 대비 "
            f"최소 Spearman 순위 상관: "
            f"{min_rank_corr:.4f}\n"
        )

    if (
        min_overlap
        is not None
    ):

        f.write(
            f"- 균등가중치 Top20 대비 "
            f"최소 중복률: "
            f"{min_overlap:.1f}%\n"
        )

    f.write(
        f"- 4개 시나리오에서 "
        f"모두 Top20에 포함된 지역: "
        f"{stable_count}개\n\n"
    )

    # --------------------------------------------------------
    # 안정적 핵심지역
    # --------------------------------------------------------

    f.write(
        "[5. 안정적 핵심 미스매치 지역]\n"
    )

    f.write(
        stable_summary
        .round(2)
        .to_string(
            index=False,
        )
    )

    f.write(
        "\n\n"
    )

    # --------------------------------------------------------
    # 최종 해석
    # --------------------------------------------------------

    f.write(
        "[6. 핵심 해석]\n"
    )

    f.write(
        "1) 고령화가 빠르게 진행되는 지역은 "
        "청년 순유출이 큰 경향을 보였음.\n"
    )

    f.write(
        "2) 고령화·청년유출형 지역에서 "
        "생활 인프라 미스매치가 "
        "상대적으로 크게 나타남.\n"
    )

    f.write(
        "3) 고령지역이 모든 인프라에서 "
        "동일하게 부족한 것은 아니며, "
        "복지시설·버스정류장과 의료·철도 등 "
        "인프라 분야별 차이가 확인됨.\n"
    )

    f.write(
        "4) 인프라별 가중치를 변경한 "
        "민감도 분석에서도 주요 지역의 "
        "순위가 높은 수준으로 유지됨.\n"
    )

    f.write(
        "5) 따라서 단순 고령인구 규모만으로 "
        "지역을 판단하기보다 고령화 속도와 "
        "생활 인프라 공급의 상대적 수준을 "
        "함께 고려할 필요가 있음.\n\n"
    )

    # --------------------------------------------------------
    # 주의
    # --------------------------------------------------------

    f.write(
        "[7. 해석상 주의사항]\n"
    )

    f.write(
        "- 본 분석의 상관관계는 인과관계를 의미하지 않음.\n"
    )

    f.write(
        "- 미스매치 점수는 229개 지역 내 "
        "상대적 비교 지표이며 절대적인 "
        "지역 취약성 판정 기준이 아님.\n"
    )

    f.write(
        "- 생활 인프라 지표는 시설의 수를 기반으로 하므로 "
        "실제 접근시간, 서비스 품질, 시설 규모 등은 "
        "직접 반영하지 못함.\n"
    )

    f.write(
        "- 강원 고성군 버스정류장 지표는 "
        "원자료 부재로 K-Means 및 미스매치 분석 단계에서 "
        "강원 지역 중앙값으로 보완함.\n"
    )


# ============================================================
# README에 옮기기 쉬운 Markdown 생성
# ============================================================

markdown_path = (
    OUTPUT_DIR
    / "README_RESULT_SNIPPET.md"
)


with open(
    markdown_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "## 주요 분석 결과\n\n"
    )

    f.write(
        f"- 분석 대상: "
        f"시군구급 {total_regions}개 지역\n"
    )

    f.write(
        "- K-Means 최종 군집 수: **3개**\n"
    )

    f.write(
        "- 군집 유형: "
        "**일반도시·중간형 / "
        "고령화·청년유출형 / "
        "경제활동·청년유입형**\n"
    )

    f.write(
        f"- 고령화 수요가 높고 "
        f"생활 인프라 공급이 상대적으로 낮은 "
        f"우선 검토 지역: **{priority_count}개**\n"
    )

    f.write(
        f"- 4개 가중치 시나리오에서 "
        f"모두 미스매치 Top20에 포함된 "
        f"핵심 지역: **{stable_count}개**\n"
    )

    if (
        min_rank_corr
        is not None
    ):

        f.write(
            f"- 민감도 분석 최소 "
            f"Spearman 순위 상관계수: "
            f"**{min_rank_corr:.4f}**\n"
        )

    if (
        min_overlap
        is not None
    ):

        f.write(
            f"- 가중치 변경 시 "
            f"Top20 최소 중복률: "
            f"**{min_overlap:.0f}%**\n"
        )

    f.write(
        "\n"
    )

    f.write(
        "### 해석\n\n"
    )

    f.write(
        "- 고령화가 빠르게 진행되는 지역에서 "
        "청년 순유출이 함께 나타나는 경향 확인\n"
    )

    f.write(
        "- 고령화·청년유출형 군집에서 "
        "생활 인프라 미스매치가 상대적으로 크게 나타남\n"
    )

    f.write(
        "- 고령지역이라도 모든 인프라가 부족한 것이 아니라 "
        "복지·버스와 의료·철도 간 서로 다른 공급 구조 확인\n"
    )

    f.write(
        "- 인프라 가중치를 변경해도 "
        "주요 미스매치 지역 순위가 안정적으로 유지됨\n"
    )

    f.write(
        "\n"
    )

    f.write(
        "> 미스매치 점수는 분석 대상 지역 내 "
        "상대적 수준을 비교한 지표이며 "
        "절대적인 지역 취약성 판정 기준은 아닙니다.\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("최종 분석 결과 정리 완료")
print("========================================")

print(
    f"저장 위치:\n"
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