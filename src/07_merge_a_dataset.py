from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


POPULATION_SUMMARY_FILE = (
    PROCESSED_DIR
    / "population_summary_2025.csv"
)

MIGRATION_SUMMARY_FILE = (
    PROCESSED_DIR
    / "migration_summary_2016_2025.csv"
)

ECONOMY_FILE = (
    PROCESSED_DIR
    / "economy_2024_patched.csv"
)


# ============================================================
# 출력 파일
# ============================================================

FINAL_OUTPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_merged.csv"
)

ECONOMY_MISSING_FILE = (
    PROCESSED_DIR
    / "a_dataset_economy_missing.csv"
)


# ============================================================
# 시도 코드
# ============================================================
#
# 주민등록 행정구역 코드 앞 2자리 기준.
#
# 경제 데이터 지역명:
#   서울 종로구
#   경기 수원시
#   강원 춘천시
#   전북 전주시
#
# 형태와 맞추기 위해 사용한다.
# ============================================================

SIDO_PREFIX_MAP = {
    "11": "서울",
    "26": "부산",
    "27": "대구",
    "28": "인천",
    "29": "광주",
    "30": "대전",
    "31": "울산",
    "36": "세종",
    "41": "경기",
    "43": "충북",
    "44": "충남",
    "46": "전남",
    "47": "경북",
    "48": "경남",
    "50": "제주",
    "51": "강원",
    "52": "전북",
}


# ============================================================
# CSV 읽기
# ============================================================

def read_processed_csv(
    file_path: Path,
    dtype=None,
) -> pd.DataFrame:
    """
    data/processed의 CSV 파일을 읽는다.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            "파일을 찾을 수 없습니다.\n"
            f"{file_path}"
        )

    return pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        dtype=dtype,
        low_memory=False,
    )


# ============================================================
# 지역코드 정리
# ============================================================

def clean_region_code(
    series: pd.Series,
) -> pd.Series:
    """
    지역코드를 문자열 5자리 형태로 정리한다.

    예:
        11110.0 -> 11110
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
# 지역명 정리
# ============================================================

