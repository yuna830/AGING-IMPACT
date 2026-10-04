from pathlib import Path
import re

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

POPULATION_DIR = RAW_DIR / "population"

MIGRATION_FILE = (
    PROCESSED_DIR
    / "migration_2016_2025.csv"
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 프로젝트 설정
# ============================================================

START_YEAR = 2016
END_YEAR = 2025

YOUTH_MIN_AGE = 20
YOUTH_MAX_AGE = 39

ELDERLY_MIN_AGE = 65


# ============================================================
# 과거 행정구역 코드 -> 2025 기준 코드
# ============================================================
#
# 인구 변화 분석에서 동일 지역이
# 행정구역 명칭/소속 변경 때문에 다른 지역으로
# 취급되는 것을 막기 위한 매핑이다.
#
# 28170 남구
# -> 28177 미추홀구
#
# 47720 경북 군위군
# -> 27720 대구 군위군
#
# 이후 추가 변경지역이 발견되면
# 여기에 추가한다.
# ============================================================

REGION_CODE_MAP = {
    "28170": "28177",
    "47720": "27720",
}

REGION_NAME_MAP = {
    "28177": "미추홀구",
    "27720": "군위군",
}


# ============================================================
# 공통 함수
# ============================================================

def read_csv_auto(
    file_path: Path,
) -> pd.DataFrame:
    """
    CSV 파일의 인코딩을 순서대로 시도하여 읽는다.
    """

    encodings = [
        "cp949",
        "euc-kr",
        "utf-8-sig",
        "utf-8",
    ]

    last_error = None

    for encoding in encodings:

        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                dtype=str,
                low_memory=False,
            )

            print(
                f"[읽기 성공] "
                f"{file_path.name} "
                f"({encoding})"
            )

            return df

        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        f"CSV 파일을 읽을 수 없습니다.\n"
        f"파일: {file_path}\n"
        f"오류: {last_error}"
    )


def clean_number(
    series: pd.Series,
) -> pd.Series:
    """
    문자열 숫자를 숫자형으로 변환한다.
    """

    return pd.to_numeric(
        series
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False,
        )
        .str.strip()
        .replace(
            {
                "-": None,
                "": None,
                "nan": None,
                "None": None,
            }
        ),
        errors="coerce",
    )


def normalize_region_name(
    value,
) -> str:
    """
    지역명 공백 및 일부 표기를 정리한다.
    """

    if pd.isna(value):
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = value.replace(
        "(통합)",
        "",
    )

    return value.strip()


def extract_age(
    age_text,
):
    """
    '20세' -> 20

    '계', '100세 이상' 등은
    일반 숫자 연령에서 제외한다.
    """

    if pd.isna(age_text):
        return None

    text = str(age_text).strip()

    match = re.fullmatch(
        r"(\d+)세",
        text,
    )

    if match:
        return int(
            match.group(1)
        )

    return None


# ============================================================
# 컬럼 찾기
# ============================================================

def find_column(
    df: pd.DataFrame,
    candidates: list[str],
):
    """
    여러 후보 이름 중 실제 존재하는 컬럼을 찾는다.
    """

    for candidate in candidates:

        if candidate in df.columns:
            return candidate

    return None


# ============================================================
# 1. 인구 원자료 읽기
# ============================================================

