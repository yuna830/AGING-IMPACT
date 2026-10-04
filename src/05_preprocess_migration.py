from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MIGRATION_FILE = (
    PROCESSED_DIR
    / "migration_2016_2025.csv"
)

POPULATION_FILE = (
    PROCESSED_DIR
    / "population_2016_2025.csv"
)

POPULATION_SUMMARY_FILE = (
    PROCESSED_DIR
    / "population_summary_2025.csv"
)


# ============================================================
# 프로젝트 설정
# ============================================================

START_YEAR = 2016
END_YEAR = 2025


# ============================================================
# 행정구역 코드 변경
# ============================================================
#
# 인구 데이터와 동일하게
# 2025 기준 행정구역 코드로 통일한다.
#
# 28170 인천 남구
# -> 28177 미추홀구
#
# 47720 경북 군위군
# -> 27720 대구 군위군
#
# 이동 데이터는 '기간 동안 발생한 이동량'이므로
# 코드 변경 전/후 데이터가 같은 연도에 존재하면
# 합산한다.
# ============================================================

REGION_CODE_MAP = {
    "28170": "28177",
    "47720": "27720",
}


# ============================================================
# CSV 읽기
# ============================================================

def read_processed_csv(
    file_path: Path,
) -> pd.DataFrame:
    """
    processed CSV를 UTF-8-SIG로 읽는다.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            "파일을 찾을 수 없습니다.\n"
            f"{file_path}"
        )

    return pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
        low_memory=False,
    )


# ============================================================
# 지역코드 정리
# ============================================================

def clean_region_code(
    series: pd.Series,
) -> pd.Series:
    """
    지역코드를 문자열 형태로 정리한다.

    예:
        11110.0
        -> 11110
    """

    return (
        series
        .astype(str)
        .str.strip()
        .str.replace(
            ".0",
            "",
            regex=False,
        )
    )


# ============================================================
# 1. 데이터 읽기
# ============================================================

def load_data():
    print()
    print("=" * 70)
    print("1. 데이터 읽기")
    print("=" * 70)

    migration = read_processed_csv(
        MIGRATION_FILE
    )

    population = read_processed_csv(
        POPULATION_FILE
    )

    population_summary = read_processed_csv(
        POPULATION_SUMMARY_FILE
    )

    migration["지역코드"] = (
        clean_region_code(
            migration["지역코드"]
        )
    )

    population["지역코드"] = (
        clean_region_code(
            population["지역코드"]
        )
    )

    population_summary["지역코드"] = (
        clean_region_code(
            population_summary["지역코드"]
        )
    )

    print()
    print(
        f"이동 데이터 행 수: "
        f"{len(migration)}"
    )

    print(
        f"이동 데이터 지역 수: "
        f"{migration['지역코드'].nunique()}"
    )

    print(
        f"인구 데이터 지역 수: "
        f"{population['지역코드'].nunique()}"
    )

    print(
        f"인구 요약 지역 수: "
        f"{population_summary['지역코드'].nunique()}"
    )

    return (
        migration,
        population,
        population_summary,
    )


# ============================================================
# 2. 이동 데이터 행정구역 코드 통일
# ============================================================

def harmonize_migration_codes(
    migration: pd.DataFrame,
    population_summary: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("2. 이동 데이터 행정구역 코드 통일")
    print("=" * 70)

    df = migration.copy()

    before_count = (
        df["지역코드"].nunique()
    )

    # --------------------------------------------------------
    # 과거 코드 -> 현재 코드
    # --------------------------------------------------------

    df["지역코드"] = (
        df["지역코드"]
        .replace(
            REGION_CODE_MAP
        )
    )

    # --------------------------------------------------------
    # 2025 기준 인구 데이터의 지역명 사용
    #
    # 지역명은 이동 데이터 자체의 이름보다
    # population_summary의 이름을 기준으로 맞춘다.
    # --------------------------------------------------------

    current_region_names = (
        population_summary[
            [
                "지역코드",
                "지역명",
            ]
        ]
        .drop_duplicates(
            subset=["지역코드"]
        )
        .rename(
            columns={
                "지역명":
                    "현재지역명"
            }
        )
    )

    df = pd.merge(
        df,
        current_region_names,
        on="지역코드",
        how="left",
    )

    df["지역명"] = (
        df["현재지역명"]
        .fillna(
            df["지역명"]
        )
    )

    df = df.drop(
        columns=[
            "현재지역명"
        ]
    )

    # --------------------------------------------------------
    # 코드 변경으로 동일 지역/연도 행이 겹치면 합산
    #
    # 예:
    # 경북 군위군 + 대구 군위군
    #
    # 이동량은 flow이므로 합산한다.
    # --------------------------------------------------------

    df = (
        df
        .groupby(
            [
                "지역코드",
                "지역명",
                "연도",
            ],
            as_index=False,
        )
        .agg(
            청년전입=(
                "청년전입",
                "sum",
            ),
            청년전출=(
                "청년전출",
                "sum",
            ),
            청년순이동=(
                "청년순이동",
                "sum",
            ),
        )
    )

    after_count = (
        df["지역코드"].nunique()
    )

    print()
    print(
        f"통일 전 이동 지역 수: "
        f"{before_count}"
    )

    print(
        f"코드 통일 후 이동 지역 수: "
        f"{after_count}"
    )

    return df


# ============================================================
# 3. 현재 분석지역 229개로 필터링
# ============================================================

def filter_current_regions(
    migration: pd.DataFrame,
    population_summary: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("3. 현재 분석 대상 지역으로 필터링")
    print("=" * 70)

    analysis_codes = set(
        population_summary[
            "지역코드"
        ]
    )

    migration_codes = set(
        migration[
            "지역코드"
        ]
    )

    excluded_codes = (
        migration_codes
        - analysis_codes
    )

    print()
    print(
        f"분석 기준 지역 수: "
        f"{len(analysis_codes)}"
    )

    print(
        f"분석에서 제외되는 이동 지역코드 수: "
        f"{len(excluded_codes)}"
    )

    if excluded_codes:
        print()
        print(
            "[제외되는 지역]"
        )

        excluded_regions = (
            migration[
                migration[
                    "지역코드"
                ]
                .isin(
                    excluded_codes
                )
            ][
                [
                    "지역코드",
                    "지역명",
                ]
            ]
            .drop_duplicates()
            .sort_values(
                "지역코드"
            )
        )

        print(
            excluded_regions
            .to_string(
                index=False
            )
        )

    filtered = (
        migration[
            migration[
                "지역코드"
            ]
            .isin(
                analysis_codes
            )
        ]
        .copy()
    )

    # --------------------------------------------------------
    # canonical 지역명 다시 적용
    # --------------------------------------------------------

    current_names = (
        population_summary[
            [
                "지역코드",
                "지역명",
            ]
        ]
        .drop_duplicates()
        .set_index(
            "지역코드"
        )[
            "지역명"
        ]
        .to_dict()
    )

    filtered["지역명"] = (
        filtered["지역코드"]
        .map(
            current_names
        )
    )

    filtered = (
        filtered
        .sort_values(
            [
                "지역코드",
                "연도",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    print()
    print(
        f"필터링 후 이동 지역 수: "
        f"{filtered['지역코드'].nunique()}"
    )

    return filtered


# ============================================================
# 4. 누락된 지역/연도 확인
# ============================================================

def check_region_year_completeness(
    migration: pd.DataFrame,
    population_summary: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("4. 지역 × 연도 완전성 확인")
    print("=" * 70)

    expected_codes = set(
        population_summary[
            "지역코드"
        ]
    )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    issues = []

    for code in sorted(
        expected_codes
    ):

        region_data = (
            migration[
                migration[
                    "지역코드"
                ]
                == code
            ]
        )

        actual_years = set(
            region_data[
                "연도"
            ]
            .astype(int)
            .tolist()
        )

        missing_years = (
            expected_years
            - actual_years
        )

        if missing_years:

            region_name = (
                population_summary.loc[
                    population_summary[
                        "지역코드"
                    ]
                    == code,
                    "지역명",
                ]
                .iloc[0]
            )

            issues.append(
                {
                    "지역코드":
                        code,

                    "지역명":
                        region_name,

                    "누락연도":
                        ", ".join(
                            map(
                                str,
                                sorted(
                                    missing_years
                                ),
                            )
                        ),
                }
            )

    print()

    if not issues:
        print(
            "229개 지역 모두 "
            "2016~2025 이동 데이터 존재"
        )

    else:

        issue_df = pd.DataFrame(
            issues
        )

        print(
            issue_df.to_string(
                index=False
            )
        )


# ============================================================
# 5. 청년순이동 요약 계산
# ============================================================

def calculate_migration_summary(
    migration: pd.DataFrame,
    population: pd.DataFrame,
    population_summary: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("5. 청년순이동 지표 계산")
    print("=" * 70)

    # --------------------------------------------------------
    # 10년 누적 청년전입/전출/순이동
    # --------------------------------------------------------

    migration_summary = (
        migration
        .groupby(
            [
                "지역코드",
                "지역명",
            ],
            as_index=False,
        )
        .agg(
            청년전입_누적_2016_2025=(
                "청년전입",
                "sum",
            ),
            청년전출_누적_2016_2025=(
                "청년전출",
                "sum",
            ),
            청년순이동_누적_2016_2025=(
                "청년순이동",
                "sum",
            ),
        )
    )

    # --------------------------------------------------------
    # 2016년 청년인구 가져오기
    #
    # 청년순이동률 분모
    # --------------------------------------------------------

    youth_2016 = (
        population[
            population[
                "연도"
            ]
            == START_YEAR
        ][
            [
                "지역코드",
                "청년인구",
            ]
        ]
        .rename(
            columns={
                "청년인구":
                    "청년인구_2016"
            }
        )
        .copy()
    )

    migration_summary = pd.merge(
        migration_summary,
        youth_2016,
        on="지역코드",
        how="left",
    )

    # --------------------------------------------------------
    # 청년순이동률
    #
    # 2016~2025 누적 청년순이동
    # -------------------------- × 100
    #      2016년 청년인구
    # --------------------------------------------------------

    migration_summary[
        "청년순이동률_2016_2025"
    ] = (
        migration_summary[
            "청년순이동_누적_2016_2025"
        ]
        /
        migration_summary[
            "청년인구_2016"
        ]
        * 100
    )

    migration_summary[
        "청년순이동률_2016_2025"
    ] = (
        migration_summary[
            "청년순이동률_2016_2025"
        ]
        .round(2)
    )

    # --------------------------------------------------------
    # population_summary 기준으로 229개 지역 보장
    # --------------------------------------------------------

    base_regions = (
        population_summary[
            [
                "지역코드",
                "지역명",
            ]
        ]
        .copy()
    )

    migration_summary = pd.merge(
        base_regions,
        migration_summary.drop(
            columns=[
                "지역명"
            ]
        ),
        on="지역코드",
        how="left",
    )

    migration_summary = (
        migration_summary
        .sort_values(
            "지역코드"
        )
        .reset_index(
            drop=True
        )
    )

    return migration_summary


# ============================================================
# 6. 결과 저장
# ============================================================

def save_results(
    migration_clean: pd.DataFrame,
    migration_summary: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("6. 결과 저장")
    print("=" * 70)

    clean_file = (
        PROCESSED_DIR
        / "migration_2016_2025_clean.csv"
    )

    summary_file = (
        PROCESSED_DIR
        / "migration_summary_2016_2025.csv"
    )

    migration_clean.to_csv(
        clean_file,
        index=False,
        encoding="utf-8-sig",
    )

    migration_summary.to_csv(
        summary_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"저장 완료: "
        f"{clean_file}"
    )

    print(
        f"저장 완료: "
        f"{summary_file}"
    )


# ============================================================
# 7. 최종 검증
# ============================================================

def validate_results(
    migration_clean: pd.DataFrame,
    migration_summary: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("7. 결과 검증")
    print("=" * 70)

    print()
    print(
        "[연도별 지역 수]"
    )

    yearly_counts = (
        migration_clean
        .groupby(
            "연도"
        )[
            "지역코드"
        ]
        .nunique()
    )

    print(
        yearly_counts
        .to_string()
    )

    print()
    print(
        "[정리된 이동 데이터 결측치]"
    )

    print(
        migration_clean
        .isnull()
        .sum()
    )

    print()
    print(
        "[이동 요약 데이터 결측치]"
    )

    print(
        migration_summary
        .isnull()
        .sum()
    )

    print()
    print(
        f"[이동 요약 지역 수] "
        f"{len(migration_summary)}"
    )

    print()
    print(
        "[청년순이동률 하위 10개 지역]"
    )

    print(
        migration_summary
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=True,
        )
        .head(10)[
            [
                "지역코드",
                "지역명",
                "청년인구_2016",
                "청년순이동_누적_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[청년순이동률 상위 10개 지역]"
    )

    print(
        migration_summary
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=False,
        )
        .head(10)[
            [
                "지역코드",
                "지역명",
                "청년인구_2016",
                "청년순이동_누적_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 미추홀구 / 군위군 확인
    # --------------------------------------------------------

    print()
    print(
        "[미추홀구 확인]"
    )

    print(
        migration_clean[
            migration_clean[
                "지역코드"
            ]
            == "28177"
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[군위군 확인]"
    )

    print(
        migration_clean[
            migration_clean[
                "지역코드"
            ]
            == "27720"
        ]
        .to_string(
            index=False
        )
    )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("청년 이동 데이터 전처리")
    print("행정구역 변경 반영")
    print("=" * 70)

    (
        migration,
        population,
        population_summary,
    ) = load_data()

    migration_harmonized = (
        harmonize_migration_codes(
            migration,
            population_summary,
        )
    )

    migration_clean = (
        filter_current_regions(
            migration_harmonized,
            population_summary,
        )
    )

    check_region_year_completeness(
        migration_clean,
        population_summary,
    )

    migration_summary = (
        calculate_migration_summary(
            migration_clean,
            population,
            population_summary,
        )
    )

    save_results(
        migration_clean,
        migration_summary,
    )

    validate_results(
        migration_clean,
        migration_summary,
    )

    print()
    print("=" * 70)
    print("청년 이동 데이터 전처리 완료")
    print("=" * 70)

    print()
    print(
        "생성 파일:"
    )

    print(
        "1. "
        "migration_2016_2025_clean.csv"
    )

    print(
        "2. "
        "migration_summary_2016_2025.csv"
    )


if __name__ == "__main__":
    main()