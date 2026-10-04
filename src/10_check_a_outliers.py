from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULT_DIR = PROJECT_ROOT / "results" / "a_outliers"

INPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_features.csv"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 분석 대상 변수
# ============================================================

OUTLIER_COLUMNS = [
    "고령화율_2025",
    "고령화율변화폭_2016_2025",
    "청년비율_2025",
    "청년비율변화폭_2016_2025",
    "인구증감률_2016_2025",
    "청년순이동률_2016_2025",
    "인구천명당_사업체수_2024",
    "인구천명당_종사자수_2024",
    "사업체당_종사자수_2024",
]


# ============================================================
# 데이터 읽기
# ============================================================

def load_data():
    print()
    print("=" * 70)
    print("1. A 파생변수 데이터 읽기")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "a_dataset_features.csv가 없습니다.\n"
            f"{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
        low_memory=False,
    )

    print()
    print(
        f"전체 지역 수: {len(df)}"
    )

    return df


# ============================================================
# IQR 이상치 계산
# ============================================================

def calculate_iqr_outliers(
    df,
    column,
):
    """
    IQR 방식으로 이상치 탐지.

    하한:
        Q1 - 1.5 * IQR

    상한:
        Q3 + 1.5 * IQR
    """

    q1 = df[column].quantile(
        0.25
    )

    q3 = df[column].quantile(
        0.75
    )

    iqr = q3 - q1

    lower = (
        q1
        - 1.5 * iqr
    )

    upper = (
        q3
        + 1.5 * iqr
    )

    outliers = (
        df[
            (
                df[column]
                < lower
            )
            |
            (
                df[column]
                > upper
            )
        ]
        .copy()
    )

    return (
        q1,
        q3,
        iqr,
        lower,
        upper,
        outliers,
    )


# ============================================================
# 전체 변수 이상치 확인
# ============================================================

def check_all_outliers(
    df,
):
    print()
    print("=" * 70)
    print("2. IQR 기준 이상치 확인")
    print("=" * 70)

    summary_rows = []
    outlier_rows = []

    for column in OUTLIER_COLUMNS:

        (
            q1,
            q3,
            iqr,
            lower,
            upper,
            outliers,
        ) = calculate_iqr_outliers(
            df,
            column,
        )

        summary_rows.append(
            {
                "지표": column,
                "Q1": q1,
                "Q3": q3,
                "IQR": iqr,
                "하한": lower,
                "상한": upper,
                "이상치수": len(outliers),
            }
        )

        print()
        print(
            f"[{column}]"
        )

        print(
            f"Q1: {q1:.2f}"
        )

        print(
            f"Q3: {q3:.2f}"
        )

        print(
            f"IQR: {iqr:.2f}"
        )

        print(
            f"하한: {lower:.2f}"
        )

        print(
            f"상한: {upper:.2f}"
        )

        print(
            f"이상치 지역 수: "
            f"{len(outliers)}"
        )

        if not outliers.empty:

            temp = (
                outliers[
                    [
                        "지역코드",
                        "시도",
                        "지역명",
                        column,
                    ]
                ]
                .copy()
            )

            temp[
                "지표"
            ] = column

            temp = temp.rename(
                columns={
                    column:
                        "값"
                }
            )

            outlier_rows.append(
                temp[
                    [
                        "지표",
                        "지역코드",
                        "시도",
                        "지역명",
                        "값",
                    ]
                ]
            )

    summary_df = pd.DataFrame(
        summary_rows
    )

    if outlier_rows:

        outlier_df = pd.concat(
            outlier_rows,
            ignore_index=True,
        )

    else:

        outlier_df = pd.DataFrame(
            columns=[
                "지표",
                "지역코드",
                "시도",
                "지역명",
                "값",
            ]
        )

    return (
        summary_df,
        outlier_df,
    )


# ============================================================
# 중요 극단 지역 직접 확인
# ============================================================