def load_population_raw():
    print()
    print("=" * 70)
    print("1. 인구 원본 데이터 읽기")
    print("=" * 70)

    files = sorted(
        POPULATION_DIR.glob(
            "*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "population 폴더에 CSV 파일이 없습니다.\n"
            f"{POPULATION_DIR}"
        )

    print()
    print(
        f"인구 CSV 파일 수: {len(files)}"
    )

    dataframes = []

    for file_path in files:

        print()
        print(
            f"[파일] {file_path.name}"
        )

        df = read_csv_auto(
            file_path
        )

        dataframes.append(
            df
        )

    return dataframes


# ============================================================
# 2. Wide -> Long
# ============================================================

def reshape_population(
    dataframes,
):
    print()
    print("=" * 70)
    print("2. 인구 데이터 구조 변환")
    print("=" * 70)

    results = []

    for df in dataframes:

        region_code_column = find_column(
            df,
            [
                "[A]행정구역(시군구)별",
                "행정구역코드",
                "지역코드",
            ],
        )

        region_name_column = find_column(
            df,
            [
                "행정구역(시군구)별",
                "지역명",
            ],
        )

        age_column = find_column(
            df,
            [
                "연령별",
                "연령",
            ],
        )

        item_column = find_column(
            df,
            [
                "항목",
            ],
        )

        if region_code_column is None:
            raise ValueError(
                "지역코드 컬럼을 찾을 수 없습니다."
            )

        if region_name_column is None:
            raise ValueError(
                "지역명 컬럼을 찾을 수 없습니다."
            )

        if age_column is None:
            raise ValueError(
                "연령 컬럼을 찾을 수 없습니다."
            )

        # ----------------------------------------------------
        # 총인구만 사용
        # ----------------------------------------------------

        if item_column is not None:

            item_values = (
                df[item_column]
                .astype(str)
                .str.strip()
            )

            total_mask = (
                item_values
                .str.contains(
                    "총인구",
                    na=False,
                )
            )

            df = df[
                total_mask
            ].copy()

        else:
            df = df.copy()

        # ----------------------------------------------------
        # 기본 컬럼 생성
        # ----------------------------------------------------

        df["지역코드"] = (
            df[region_code_column]
            .astype(str)
            .str.strip()
            .str.replace(
                ".0",
                "",
                regex=False,
            )
        )

        df["지역명"] = (
            df[region_name_column]
            .apply(
                normalize_region_name
            )
        )

        df["연령"] = (
            df[age_column]
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # 연도 컬럼 탐색
        # ----------------------------------------------------

        year_columns = []

        for column in df.columns:

            text = (
                str(column)
                .strip()
            )

            match = re.fullmatch(
                r"(\d{4})\s*년?",
                text,
            )

            if match is None:
                continue

            year = int(
                match.group(1)
            )

            if (
                START_YEAR
                <= year
                <= END_YEAR
            ):
                year_columns.append(
                    column
                )

        if not year_columns:
            continue

        temp = df.melt(
            id_vars=[
                "지역코드",
                "지역명",
                "연령",
            ],
            value_vars=year_columns,
            var_name="연도",
            value_name="인구수",
        )

        temp["연도"] = (
            temp["연도"]
            .astype(str)
            .str.extract(
                r"(\d{4})"
            )[0]
            .astype(int)
        )

        temp["인구수"] = (
            clean_number(
                temp["인구수"]
            )
        )

        results.append(
            temp
        )

    if not results:
        raise ValueError(
            "2016~2025 인구 데이터를 찾지 못했습니다."
        )

    population_long = pd.concat(
        results,
        ignore_index=True,
    )

    print()
    print(
        "행정구역 통합 전 "
        f"고유 지역코드 수: "
        f"{population_long['지역코드'].nunique()}"
    )

    return population_long


# ============================================================
# 3. 행정구역 코드 통일
# ============================================================

def harmonize_region_codes(
    population_long: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("3. 행정구역 코드 통일")
    print("=" * 70)

    df = population_long.copy()

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
    # 현재 코드 기준 지역명 통일
    # --------------------------------------------------------

    for code, name in (
        REGION_NAME_MAP.items()
    ):

        df.loc[
            df["지역코드"] == code,
            "지역명",
        ] = name

    # --------------------------------------------------------
    # 코드 변경으로 같은 지역/연도/연령 행이
    # 두 개 생길 수 있으므로 하나로 통합한다.
    #
    # 동일 지역을 합산하면 중복 계산 위험이 있으므로
    # 값이 존재하는 쪽을 선택하는 방식으로 max 사용.
    # --------------------------------------------------------

    df = (
        df
        .groupby(
            [
                "지역코드",
                "지역명",
                "연령",
                "연도",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            인구수=(
                "인구수",
                "max",
            )
        )
    )

    print()
    print(
        "행정구역 통합 후 "
        f"고유 지역코드 수: "
        f"{df['지역코드'].nunique()}"
    )

    print()
    print("[통합 대상 확인]")

    target = df[
        df["지역코드"].isin(
            [
                "28177",
                "27720",
            ]
        )
    ]

    print(
        target[
            [
                "지역코드",
                "지역명",
                "연도",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "지역코드",
                "연도",
            ]
        )
        .to_string(
            index=False
        )
    )

    return df


# ============================================================
# 4. 현재 분석 대상 지역 선택
# ============================================================

def filter_analysis_regions(
    population_long: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("4. 분석 대상 지역 정리")
    print("=" * 70)

    if not MIGRATION_FILE.exists():
        raise FileNotFoundError(
            "migration_2016_2025.csv가 없습니다."
        )

    migration = pd.read_csv(
        MIGRATION_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    migration[
        "지역코드"
    ] = (
        migration[
            "지역코드"
        ]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # 이동 데이터도 코드 변경을 적용한다.
    # --------------------------------------------------------

    migration[
        "지역코드"
    ] = (
        migration[
            "지역코드"
        ]
        .replace(
            REGION_CODE_MAP
        )
    )

    # --------------------------------------------------------
    # 2025년에 실제 이동이 존재하는 지역만 사용
    # --------------------------------------------------------

    migration_2025 = (
        migration[
            migration["연도"]
            == END_YEAR
        ]
        .copy()
    )

    migration_2025[
        "이동합계"
    ] = (
        migration_2025[
            "청년전입"
        ]
        .fillna(0)
        +
        migration_2025[
            "청년전출"
        ]
        .fillna(0)
    )

    active_codes = set(
        migration_2025.loc[
            migration_2025[
                "이동합계"
            ] > 0,
            "지역코드",
        ]
    )

    before_count = (
        population_long[
            "지역코드"
        ]
        .nunique()
    )

    population_filtered = (
        population_long[
            population_long[
                "지역코드"
            ]
            .isin(
                active_codes
            )
        ]
        .copy()
    )

    after_count = (
        population_filtered[
            "지역코드"
        ]
        .nunique()
    )

    print()
    print(
        f"인구 원본 지역 수: "
        f"{before_count}"
    )

    print(
        f"현재 분석 대상 지역 수: "
        f"{after_count}"
    )

    return population_filtered


# ============================================================
# 5. 인구 지표 계산
# ============================================================

def calculate_population_metrics(
    population_long: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("5. 인구 지표 계산")
    print("=" * 70)

    # --------------------------------------------------------
    # 총인구
    # --------------------------------------------------------

    total_population = (
        population_long[
            population_long[
                "연령"
            ]
            == "계"
        ][
            [
                "지역코드",
                "지역명",
                "연도",
                "인구수",
            ]
        ]
        .rename(
            columns={
                "인구수":
                    "총인구"
            }
        )
        .copy()
    )

    # --------------------------------------------------------
    # 숫자 연령
    # --------------------------------------------------------

    age_data = (
        population_long[
            population_long[
                "연령"
            ]
            != "계"
        ]
        .copy()
    )

    age_data[
        "나이"
    ] = (
        age_data[
            "연령"
        ]
        .apply(
            extract_age
        )
    )

    # --------------------------------------------------------
    # 청년 20~39세
    # --------------------------------------------------------

    youth_population = (
        age_data[
            age_data[
                "나이"
            ]
            .between(
                YOUTH_MIN_AGE,
                YOUTH_MAX_AGE,
                inclusive="both",
            )
        ]
        .groupby(
            [
                "지역코드",
                "지역명",
                "연도",
            ],
            as_index=False,
        )
        .agg(
            청년인구=(
                "인구수",
                "sum",
            )
        )
    )

    # --------------------------------------------------------
    # 고령 65~99세
    # --------------------------------------------------------

    elderly_population = (
        age_data[
            age_data[
                "나이"
            ]
            .ge(
                ELDERLY_MIN_AGE
            )
        ]
        .groupby(
            [
                "지역코드",
                "지역명",
                "연도",
            ],
            as_index=False,
        )
        .agg(
            고령인구=(
                "인구수",
                "sum",
            )
        )
    )

    # --------------------------------------------------------
    # 100세 이상
    # --------------------------------------------------------

    elderly_100_plus = (
        population_long[
            population_long[
                "연령"
            ]
            .str.contains(
                "100세",
                na=False,
            )
        ]
        .groupby(
            [
                "지역코드",
                "지역명",
                "연도",
            ],
            as_index=False,
        )
        .agg(
            고령인구_100세이상=(
                "인구수",
                "sum",
            )
        )
    )

    elderly_population = pd.merge(
        elderly_population,
        elderly_100_plus,
        on=[
            "지역코드",
            "지역명",
            "연도",
        ],
        how="outer",
    )

    elderly_population[
        "고령인구"
    ] = (
        elderly_population[
            "고령인구"
        ]
        .fillna(0)
        +
        elderly_population[
            "고령인구_100세이상"
        ]
        .fillna(0)
    )

    elderly_population = (
        elderly_population[
            [
                "지역코드",
                "지역명",
                "연도",
                "고령인구",
            ]
        ]
    )

    # --------------------------------------------------------
    # 결합
    # --------------------------------------------------------

    population_metrics = pd.merge(
        total_population,
        youth_population,
        on=[
            "지역코드",
            "지역명",
            "연도",
        ],
        how="left",
    )

    population_metrics = pd.merge(
        population_metrics,
        elderly_population,
        on=[
            "지역코드",
            "지역명",
            "연도",
        ],
        how="left",
    )

    # --------------------------------------------------------
    # 비율
    # --------------------------------------------------------

    population_metrics[
        "고령화율"
    ] = (
        population_metrics[
            "고령인구"
        ]
        /
        population_metrics[
            "총인구"
        ]
        * 100
    )

    population_metrics[
        "청년비율"
    ] = (
        population_metrics[
            "청년인구"
        ]
        /
        population_metrics[
            "총인구"
        ]
        * 100
    )

    population_metrics[
        "고령화율"
    ] = (
        population_metrics[
            "고령화율"
        ]
        .round(2)
    )

    population_metrics[
        "청년비율"
    ] = (
        population_metrics[
            "청년비율"
        ]
        .round(2)
    )

    population_metrics = (
        population_metrics
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

    return population_metrics


# ============================================================
# 6. 2016 -> 2025 인구증감률
# ============================================================

def calculate_population_change(
    population_metrics: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("6. 인구증감률 계산")
    print("=" * 70)

    population_2016 = (
        population_metrics[
            population_metrics[
                "연도"
            ]
            == START_YEAR
        ][
            [
                "지역코드",
                "지역명",
                "총인구",
            ]
        ]
        .rename(
            columns={
                "총인구":
                    "총인구_2016"
            }
        )
    )

    population_2025 = (
        population_metrics[
            population_metrics[
                "연도"
            ]
            == END_YEAR
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
        .rename(
            columns={
                "총인구":
                    "총인구_2025",

                "청년인구":
                    "청년인구_2025",

                "고령인구":
                    "고령인구_2025",

                "고령화율":
                    "고령화율_2025",

                "청년비율":
                    "청년비율_2025",
            }
        )
    )

    summary = pd.merge(
        population_2016,
        population_2025,
        on=[
            "지역코드",
            "지역명",
        ],
        how="inner",
    )

    summary[
        "인구증감률_2016_2025"
    ] = (
        (
            summary[
                "총인구_2025"
            ]
            -
            summary[
                "총인구_2016"
            ]
        )
        /
        summary[
            "총인구_2016"
        ]
        * 100
    ).round(2)

    summary = summary[
        [
            "지역코드",
            "지역명",
            "총인구_2016",
            "총인구_2025",
            "청년인구_2025",
            "고령인구_2025",
            "고령화율_2025",
            "청년비율_2025",
            "인구증감률_2016_2025",
        ]
    ]

    summary = (
        summary
        .sort_values(
            "지역코드"
        )
        .reset_index(
            drop=True
        )
    )

    return summary


# ============================================================
# 7. 저장
# ============================================================

def save_results(
    population_metrics,
    population_summary,
):
    print()
    print("=" * 70)
    print("7. 결과 저장")
    print("=" * 70)

    population_file = (
        PROCESSED_DIR
        / "population_2016_2025.csv"
    )

    summary_file = (
        PROCESSED_DIR
        / "population_summary_2025.csv"
    )

    population_metrics.to_csv(
        population_file,
        index=False,
        encoding="utf-8-sig",
    )

    population_summary.to_csv(
        summary_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"저장 완료: {population_file}"
    )

    print(
        f"저장 완료: {summary_file}"
    )


# ============================================================
# 8. 최종 검증
# ============================================================

def validate_results(
    population_metrics,
    population_summary,
):
    print()
    print("=" * 70)
    print("8. 결과 검증")
    print("=" * 70)

    print()
    print("[연도별 지역 수]")

    print(
        population_metrics
        .groupby(
            "연도"
        )[
            "지역코드"
        ]
        .nunique()
        .to_string()
    )

    print()
    print("[결측치]")

    print(
        population_metrics
        .isnull()
        .sum()
    )

    print()
    print(
        f"[최종 요약 지역 수] "
        f"{len(population_summary)}"
    )

    print()
    print(
        "[미추홀구 확인]"
    )

    print(
        population_metrics[
            population_metrics[
                "지역코드"
            ]
            == "28177"
        ][
            [
                "지역코드",
                "지역명",
                "연도",
                "총인구",
            ]
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
        population_metrics[
            population_metrics[
                "지역코드"
            ]
            == "27720"
        ][
            [
                "지역코드",
                "지역명",
                "연도",
                "총인구",
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[요약 결측치]"
    )

    print(
        population_summary
        .isnull()
        .sum()
    )


# ============================================================
# 메인
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("인구 데이터 전처리")
    print("행정구역 변경 반영")
    print("=" * 70)

    raw_dataframes = (
        load_population_raw()
    )

    population_long = (
        reshape_population(
            raw_dataframes
        )
    )

    population_long = (
        harmonize_region_codes(
            population_long
        )
    )

    population_filtered = (
        filter_analysis_regions(
            population_long
        )
    )

    population_metrics = (
        calculate_population_metrics(
            population_filtered
        )
    )

    population_summary = (
        calculate_population_change(
            population_metrics
        )
    )

    save_results(
        population_metrics,
        population_summary,
    )

    validate_results(
        population_metrics,
        population_summary,
    )

    print()
    print("=" * 70)
    print("인구 데이터 전처리 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()