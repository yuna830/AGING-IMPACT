from pathlib import Path

import pandas as pd


# ============================================================
# 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

POPULATION_FILE = (
    PROCESSED_DIR / "population_2016_2025.csv"
)

POPULATION_SUMMARY_FILE = (
    PROCESSED_DIR / "population_summary_2025.csv"
)

MIGRATION_FILE = (
    PROCESSED_DIR / "migration_2016_2025.csv"
)


# ============================================================
# 파일 읽기
# ============================================================

def load_data():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("인구 데이터 추가 검증")
    print("=" * 70)

    population = pd.read_csv(
        POPULATION_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    population_summary = pd.read_csv(
        POPULATION_SUMMARY_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    migration = pd.read_csv(
        MIGRATION_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    return (
        population,
        population_summary,
        migration,
    )


# ============================================================
# 1. 결측치 행 확인
# ============================================================

def check_missing_population(
    population: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("1. 총인구 결측 지역 확인")
    print("=" * 70)

    missing = population[
        population["총인구"].isna()
    ].copy()

    if missing.empty:
        print()
        print("총인구 결측치 없음")
        return

    print()
    print(
        missing[
            [
                "지역코드",
                "지역명",
                "연도",
                "총인구",
                "청년인구",
                "고령인구",
                "고령화율",
                "청년비율",
            ]
        ].to_string(
            index=False
        )
    )


# ============================================================
# 2. 연도별 지역코드 비교
# ============================================================

def check_year_region_difference(
    population: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("2. 2016 / 2022 / 2025 지역코드 비교")
    print("=" * 70)

    codes_2016 = set(
        population.loc[
            population["연도"] == 2016,
            "지역코드",
        ]
    )

    codes_2021 = set(
        population.loc[
            population["연도"] == 2021,
            "지역코드",
        ]
    )

    codes_2022 = set(
        population.loc[
            population["연도"] == 2022,
            "지역코드",
        ]
    )

    codes_2025 = set(
        population.loc[
            population["연도"] == 2025,
            "지역코드",
        ]
    )

    added_2022 = (
        codes_2022
        - codes_2021
    )

    print()
    print(
        "[2021에는 없고 2022부터 있는 지역]"
    )

    if not added_2022:
        print("없음")

    else:
        temp = (
            population[
                population[
                    "지역코드"
                ].isin(
                    added_2022
                )
            ][
                [
                    "지역코드",
                    "지역명",
                    "연도",
                    "총인구",
                ]
            ]
            .sort_values(
                [
                    "지역코드",
                    "연도",
                ]
            )
        )

        print(
            temp.to_string(
                index=False
            )
        )

    print()
    print(
        "[2016에는 없고 2025에는 있는 지역]"
    )

    added_since_2016 = (
        codes_2025
        - codes_2016
    )

    if not added_since_2016:
        print("없음")

    else:
        temp = (
            population[
                population[
                    "지역코드"
                ].isin(
                    added_since_2016
                )
            ][
                [
                    "지역코드",
                    "지역명",
                    "연도",
                    "총인구",
                ]
            ]
            .sort_values(
                [
                    "지역코드",
                    "연도",
                ]
            )
        )

        print(
            temp.to_string(
                index=False
            )
        )


# ============================================================
# 3. 2016에는 있지만 2025에는 없는 지역
# ============================================================

def check_removed_regions(
    population: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("3. 2016 이후 사라진 지역 확인")
    print("=" * 70)

    codes_2016 = set(
        population.loc[
            population["연도"] == 2016,
            "지역코드",
        ]
    )

    codes_2025 = set(
        population.loc[
            population["연도"] == 2025,
            "지역코드",
        ]
    )

    removed = (
        codes_2016
        - codes_2025
    )

    if not removed:
        print()
        print("없음")
        return

    temp = (
        population[
            population[
                "지역코드"
            ].isin(
                removed
            )
        ][
            [
                "지역코드",
                "지역명",
                "연도",
                "총인구",
            ]
        ]
        .sort_values(
            [
                "지역코드",
                "연도",
            ]
        )
    )

    print()
    print(
        temp.to_string(
            index=False
        )
    )


# ============================================================
# 4. 요약 데이터에서 빠진 지역 확인
# ============================================================

def check_summary_difference(
    population: pd.DataFrame,
    population_summary: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("4. 2025 인구와 요약 데이터 차이")
    print("=" * 70)

    population_2025 = (
        population[
            population["연도"]
            == 2025
        ][
            [
                "지역코드",
                "지역명",
                "총인구",
            ]
        ]
        .copy()
    )

    summary_codes = set(
        population_summary[
            "지역코드"
        ]
    )

    missing_from_summary = (
        population_2025[
            ~population_2025[
                "지역코드"
            ].isin(
                summary_codes
            )
        ]
    )

    print()
    print(
        "[2025에는 있지만 "
        "2016→2025 요약에서 빠진 지역]"
    )

    if missing_from_summary.empty:
        print("없음")

    else:
        print(
            missing_from_summary
            .to_string(
                index=False
            )
        )


# ============================================================
# 5. 이동 데이터와 비교
# ============================================================

def check_migration_difference(
    population: pd.DataFrame,
    migration: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("5. 2025 인구 / 이동 지역 비교")
    print("=" * 70)

    population_2025 = (
        population[
            population["연도"]
            == 2025
        ][
            [
                "지역코드",
                "지역명",
            ]
        ]
        .drop_duplicates()
    )

    migration_2025 = (
        migration[
            migration["연도"]
            == 2025
        ][
            [
                "지역코드",
                "지역명",
            ]
        ]
        .drop_duplicates()
    )

    population_codes = set(
        population_2025[
            "지역코드"
        ]
    )

    migration_codes = set(
        migration_2025[
            "지역코드"
        ]
    )

    only_population = (
        population_codes
        - migration_codes
    )

    only_migration = (
        migration_codes
        - population_codes
    )

    print()
    print(
        "[인구에는 있고 이동에는 없는 지역]"
    )

    if not only_population:
        print("없음")
    else:
        print(
            population_2025[
                population_2025[
                    "지역코드"
                ].isin(
                    only_population
                )
            ]
            .sort_values(
                "지역코드"
            )
            .to_string(
                index=False
            )
        )

    print()
    print(
        "[이동에는 있고 인구에는 없는 지역]"
    )

    if not only_migration:
        print("없음")
    else:
        print(
            migration_2025[
                migration_2025[
                    "지역코드"
                ].isin(
                    only_migration
                )
            ]
            .sort_values(
                "지역코드"
            )
            .to_string(
                index=False
            )
        )


# ============================================================
# 메인
# ============================================================

def main():

    (
        population,
        population_summary,
        migration,
    ) = load_data()

    check_missing_population(
        population
    )

    check_year_region_difference(
        population
    )

    check_removed_regions(
        population
    )

    check_summary_difference(
        population,
        population_summary,
    )

    check_migration_difference(
        population,
        migration,
    )

    print()
    print("=" * 70)
    print("추가 검증 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()