def check_extreme_regions(
    df,
):
    print()
    print("=" * 70)
    print("3. 주요 극단 지역 확인")
    print("=" * 70)

    configs = [
        (
            "청년순이동률_2016_2025",
            False,
            "청년순유입 상위 10개",
        ),
        (
            "청년순이동률_2016_2025",
            True,
            "청년순유출 상위 10개",
        ),
        (
            "인구증감률_2016_2025",
            False,
            "인구증가 상위 10개",
        ),
        (
            "인구증감률_2016_2025",
            True,
            "인구감소 상위 10개",
        ),
        (
            "인구천명당_사업체수_2024",
            False,
            "인구천명당 사업체수 상위 10개",
        ),
        (
            "인구천명당_종사자수_2024",
            False,
            "인구천명당 종사자수 상위 10개",
        ),
        (
            "사업체당_종사자수_2024",
            False,
            "사업체당 종사자수 상위 10개",
        ),
    ]

    result_list = []

    for (
        column,
        ascending,
        title,
    ) in configs:

        temp = (
            df
            .sort_values(
                column,
                ascending=ascending,
            )
            .head(10)[
                [
                    "지역코드",
                    "시도",
                    "지역명",
                    column,
                ]
            ]
            .copy()
        )

        temp[
            "구분"
        ] = title

        temp[
            "순위"
        ] = range(
            1,
            11,
        )

        temp[
            "지표"
        ] = column

        temp = temp.rename(
            columns={
                column:
                    "값"
            }
        )

        result_list.append(
            temp[
                [
                    "구분",
                    "순위",
                    "지역코드",
                    "시도",
                    "지역명",
                    "지표",
                    "값",
                ]
            ]
        )

        print()
        print(
            f"[{title}]"
        )

        print(
            temp[
                [
                    "순위",
                    "지역코드",
                    "시도",
                    "지역명",
                    "값",
                ]
            ]
            .to_string(
                index=False
            )
        )

    result = pd.concat(
        result_list,
        ignore_index=True,
    )

    return result


# ============================================================
# 극단 기준 별도 검사
# ============================================================