def normalize_region_name(
    series: pd.Series,
) -> pd.Series:
    """
    지역명의 불필요한 공백 정리.
    """

    return (
        series
        .astype(str)
        .str.strip()
        .str.replace(
            r"\s+",
            " ",
            regex=True,
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

    population = read_processed_csv(
        POPULATION_SUMMARY_FILE,
        dtype={
            "지역코드": str,
        },
    )

    migration = read_processed_csv(
        MIGRATION_SUMMARY_FILE,
        dtype={
            "지역코드": str,
        },
    )

    economy = read_processed_csv(
        ECONOMY_FILE,
    )

    population["지역코드"] = (
        clean_region_code(
            population["지역코드"]
        )
    )

    migration["지역코드"] = (
        clean_region_code(
            migration["지역코드"]
        )
    )

    population["지역명"] = (
        normalize_region_name(
            population["지역명"]
        )
    )

    migration["지역명"] = (
        normalize_region_name(
            migration["지역명"]
        )
    )

    economy["지역명"] = (
        normalize_region_name(
            economy["지역명"]
        )
    )

    print()
    print(
        f"인구 요약 지역 수: "
        f"{population['지역코드'].nunique()}"
    )

    print(
        f"이동 요약 지역 수: "
        f"{migration['지역코드'].nunique()}"
    )

    print(
        f"경제 데이터 지역 수: "
        f"{len(economy)}"
    )

    return (
        population,
        migration,
        economy,
    )


# ============================================================
# 2. 인구 + 이동 결합
# ============================================================

def merge_population_migration(
    population: pd.DataFrame,
    migration: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("2. 인구 + 이동 데이터 결합")
    print("=" * 70)

    # --------------------------------------------------------
    # 지역코드 중복 검사
    # --------------------------------------------------------

    population_duplicates = (
        population[
            population[
                "지역코드"
            ]
            .duplicated(
                keep=False
            )
        ]
    )

    migration_duplicates = (
        migration[
            migration[
                "지역코드"
            ]
            .duplicated(
                keep=False
            )
        ]
    )

    if not population_duplicates.empty:
        raise ValueError(
            "population_summary에 "
            "중복 지역코드가 있습니다.\n"
            f"{population_duplicates}"
        )

    if not migration_duplicates.empty:
        raise ValueError(
            "migration_summary에 "
            "중복 지역코드가 있습니다.\n"
            f"{migration_duplicates}"
        )

    # --------------------------------------------------------
    # 이동 데이터의 지역명은 제거
    #
    # 지역명은 population을 기준으로 유지한다.
    # --------------------------------------------------------

    migration_for_merge = (
        migration.drop(
            columns=[
                "지역명"
            ]
        )
        .copy()
    )

    # --------------------------------------------------------
    # LEFT JOIN
    #
    # population의 229개 지역을 기준으로 유지
    # --------------------------------------------------------

    merged = pd.merge(
        population,
        migration_for_merge,
        on="지역코드",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    print()
    print(
        "[인구 + 이동 JOIN 결과]"
    )

    print(
        merged["_merge"]
        .value_counts()
        .to_string()
    )

    missing_migration = (
        merged[
            merged["_merge"]
            != "both"
        ]
    )

    if not missing_migration.empty:
        print()
        print(
            "[이동 데이터가 없는 지역]"
        )

        print(
            missing_migration[
                [
                    "지역코드",
                    "지역명",
                    "_merge",
                ]
            ]
            .to_string(
                index=False
            )
        )

    merged = (
        merged.drop(
            columns=[
                "_merge"
            ]
        )
    )

    print()
    print(
        f"결합 후 지역 수: "
        f"{len(merged)}"
    )

    return merged


# ============================================================
# 3. 경제 데이터 JOIN용 지역키 만들기
# ============================================================

def create_economy_join_key(
    merged: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("3. 경제 데이터 JOIN 키 생성")
    print("=" * 70)

    df = merged.copy()

    # --------------------------------------------------------
    # 지역코드 앞 2자리 -> 시도명
    # --------------------------------------------------------

    df["시도코드"] = (
        df["지역코드"]
        .str[:2]
    )

    df["시도"] = (
        df["시도코드"]
        .map(
            SIDO_PREFIX_MAP
        )
    )

    # --------------------------------------------------------
    # 시도 매핑 실패 확인
    # --------------------------------------------------------

    missing_sido = (
        df[
            df["시도"].isna()
        ][
            [
                "지역코드",
                "지역명",
                "시도코드",
            ]
        ]
    )

    if not missing_sido.empty:
        print()
        print(
            "[시도 코드 매핑 실패]"
        )

        print(
            missing_sido
            .to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # 경제 데이터와 동일한 형태의 키 생성
    #
    # 예:
    # 11110 / 종로구
    # -> 서울 종로구
    #
    # 41110 / 수원시
    # -> 경기 수원시
    # --------------------------------------------------------

    df["경제지역키"] = (
        df["시도"]
        .fillna("")
        .str.strip()
        +
        " "
        +
        df["지역명"]
        .str.strip()
    )

    df["경제지역키"] = (
        df["경제지역키"]
        .str.strip()
    )

    print()
    print(
        "[JOIN 키 예시]"
    )

    print(
        df[
            [
                "지역코드",
                "지역명",
                "경제지역키",
            ]
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    return df


# ============================================================
# 4. 경제 데이터 정리
# ============================================================

def prepare_economy(
    economy: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("4. 경제 데이터 JOIN 준비")
    print("=" * 70)

    economy_clean = (
        economy.copy()
    )

    economy_clean[
        "경제지역키"
    ] = (
        normalize_region_name(
            economy_clean[
                "지역명"
            ]
        )
    )

    # --------------------------------------------------------
    # 중복 지역명 확인
    # --------------------------------------------------------

    duplicated = (
        economy_clean[
            economy_clean[
                "경제지역키"
            ]
            .duplicated(
                keep=False
            )
        ]
    )

    if not duplicated.empty:
        print()
        print(
            "[경제 데이터 중복 지역]"
        )

        print(
            duplicated
            .sort_values(
                "경제지역키"
            )
            .to_string(
                index=False
            )
        )

        raise ValueError(
            "경제 데이터에 중복 지역이 있어 "
            "JOIN을 중단합니다."
        )

    economy_clean = (
        economy_clean[
            [
                "경제지역키",
                "사업체수_2024",
                "종사자수_2024",
            ]
        ]
        .copy()
    )

    print()
    print(
        f"경제 JOIN 대상 지역 수: "
        f"{len(economy_clean)}"
    )

    return economy_clean


# ============================================================
# 5. 경제 데이터 LEFT JOIN
# ============================================================

def merge_economy(
    base: pd.DataFrame,
    economy: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("5. 경제 데이터 LEFT JOIN")
    print("=" * 70)

    merged = pd.merge(
        base,
        economy,
        on="경제지역키",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    print()
    print(
        "[경제 JOIN 결과]"
    )

    print(
        merged["_merge"]
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"LEFT JOIN 후 전체 지역 수: "
        f"{len(merged)}"
    )

    # --------------------------------------------------------
    # 경제 데이터 미매칭 지역
    # --------------------------------------------------------

    missing = (
        merged[
            merged["_merge"]
            != "both"
        ][
            [
                "지역코드",
                "지역명",
                "시도",
                "경제지역키",
                "고령화율_2025",
                "청년비율_2025",
                "인구증감률_2016_2025",
                "청년순이동률_2016_2025",
            ]
        ]
        .copy()
    )

    print()
    print(
        f"경제 데이터 매칭 성공: "
        f"{(merged['_merge'] == 'both').sum()}개"
    )

    print(
        f"경제 데이터 미매칭: "
        f"{len(missing)}개"
    )

    if not missing.empty:
        print()
        print(
            "[경제 데이터가 없는 지역]"
        )

        print(
            missing.to_string(
                index=False
            )
        )

    merged = (
        merged.drop(
            columns=[
                "_merge"
            ]
        )
    )

    return (
        merged,
        missing,
    )


# ============================================================
# 6. 최종 컬럼 정리
# ============================================================

def create_final_dataset(
    merged: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("6. 최종 A 데이터셋 생성")
    print("=" * 70)

    # --------------------------------------------------------
    # 우리가 실제 분석에서 사용할 컬럼
    # --------------------------------------------------------

    final_columns = [
        "지역코드",
        "지역명",
        "시도",

        "총인구_2016",
        "총인구_2025",

        "고령인구_2025",
        "청년인구_2025",

        "고령화율_2025",
        "청년비율_2025",

        "인구증감률_2016_2025",

        "청년전입_누적_2016_2025",
        "청년전출_누적_2016_2025",
        "청년순이동_누적_2016_2025",
        "청년순이동률_2016_2025",

        "사업체수_2024",
        "종사자수_2024",
    ]

    final = (
        merged[
            final_columns
        ]
        .copy()
    )

    final = (
        final
        .sort_values(
            "지역코드"
        )
        .reset_index(
            drop=True
        )
    )

    return final


# ============================================================
# 7. 결과 저장
# ============================================================

def save_results(
    final: pd.DataFrame,
    missing: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("7. 결과 저장")
    print("=" * 70)

    final.to_csv(
        FINAL_OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    missing.to_csv(
        ECONOMY_MISSING_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"최종 데이터 저장:"
    )

    print(
        FINAL_OUTPUT_FILE
    )

    print()
    print(
        f"경제 미매칭 지역 저장:"
    )

    print(
        ECONOMY_MISSING_FILE
    )


# ============================================================
# 8. 최종 검증
# ============================================================

def validate_final_dataset(
    final: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("8. 최종 데이터 검증")
    print("=" * 70)

    print()
    print(
        f"전체 지역 수: "
        f"{len(final)}"
    )

    print()
    print(
        "[컬럼별 결측치]"
    )

    print(
        final
        .isnull()
        .sum()
        .to_string()
    )

    print()
    print(
        "[경제 데이터 존재 여부]"
    )

    economy_complete = (
        final[
            [
                "사업체수_2024",
                "종사자수_2024",
            ]
        ]
        .notna()
        .all(
            axis=1
        )
        .sum()
    )

    economy_missing = (
        final[
            [
                "사업체수_2024",
                "종사자수_2024",
            ]
        ]
        .isna()
        .any(
            axis=1
        )
        .sum()
    )

    print(
        f"경제 데이터 있음: "
        f"{economy_complete}"
    )

    print(
        f"경제 데이터 없음: "
        f"{economy_missing}"
    )

    print()
    print(
        "[앞 20행]"
    )

    print(
        final
        .head(20)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[핵심 분석 변수]"
    )

    print(
        final[
            [
                "고령화율_2025",
                "청년비율_2025",
                "인구증감률_2016_2025",
                "청년순이동률_2016_2025",
                "사업체수_2024",
                "종사자수_2024",
            ]
        ]
        .describe()
        .round(2)
        .to_string()
    )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("A 담당 데이터 최종 결합")
    print("229개 분석지역 기준 LEFT JOIN")
    print("=" * 70)

    (
        population,
        migration,
        economy,
    ) = load_data()

    population_migration = (
        merge_population_migration(
            population,
            migration,
        )
    )

    base = (
        create_economy_join_key(
            population_migration
        )
    )

    economy_clean = (
        prepare_economy(
            economy
        )
    )

    (
        merged,
        missing,
    ) = merge_economy(
        base,
        economy_clean,
    )

    final = (
        create_final_dataset(
            merged
        )
    )

    save_results(
        final,
        missing,
    )

    validate_final_dataset(
        final
    )

    print()
    print("=" * 70)
    print("A 담당 데이터 결합 완료")
    print("=" * 70)

    print()
    print(
        "생성 파일:"
    )

    print(
        "1. a_dataset_merged.csv"
    )

    print(
        "2. a_dataset_economy_missing.csv"
    )


if __name__ == "__main__":
    main()