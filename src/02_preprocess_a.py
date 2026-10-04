from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MIGRATION_DIR = RAW_DIR / "migration"
BUSINESS_DIR = RAW_DIR / "business"
EMPLOYEE_DIR = RAW_DIR / "employee"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 프로젝트 설정
# ============================================================

START_YEAR = 2016
END_YEAR = 2025

YOUNG_AGE_GROUPS = [
    "20 - 24세",
    "25 - 29세",
    "30 - 34세",
    "35 - 39세",
]


# ============================================================
# 공통 함수
# ============================================================

def read_kosis_csv(file_path: Path) -> pd.DataFrame:
    """
    KOSIS CSV 파일 읽기.

    이번에 받은 KOSIS CSV는 CP949 인코딩이므로
    CP949를 먼저 사용한다.
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
            return pd.read_csv(
                file_path,
                encoding=encoding,
                dtype={
                    "[A]행정구역(시군구)별": str,
                },
                low_memory=False,
            )

        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        f"CSV 파일을 읽을 수 없습니다.\n"
        f"파일: {file_path}\n"
        f"오류: {last_error}"
    )


def clean_number(series: pd.Series) -> pd.Series:
    """
    콤마가 포함된 숫자 등을 실제 숫자로 변환한다.
    """

    return pd.to_numeric(
        series
        .astype(str)
        .str.replace(",", "", regex=False)
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


def normalize_region_name(value) -> str:
    """
    지역명의 연속된 공백을 한 칸으로 통일한다.

    예:
        '대구 남  구'
        -> '대구 남 구'
    """

    if pd.isna(value):
        return ""

    return " ".join(
        str(value).strip().split()
    )


# ============================================================
# 1. 이동 데이터 파일 찾기
# ============================================================

def find_migration_file() -> Path:
    """
    새로 받은 시군구 이동자수 파일을 찾는다.

    우선 migration_2016_2025.csv를 찾고,
    없으면 CSV 구조를 검사하여 자동으로 찾는다.
    """

    preferred_file = (
        MIGRATION_DIR
        / "migration_2016_2025.csv"
    )

    if preferred_file.exists():
        return preferred_file

    csv_files = sorted(
        MIGRATION_DIR.glob("*.csv")
    )

    for file_path in csv_files:

        try:
            df = read_kosis_csv(file_path)

        except Exception:
            continue

        required_columns = {
            "[A]행정구역(시군구)별",
            "행정구역(시군구)별",
            "연령별",
            "항목",
            "2016 년",
            "2025 년",
        }

        if required_columns.issubset(
            set(df.columns)
        ):
            return file_path

    raise FileNotFoundError(
        "새로운 시군구 이동자수 CSV를 "
        "찾을 수 없습니다.\n"
        f"확인 경로: {MIGRATION_DIR}"
    )


# ============================================================
# 2. 이동 데이터 전처리
# ============================================================

def preprocess_migration() -> pd.DataFrame:

    print()
    print("=" * 70)
    print("1. 이동 데이터 전처리")
    print("=" * 70)

    file_path = find_migration_file()

    print()
    print(
        f"[사용 파일] {file_path.name}"
    )

    df = read_kosis_csv(
        file_path
    )

    # --------------------------------------------------------
    # 필요한 컬럼 확인
    # --------------------------------------------------------

    region_code_column = (
        "[A]행정구역(시군구)별"
    )

    region_name_column = (
        "행정구역(시군구)별"
    )

    age_column = "연령별"
    item_column = "항목"

    required_columns = [
        region_code_column,
        region_name_column,
        age_column,
        item_column,
    ]

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):
        required_columns.append(
            f"{year} 년"
        )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "필요한 컬럼이 없습니다.\n"
            f"{missing_columns}"
        )

    # --------------------------------------------------------
    # 필요 컬럼만 사용
    # --------------------------------------------------------

    df = df[
        required_columns
    ].copy()

    # --------------------------------------------------------
    # 지역코드 문자열 처리
    # --------------------------------------------------------

    df["지역코드"] = (
        df[region_code_column]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # 지역명 정리
    # --------------------------------------------------------

    df["지역명"] = (
        df[region_name_column]
        .apply(
            normalize_region_name
        )
    )

    # --------------------------------------------------------
    # 연령 정리
    # --------------------------------------------------------

    df["연령대"] = (
        df[age_column]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # 20~39세만 남김
    # --------------------------------------------------------

    df = df[
        df["연령대"].isin(
            YOUNG_AGE_GROUPS
        )
    ].copy()

    print()
    print("[사용 연령대]")

    for age in sorted(
        df["연령대"].unique()
    ):
        print(
            f" - {age}"
        )

    # --------------------------------------------------------
    # 총전입 / 총전출만 남김
    # --------------------------------------------------------

    print()
    print("[항목 확인]")

    for item in sorted(
        df[item_column]
        .dropna()
        .unique()
    ):
        print(
            f" - {item}"
        )

    df = df[
        df[item_column].isin(
            [
                "총전입[명]",
                "총전출[명]",
            ]
        )
    ].copy()

    # --------------------------------------------------------
    # 연도별 열을 행으로 변환
    #
    # 기존:
    #
    # 지역 | 연령 | 항목 | 2016 | 2017 | ...
    #
    # 변경:
    #
    # 지역 | 연령 | 항목 | 연도 | 값
    # --------------------------------------------------------

    year_columns = [
        f"{year} 년"
        for year in range(
            START_YEAR,
            END_YEAR + 1,
        )
    ]

    migration_long = df.melt(
        id_vars=[
            "지역코드",
            "지역명",
            "연령대",
            item_column,
        ],
        value_vars=year_columns,
        var_name="연도",
        value_name="이동자수",
    )

    # --------------------------------------------------------
    # "2016 년" -> 2016
    # --------------------------------------------------------

    migration_long["연도"] = (
        migration_long["연도"]
        .str.replace(
            " 년",
            "",
            regex=False,
        )
        .astype(int)
    )

    # --------------------------------------------------------
    # 이동자수 숫자 변환
    # --------------------------------------------------------

    migration_long[
        "이동자수"
    ] = clean_number(
        migration_long[
            "이동자수"
        ]
    )

    # --------------------------------------------------------
    # 청년 전입 / 전출 합계
    #
    # 한 지역의:
    #
    # 20~24
    # 25~29
    # 30~34
    # 35~39
    #
    # 합산
    # --------------------------------------------------------

    migration_grouped = (
        migration_long
        .groupby(
            [
                "지역코드",
                "지역명",
                "연도",
                item_column,
            ],
            as_index=False,
        )
        .agg(
            이동자수=(
                "이동자수",
                "sum",
            )
        )
    )

    # --------------------------------------------------------
    # 총전입 / 총전출을 컬럼으로 변경
    # --------------------------------------------------------

    migration_pivot = (
        migration_grouped
        .pivot_table(
            index=[
                "지역코드",
                "지역명",
                "연도",
            ],
            columns=item_column,
            values="이동자수",
            aggfunc="sum",
        )
        .reset_index()
    )

    migration_pivot.columns.name = None

    migration_pivot = (
        migration_pivot.rename(
            columns={
                "총전입[명]":
                    "청년전입",
                "총전출[명]":
                    "청년전출",
            }
        )
    )

    # --------------------------------------------------------
    # 청년 순이동 계산
    # --------------------------------------------------------

    migration_pivot[
        "청년순이동"
    ] = (
        migration_pivot[
            "청년전입"
        ]
        - migration_pivot[
            "청년전출"
        ]
    )

    # --------------------------------------------------------
    # 정렬
    # --------------------------------------------------------

    migration_pivot = (
        migration_pivot
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

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    output_file = (
        PROCESSED_DIR
        / "migration_2016_2025.csv"
    )

    migration_pivot.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"저장 완료: {output_file}"
    )

    print()
    print(
        f"고유 지역코드 수: "
        f"{migration_pivot['지역코드'].nunique()}"
    )

    print(
        f"행 수: "
        f"{len(migration_pivot)}"
    )

    print()
    print("[연도별 지역 수]")

    print(
        migration_pivot
        .groupby("연도")[
            "지역코드"
        ]
        .nunique()
        .to_string()
    )

    print()
    print("[앞 20행]")

    print(
        migration_pivot
        .head(20)
        .to_string(
            index=False
        )
    )

    return migration_pivot


# ============================================================
# 3. 사업체 데이터 전처리
# ============================================================

def preprocess_business() -> pd.DataFrame:

    print()
    print("=" * 70)
    print("2. 사업체 데이터 전처리")
    print("=" * 70)

    files = sorted(
        BUSINESS_DIR.glob(
            "*.xlsx"
        )
    )

    if not files:
        raise FileNotFoundError(
            f"사업체 파일이 없습니다.\n"
            f"{BUSINESS_DIR}"
        )

    results = []

    for file_path in files:

        print(
            f"[읽는 중] "
            f"{file_path.name}"
        )

        df = pd.read_excel(
            file_path,
            sheet_name="사업체수",
            header=1,
        )

        region_column = (
            df.columns[0]
        )

        year_column = None

        for column in df.columns:

            if (
                str(column).strip()
                == "2024"
            ):
                year_column = column
                break

        if year_column is None:
            raise ValueError(
                f"{file_path.name}: "
                "2024년 컬럼이 없습니다."
            )

        temp = df[
            [
                region_column,
                year_column,
            ]
        ].copy()

        temp.columns = [
            "지역명",
            "사업체수_2024",
        ]

        temp["지역명"] = (
            temp["지역명"]
            .apply(
                normalize_region_name
            )
        )

        temp[
            "사업체수_2024"
        ] = clean_number(
            temp[
                "사업체수_2024"
            ]
        )

        # 빈 행 제거
        temp = temp[
            temp["지역명"] != ""
        ].copy()

        # 과거 군위군 행 제거
        temp = temp[
            ~temp["지역명"]
            .str.contains(
                r"\(구\)",
                regex=True,
                na=False,
            )
        ].copy()

        results.append(
            temp
        )

    business = pd.concat(
        results,
        ignore_index=True,
    )

    business = (
        business
        .drop_duplicates(
            subset=["지역명"]
        )
        .sort_values(
            "지역명"
        )
        .reset_index(
            drop=True
        )
    )

    output_file = (
        PROCESSED_DIR
        / "business_2024.csv"
    )

    business.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"파일 수: {len(files)}"
    )

    print(
        f"지역 수: "
        f"{len(business)}"
    )

    print(
        f"저장 완료: "
        f"{output_file}"
    )

    return business


# ============================================================
# 4. 종사자 데이터 전처리
# ============================================================

def preprocess_employee() -> pd.DataFrame:

    print()
    print("=" * 70)
    print("3. 종사자 데이터 전처리")
    print("=" * 70)

    files = sorted(
        EMPLOYEE_DIR.glob(
            "*.xlsx"
        )
    )

    if not files:
        raise FileNotFoundError(
            f"종사자 파일이 없습니다.\n"
            f"{EMPLOYEE_DIR}"
        )

    results = []

    for file_path in files:

        print(
            f"[읽는 중] "
            f"{file_path.name}"
        )

        df = pd.read_excel(
            file_path,
            sheet_name="종사자수",
            header=1,
        )

        region_column = (
            df.columns[0]
        )

        year_column = None

        for column in df.columns:

            if (
                str(column).strip()
                == "2024"
            ):
                year_column = column
                break

        if year_column is None:
            raise ValueError(
                f"{file_path.name}: "
                "2024년 컬럼이 없습니다."
            )

        temp = df[
            [
                region_column,
                year_column,
            ]
        ].copy()

        temp.columns = [
            "지역명",
            "종사자수_2024",
        ]

        temp["지역명"] = (
            temp["지역명"]
            .apply(
                normalize_region_name
            )
        )

        temp[
            "종사자수_2024"
        ] = clean_number(
            temp[
                "종사자수_2024"
            ]
        )

        temp = temp[
            temp["지역명"] != ""
        ].copy()

        # 과거 군위군 행 제거
        temp = temp[
            ~temp["지역명"]
            .str.contains(
                r"\(구\)",
                regex=True,
                na=False,
            )
        ].copy()

        results.append(
            temp
        )

    employee = pd.concat(
        results,
        ignore_index=True,
    )

    employee = (
        employee
        .drop_duplicates(
            subset=["지역명"]
        )
        .sort_values(
            "지역명"
        )
        .reset_index(
            drop=True
        )
    )

    output_file = (
        PROCESSED_DIR
        / "employee_2024.csv"
    )

    employee.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"파일 수: {len(files)}"
    )

    print(
        f"지역 수: "
        f"{len(employee)}"
    )

    print(
        f"저장 완료: "
        f"{output_file}"
    )

    return employee


# ============================================================
# 5. 사업체 + 종사자 결합
# ============================================================

def merge_economy(
    business: pd.DataFrame,
    employee: pd.DataFrame,
) -> pd.DataFrame:

    print()
    print("=" * 70)
    print("4. 경제 데이터 결합")
    print("=" * 70)

    economy = pd.merge(
        business,
        employee,
        on="지역명",
        how="outer",
        indicator=True,
    )

    unmatched = economy[
        economy["_merge"]
        != "both"
    ]

    if not unmatched.empty:

        print()
        print(
            "[사업체/종사자 "
            "불일치 지역]"
        )

        print(
            unmatched[
                [
                    "지역명",
                    "_merge",
                ]
            ]
            .to_string(
                index=False
            )
        )

    economy = (
        economy
        .drop(
            columns=["_merge"]
        )
        .sort_values(
            "지역명"
        )
        .reset_index(
            drop=True
        )
    )

    output_file = (
        PROCESSED_DIR
        / "economy_2024.csv"
    )

    economy.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"지역 수: "
        f"{len(economy)}"
    )

    print(
        f"저장 완료: "
        f"{output_file}"
    )

    return economy


# ============================================================
# 6. 최종 검증
# ============================================================

def validate_data(
    migration: pd.DataFrame,
    economy: pd.DataFrame,
):

    print()
    print("=" * 70)
    print("5. 데이터 검증")
    print("=" * 70)

    print()
    print("[이동 데이터 연도]")

    print(
        sorted(
            migration[
                "연도"
            ].unique()
        )
    )

    print()
    print("[이동 데이터 결측치]")

    print(
        migration
        .isnull()
        .sum()
    )

    print()
    print(
        "[경제 데이터 결측치]"
    )

    print(
        economy
        .isnull()
        .sum()
    )

    print()
    print(
        "[경제 데이터 지역 수]"
    )

    print(
        len(economy)
    )


# ============================================================
# 메인 실행
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("A 담당 데이터 전처리")
    print("=" * 70)

    migration = (
        preprocess_migration()
    )

    business = (
        preprocess_business()
    )

    employee = (
        preprocess_employee()
    )

    economy = merge_economy(
        business,
        employee,
    )

    validate_data(
        migration,
        economy,
    )

    print()
    print("=" * 70)
    print("전처리 완료")
    print("=" * 70)

    print()
    print("생성된 파일:")

    print(
        "1. "
        "migration_2016_2025.csv"
    )

    print(
        "2. business_2024.csv"
    )

    print(
        "3. employee_2024.csv"
    )

    print(
        "4. economy_2024.csv"
    )


if __name__ == "__main__":
    main()