def check_rule_based_extremes(
    df,
):
    print()
    print("=" * 70)
    print("4. 기준값 기반 극단 지역 확인")
    print("=" * 70)

    rules = []

    # --------------------------------------------------------
    # 청년순이동률 절댓값 50% 이상
    # --------------------------------------------------------

    youth_extreme = (
        df[
            df[
                "청년순이동률_2016_2025"
            ]
            .abs()
            >= 50
        ]
        .copy()
    )

    youth_extreme[
        "검사기준"
    ] = (
        "청년순이동률 절댓값 50% 이상"
    )

    rules.append(
        youth_extreme
    )

    print()
    print(
        "[청년순이동률 절댓값 50% 이상]"
    )

    print(
        youth_extreme[
            [
                "지역코드",
                "시도",
                "지역명",
                "청년순이동률_2016_2025",
            ]
        ]
        .sort_values(
            "청년순이동률_2016_2025"
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 인구증감률 절댓값 30% 이상
    # --------------------------------------------------------

    population_extreme = (
        df[
            df[
                "인구증감률_2016_2025"
            ]
            .abs()
            >= 30
        ]
        .copy()
    )

    population_extreme[
        "검사기준"
    ] = (
        "인구증감률 절댓값 30% 이상"
    )

    rules.append(
        population_extreme
    )

    print()
    print(
        "[인구증감률 절댓값 30% 이상]"
    )

    print(
        population_extreme[
            [
                "지역코드",
                "시도",
                "지역명",
                "인구증감률_2016_2025",
            ]
        ]
        .sort_values(
            "인구증감률_2016_2025"
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 인구 천명당 사업체수 250 이상
    # --------------------------------------------------------

    business_extreme = (
        df[
            df[
                "인구천명당_사업체수_2024"
            ]
            >= 250
        ]
        .copy()
    )

    business_extreme[
        "검사기준"
    ] = (
        "인구천명당 사업체수 250 이상"
    )

    rules.append(
        business_extreme
    )

    print()
    print(
        "[인구천명당 사업체수 250 이상]"
    )

    print(
        business_extreme[
            [
                "지역코드",
                "시도",
                "지역명",
                "총인구_2024",
                "사업체수_2024",
                "인구천명당_사업체수_2024",
            ]
        ]
        .sort_values(
            "인구천명당_사업체수_2024",
            ascending=False,
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 인구 천명당 종사자수 1000 이상
    # --------------------------------------------------------

    employee_extreme = (
        df[
            df[
                "인구천명당_종사자수_2024"
            ]
            >= 1000
        ]
        .copy()
    )

    employee_extreme[
        "검사기준"
    ] = (
        "인구천명당 종사자수 1000 이상"
    )

    rules.append(
        employee_extreme
    )

    print()
    print(
        "[인구천명당 종사자수 1000 이상]"
    )

    print(
        employee_extreme[
            [
                "지역코드",
                "시도",
                "지역명",
                "총인구_2024",
                "종사자수_2024",
                "인구천명당_종사자수_2024",
            ]
        ]
        .sort_values(
            "인구천명당_종사자수_2024",
            ascending=False,
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 결과 통합
    # --------------------------------------------------------

    combined = pd.concat(
        rules,
        ignore_index=True,
    )

    combined = (
        combined[
            [
                "검사기준",
                "지역코드",
                "시도",
                "지역명",
                "인구증감률_2016_2025",
                "청년순이동률_2016_2025",
                "인구천명당_사업체수_2024",
                "인구천명당_종사자수_2024",
                "사업체당_종사자수_2024",
            ]
        ]
    )

    return combined


# ============================================================
# 상관계수 비교
# ============================================================

def compare_correlations_without_extremes(
    df,
):
    print()
    print("=" * 70)
    print("5. 극단값 제외 전/후 상관계수 비교")
    print("=" * 70)

    # --------------------------------------------------------
    # 기존 전체 데이터
    # --------------------------------------------------------

    full_aging_migration = (
        df[
            [
                "고령화율_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    full_population_migration = (
        df[
            [
                "인구증감률_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    full_aging_change_migration = (
        df[
            [
                "고령화율변화폭_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    # --------------------------------------------------------
    # 청년순이동률 IQR 이상치 제외
    # --------------------------------------------------------

    (
        _,
        _,
        _,
        lower,
        upper,
        _,
    ) = calculate_iqr_outliers(
        df,
        "청년순이동률_2016_2025",
    )

    filtered = (
        df[
            (
                df[
                    "청년순이동률_2016_2025"
                ]
                >= lower
            )
            &
            (
                df[
                    "청년순이동률_2016_2025"
                ]
                <= upper
            )
        ]
        .copy()
    )

    filtered_aging_migration = (
        filtered[
            [
                "고령화율_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    filtered_population_migration = (
        filtered[
            [
                "인구증감률_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    filtered_aging_change_migration = (
        filtered[
            [
                "고령화율변화폭_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    comparison = pd.DataFrame(
        [
            {
                "관계":
                    "고령화율 ↔ 청년순이동률",

                "전체":
                    full_aging_migration,

                "극단값제외":
                    filtered_aging_migration,
            },
            {
                "관계":
                    "인구증감률 ↔ 청년순이동률",

                "전체":
                    full_population_migration,

                "극단값제외":
                    filtered_population_migration,
            },
            {
                "관계":
                    "고령화율변화폭 ↔ 청년순이동률",

                "전체":
                    full_aging_change_migration,

                "극단값제외":
                    filtered_aging_change_migration,
            },
        ]
    )

    comparison[
        "차이"
    ] = (
        comparison[
            "극단값제외"
        ]
        -
        comparison[
            "전체"
        ]
    )

    print()
    print(
        f"전체 지역 수: "
        f"{len(df)}"
    )

    print(
        f"극단값 제외 후 지역 수: "
        f"{len(filtered)}"
    )

    print()
    print(
        comparison
        .round(3)
        .to_string(
            index=False
        )
    )

    return comparison


# ============================================================
# 결과 저장
# ============================================================

def save_results(
    summary_df,
    outlier_df,
    extreme_df,
    rule_df,
    correlation_comparison,
):
    print()
    print("=" * 70)
    print("6. 결과 저장")
    print("=" * 70)

    files = {
        "outlier_summary.csv":
            summary_df,

        "iqr_outlier_regions.csv":
            outlier_df,

        "extreme_rankings.csv":
            extreme_df,

        "rule_based_extremes.csv":
            rule_df,

        "correlation_outlier_comparison.csv":
            correlation_comparison,
    }

    for (
        filename,
        dataframe,
    ) in files.items():

        output_path = (
            RESULT_DIR
            / filename
        )

        dataframe.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

        print(
            f"[저장] {filename}"
        )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("A 데이터 이상치 검증")
    print("=" * 70)

    df = load_data()

    (
        summary_df,
        outlier_df,
    ) = check_all_outliers(
        df
    )

    extreme_df = (
        check_extreme_regions(
            df
        )
    )

    rule_df = (
        check_rule_based_extremes(
            df
        )
    )

    correlation_comparison = (
        compare_correlations_without_extremes(
            df
        )
    )

    save_results(
        summary_df,
        outlier_df,
        extreme_df,
        rule_df,
        correlation_comparison,
    )

    print()
    print("=" * 70)
    print("A 데이터 이상치 검증 완료")
    print("=" * 70)

    print()
    print(
        "결과 폴더:"
    )

    print(
        RESULT_DIR
    )


if __name__ == "__main__":
    main()