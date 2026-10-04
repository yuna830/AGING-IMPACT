from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ============================================================
# 입력 파일
# ============================================================

A_DATASET_FILE = (
    PROCESSED_DIR
    / "a_dataset_merged.csv"
)

POPULATION_FILE = (
    PROCESSED_DIR
    / "population_2016_2025.csv"
)


# ============================================================
# 출력 파일
# ============================================================

OUTPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_features.csv"
)


# ============================================================
# 설정
# ============================================================

BASE_YEAR = 2016
ECONOMY_YEAR = 2024
END_YEAR = 2025


# ============================================================
# CSV 읽기
# ============================================================

def read_csv(
    file_path: Path,
) -> pd.DataFrame:
    """
    processed 폴더의 CSV 파일을 읽는다.
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
    지역코드를 문자열 형태로 통일한다.
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

    a_dataset = read_csv(
        A_DATASET_FILE
    )

    population = read_csv(
        POPULATION_FILE
    )

    a_dataset["지역코드"] = (
        clean_region_code(
            a_dataset["지역코드"]
        )
    )

    population["지역코드"] = (
        clean_region_code(
            population["지역코드"]
        )
    )

    print()
    print(
        f"A 최종 데이터 지역 수: "
        f"{a_dataset['지역코드'].nunique()}"
    )

    print(
        f"연도별 인구 데이터 지역 수: "
        f"{population['지역코드'].nunique()}"
    )

    return (
        a_dataset,
        population,
    )


# ============================================================
# 2. 2016 인구구조 지표 준비
# ============================================================

def create_2016_features(
    population: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("2. 2016년 인구구조 지표 준비")
    print("=" * 70)

    population_2016 = (
        population[
            population["연도"]
            == BASE_YEAR
        ][
            [
                "지역코드",
                "지역명",
                "총인구",
                "청년인구",
                "고령인구",
                "고령화율",
                "청년비율",
            ]
        ]
        .copy()
    )

    population_2016 = (
        population_2016.rename(
            columns={
                "총인구":
                    "총인구_2016_확인",

                "청년인구":
                    "청년인구_2016",

                "고령인구":
                    "고령인구_2016",

                "고령화율":
                    "고령화율_2016",

                "청년비율":
                    "청년비율_2016",
            }
        )
    )

    print()
    print(
        f"2016년 지역 수: "
        f"{len(population_2016)}"
    )

    print()
    print(
        population_2016
        .head(10)
        .to_string(
            index=False
        )
    )

    return population_2016


# ============================================================
# 3. 2024 인구 준비
# ============================================================

def create_2024_population(
    population: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("3. 2024년 인구 준비")
    print("=" * 70)

    population_2024 = (
        population[
            population["연도"]
            == ECONOMY_YEAR
        ][
            [
                "지역코드",
                "총인구",
            ]
        ]
        .rename(
            columns={
                "총인구":
                    "총인구_2024"
            }
        )
        .copy()
    )

    print()
    print(
        f"2024년 지역 수: "
        f"{len(population_2024)}"
    )

    return population_2024


# ============================================================
# 4. A 데이터와 결합
# ============================================================

def merge_features(
    a_dataset: pd.DataFrame,
    population_2016: pd.DataFrame,
    population_2024: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("4. 분석용 기초 변수 결합")
    print("=" * 70)

    # --------------------------------------------------------
    # 2016 지표의 지역명은 기존 최종 데이터와 중복되므로 제거
    # --------------------------------------------------------

    population_2016_for_merge = (
        population_2016.drop(
            columns=[
                "지역명"
            ]
        )
        .copy()
    )

    merged = pd.merge(
        a_dataset,
        population_2016_for_merge,
        on="지역코드",
        how="left",
        validate="one_to_one",
    )

    merged = pd.merge(
        merged,
        population_2024,
        on="지역코드",
        how="left",
        validate="one_to_one",
    )

    print()
    print(
        f"결합 후 지역 수: "
        f"{len(merged)}"
    )

    # --------------------------------------------------------
    # 기존 총인구_2016과 population 파일 값 비교
    # --------------------------------------------------------

    population_difference = (
        merged[
            "총인구_2016"
        ]
        -
        merged[
            "총인구_2016_확인"
        ]
    ).abs()

    mismatch_count = (
        population_difference
        .fillna(0)
        .gt(0)
        .sum()
    )

    print()
    print(
        f"2016 총인구 값 불일치 지역 수: "
        f"{mismatch_count}"
    )

    if mismatch_count > 0:
        print()
        print(
            "[2016 총인구 불일치 지역]"
        )

        mismatch = (
            merged[
                population_difference
                .fillna(0)
                .gt(0)
            ][
                [
                    "지역코드",
                    "지역명",
                    "총인구_2016",
                    "총인구_2016_확인",
                ]
            ]
        )

        print(
            mismatch.to_string(
                index=False
            )
        )

    return merged


# ============================================================
# 5. 파생변수 계산
# ============================================================

def create_derived_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("5. 파생변수 계산")
    print("=" * 70)

    result = df.copy()

    # --------------------------------------------------------
    # 고령화율 변화폭
    #
    # 단위: %p
    #
    # 예:
    # 2016 = 20%
    # 2025 = 25%
    # 변화폭 = +5%p
    # --------------------------------------------------------

    result[
        "고령화율변화폭_2016_2025"
    ] = (
        result[
            "고령화율_2025"
        ]
        -
        result[
            "고령화율_2016"
        ]
    )

    # --------------------------------------------------------
    # 청년비율 변화폭
    #
    # 단위: %p
    # --------------------------------------------------------

    result[
        "청년비율변화폭_2016_2025"
    ] = (
        result[
            "청년비율_2025"
        ]
        -
        result[
            "청년비율_2016"
        ]
    )

    # --------------------------------------------------------
    # 인구 천명당 사업체수
    #
    # 경제 데이터가 2024년이므로
    # 2024년 인구를 분모로 사용
    # --------------------------------------------------------

    result[
        "인구천명당_사업체수_2024"
    ] = (
        result[
            "사업체수_2024"
        ]
        /
        result[
            "총인구_2024"
        ]
        * 1000
    )

    # --------------------------------------------------------
    # 인구 천명당 종사자수
    # --------------------------------------------------------

    result[
        "인구천명당_종사자수_2024"
    ] = (
        result[
            "종사자수_2024"
        ]
        /
        result[
            "총인구_2024"
        ]
        * 1000
    )

    # --------------------------------------------------------
    # 사업체당 종사자수
    # --------------------------------------------------------

    result[
        "사업체당_종사자수_2024"
    ] = (
        result[
            "종사자수_2024"
        ]
        /
        result[
            "사업체수_2024"
        ]
    )

    # --------------------------------------------------------
    # 소수점 정리
    # --------------------------------------------------------

    round_columns = [
        "고령화율_2016",
        "청년비율_2016",
        "고령화율변화폭_2016_2025",
        "청년비율변화폭_2016_2025",
        "인구천명당_사업체수_2024",
        "인구천명당_종사자수_2024",
        "사업체당_종사자수_2024",
    ]

    for column in round_columns:

        result[column] = (
            result[column]
            .round(2)
        )

    return result


# ============================================================
# 6. 컬럼 정리
# ============================================================

def organize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("6. 컬럼 정리")
    print("=" * 70)

    columns = [
        # 지역
        "지역코드",
        "지역명",
        "시도",

        # 총인구
        "총인구_2016",
        "총인구_2024",
        "총인구_2025",

        # 고령인구
        "고령인구_2016",
        "고령인구_2025",

        # 청년인구
        "청년인구_2016",
        "청년인구_2025",

        # 인구구조 비율
        "고령화율_2016",
        "고령화율_2025",
        "고령화율변화폭_2016_2025",

        "청년비율_2016",
        "청년비율_2025",
        "청년비율변화폭_2016_2025",

        # 전체 인구 변화
        "인구증감률_2016_2025",

        # 청년 이동
        "청년전입_누적_2016_2025",
        "청년전출_누적_2016_2025",
        "청년순이동_누적_2016_2025",
        "청년순이동률_2016_2025",

        # 경제 절대값
        "사업체수_2024",
        "종사자수_2024",

        # 경제 보정값
        "인구천명당_사업체수_2024",
        "인구천명당_종사자수_2024",
        "사업체당_종사자수_2024",
    ]

    result = (
        df[
            columns
        ]
        .sort_values(
            "지역코드"
        )
        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# 7. 저장
# ============================================================

def save_result(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("7. 결과 저장")
    print("=" * 70)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"저장 완료:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# 8. 검증
# ============================================================

def validate_result(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("8. 파생변수 데이터 검증")
    print("=" * 70)

    print()
    print(
        f"전체 지역 수: "
        f"{len(df)}"
    )

    print()
    print(
        "[결측치]"
    )

    print(
        df
        .isnull()
        .sum()
        .to_string()
    )

    print()
    print(
        "[새 파생변수 기초통계]"
    )

    feature_columns = [
        "고령화율_2016",
        "고령화율_2025",
        "고령화율변화폭_2016_2025",
        "청년비율_2016",
        "청년비율_2025",
        "청년비율변화폭_2016_2025",
        "인구천명당_사업체수_2024",
        "인구천명당_종사자수_2024",
        "사업체당_종사자수_2024",
    ]

    print(
        df[
            feature_columns
        ]
        .describe()
        .round(2)
        .to_string()
    )

    # --------------------------------------------------------
    # 고령화 속도가 가장 빠른 지역
    # --------------------------------------------------------

    print()
    print(
        "[고령화율 증가폭 상위 10개 지역]"
    )

    print(
        df
        .sort_values(
            "고령화율변화폭_2016_2025",
            ascending=False,
        )
        .head(10)[
            [
                "지역코드",
                "지역명",
                "시도",
                "고령화율_2016",
                "고령화율_2025",
                "고령화율변화폭_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 청년비율 감소폭이 큰 지역
    # --------------------------------------------------------

    print()
    print(
        "[청년비율 감소폭 상위 10개 지역]"
    )

    print(
        df
        .sort_values(
            "청년비율변화폭_2016_2025",
            ascending=True,
        )
        .head(10)[
            [
                "지역코드",
                "지역명",
                "시도",
                "청년비율_2016",
                "청년비율_2025",
                "청년비율변화폭_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 인구 천명당 사업체수 상위
    # --------------------------------------------------------

    print()
    print(
        "[인구 천명당 사업체수 상위 10개 지역]"
    )

    print(
        df
        .sort_values(
            "인구천명당_사업체수_2024",
            ascending=False,
        )
        .head(10)[
            [
                "지역코드",
                "지역명",
                "시도",
                "총인구_2024",
                "사업체수_2024",
                "인구천명당_사업체수_2024",
            ]
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
    print("A 분석용 파생변수 생성")
    print("=" * 70)

    (
        a_dataset,
        population,
    ) = load_data()

    population_2016 = (
        create_2016_features(
            population
        )
    )

    population_2024 = (
        create_2024_population(
            population
        )
    )

    merged = merge_features(
        a_dataset,
        population_2016,
        population_2024,
    )

    featured = (
        create_derived_features(
            merged
        )
    )

    final = (
        organize_columns(
            featured
        )
    )

    save_result(
        final
    )

    validate_result(
        final
    )

    print()
    print("=" * 70)
    print("A 파생변수 생성 완료")
    print("=" * 70)

    print()
    print(
        "생성 파일:"
    )

    print(
        "a_dataset_features.csv"
    )


if __name__ == "__main__":
    main()