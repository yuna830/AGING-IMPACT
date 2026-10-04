from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CENSUS_DIR = RAW_DIR / "census_2024"

JEONNAM_FILE = (
    CENSUS_DIR / "전라남도.xlsx"
)

SEJONG_FILE = (
    CENSUS_DIR / "세종특별자치시.xlsx"
)

ECONOMY_FILE = (
    PROCESSED_DIR
    / "economy_2024_patched.csv"
)

FINAL_A_FILE = (
    PROCESSED_DIR / "a_dataset_merged.csv"
)


# ============================================================
# 출력 파일
# ============================================================

PATCH_FILE = (
    PROCESSED_DIR
    / "economy_2024_patch_census.csv"
)

ECONOMY_PATCHED_FILE = (
    PROCESSED_DIR
    / "economy_2024_patched.csv"
)


# ============================================================
# 지역명 정리
# ============================================================

def normalize_region_name(
    value,
) -> str:
    """
    지역명의 공백을 정리한다.
    """

    if pd.isna(value):
        return ""

    return " ".join(
        str(value)
        .strip()
        .split()
    )


# ============================================================
# 숫자 정리
# ============================================================

def clean_number(
    series: pd.Series,
) -> pd.Series:
    """
    숫자형 컬럼 정리.
    """

    return pd.to_numeric(
        series,
        errors="coerce",
    )


# ============================================================
# 1. 전국사업체조사 파일 읽기
# ============================================================

def read_census_excel(
    file_path: Path,
) -> pd.DataFrame:
    """
    전국사업체조사 Excel 구조:

    0~2행 : 설명/다중헤더
    3행   : 실제 컬럼명
    4행~  : 데이터

    따라서 header=3 사용.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            "파일이 없습니다.\n"
            f"{file_path}"
        )

    df = pd.read_excel(
        file_path,
        sheet_name=0,
        header=3,
    )

    required_columns = [
        "AD_CD_INDST_IDV_CD",
        "CPNM1",
        "INDST_NM",
        "C1",
        "C2",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_path.name}에 "
            f"필요한 컬럼이 없습니다.\n"
            f"{missing_columns}"
        )

    return df


# ============================================================
# 2. 전산업 행 추출
# ============================================================

def extract_total_industry(
    file_path: Path,
    sido_name: str,
) -> pd.DataFrame:
    """
    산업분류명칭이 '전산업'인 행만 추출한다.

    C1 = 총사업체수
    C2 = 총종사자수
    """

    print()
    print(
        f"[읽는 중] {file_path.name}"
    )

    df = read_census_excel(
        file_path
    )

    df["CPNM1"] = (
        df["CPNM1"]
        .apply(
            normalize_region_name
        )
    )

    df["INDST_NM"] = (
        df["INDST_NM"]
        .astype(str)
        .str.strip()
    )

    total = (
        df[
            df["INDST_NM"]
            == "전산업"
        ][
            [
                "AD_CD_INDST_IDV_CD",
                "CPNM1",
                "C1",
                "C2",
            ]
        ]
        .copy()
    )

    total.columns = [
        "원자료코드",
        "시군구명",
        "사업체수_2024",
        "종사자수_2024",
    ]

    total[
        "사업체수_2024"
    ] = clean_number(
        total[
            "사업체수_2024"
        ]
    )

    total[
        "종사자수_2024"
    ] = clean_number(
        total[
            "종사자수_2024"
        ]
    )

    # --------------------------------------------------------
    # 시도 전체 합계 행 제거
    #
    # 예:
    # 전라남도
    # 세종특별자치시
    #
    # 단, 세종은 자체가 최종 분석 지역이므로
    # 따로 유지해야 한다.
    # --------------------------------------------------------

    if sido_name == "전남":

        total = total[
            total["시군구명"]
            != "전라남도"
        ].copy()

        total["지역명"] = (
            "전남 "
            + total["시군구명"]
        )

    elif sido_name == "세종":

        total = total[
            total["시군구명"]
            == "세종특별자치시"
        ].copy()

        total["지역명"] = (
            "세종 세종특별자치시"
        )

    else:
        raise ValueError(
            f"지원하지 않는 시도입니다: "
            f"{sido_name}"
        )

    result = total[
        [
            "지역명",
            "사업체수_2024",
            "종사자수_2024",
        ]
    ].copy()

    result["지역명"] = (
        result["지역명"]
        .apply(
            normalize_region_name
        )
    )

    return result


# ============================================================
# 3. 보완 데이터 생성
# ============================================================

def create_patch_data() -> pd.DataFrame:
    print()
    print("=" * 70)
    print("1. 전국사업체조사 보완 데이터 생성")
    print("=" * 70)

    jeonnam = extract_total_industry(
        JEONNAM_FILE,
        "전남",
    )

    sejong = extract_total_industry(
        SEJONG_FILE,
        "세종",
    )

    patch = pd.concat(
        [
            jeonnam,
            sejong,
        ],
        ignore_index=True,
    )

    patch = (
        patch
        .drop_duplicates(
            subset=[
                "지역명"
            ],
            keep="last",
        )
        .sort_values(
            "지역명"
        )
        .reset_index(
            drop=True
        )
    )

    print()
    print(
        f"보완 데이터 지역 수: "
        f"{len(patch)}"
    )

    print()
    print(
        patch.to_string(
            index=False
        )
    )

    patch.to_csv(
        PATCH_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"보완 데이터 저장: "
        f"{PATCH_FILE}"
    )

    return patch


# ============================================================
# 4. 기존 경제 데이터에 보완
# ============================================================

def patch_economy(
    patch: pd.DataFrame,
) -> pd.DataFrame:
    print()
    print("=" * 70)
    print("2. 기존 경제 데이터 보완")
    print("=" * 70)

    if not ECONOMY_FILE.exists():
        raise FileNotFoundError(
            "economy_2024.csv가 없습니다.\n"
            f"{ECONOMY_FILE}"
        )

    economy = pd.read_csv(
        ECONOMY_FILE,
        encoding="utf-8-sig",
    )

    economy["지역명"] = (
        economy["지역명"]
        .apply(
            normalize_region_name
        )
    )

    print()
    print(
        f"기존 경제 데이터 지역 수: "
        f"{len(economy)}"
    )

    # --------------------------------------------------------
    # 기존 데이터와 patch 결합
    #
    # patch 값이 있으면 전국사업체조사 값을 우선 사용.
    #
    # 이렇게 하면 전남 5개 시도 동일한 원자료 기준으로
    # 덮어쓸 수 있다.
    # --------------------------------------------------------

    merged = pd.merge(
        economy,
        patch,
        on="지역명",
        how="outer",
        suffixes=(
            "_기존",
            "_census",
        ),
    )

    merged[
        "사업체수_2024"
    ] = (
        merged[
            "사업체수_2024_census"
        ]
        .combine_first(
            merged[
                "사업체수_2024_기존"
            ]
        )
    )

    merged[
        "종사자수_2024"
    ] = (
        merged[
            "종사자수_2024_census"
        ]
        .combine_first(
            merged[
                "종사자수_2024_기존"
            ]
        )
    )

    patched = merged[
        [
            "지역명",
            "사업체수_2024",
            "종사자수_2024",
        ]
    ].copy()

    patched = (
        patched
        .sort_values(
            "지역명"
        )
        .reset_index(
            drop=True
        )
    )

    print()
    print(
        f"보완 후 경제 데이터 지역 수: "
        f"{len(patched)}"
    )

    print()
    print(
        "[보완 후 결측치]"
    )

    print(
        patched
        .isnull()
        .sum()
        .to_string()
    )

    patched.to_csv(
        ECONOMY_PATCHED_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"저장 완료: "
        f"{ECONOMY_PATCHED_FILE}"
    )

    return patched


# ============================================================
# 5. A 데이터 기준 실제 매칭 확인
# ============================================================

def validate_against_a_dataset(
    patched: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("3. A 데이터 기준 매칭 확인")
    print("=" * 70)

    if not FINAL_A_FILE.exists():
        print()
        print(
            "a_dataset_merged.csv가 아직 없어 "
            "매칭 검증을 건너뜁니다."
        )
        return

    a_dataset = pd.read_csv(
        FINAL_A_FILE,
        encoding="utf-8-sig",
        dtype={
            "지역코드": str,
        },
    )

    # --------------------------------------------------------
    # A 데이터의 JOIN 키 생성
    # --------------------------------------------------------

    a_dataset[
        "경제지역키"
    ] = (
        a_dataset["시도"]
        .astype(str)
        .str.strip()
        +
        " "
        +
        a_dataset["지역명"]
        .astype(str)
        .str.strip()
    )

    a_dataset[
        "경제지역키"
    ] = (
        a_dataset[
            "경제지역키"
        ]
        .apply(
            normalize_region_name
        )
    )

    check = pd.merge(
        a_dataset[
            [
                "지역코드",
                "지역명",
                "경제지역키",
            ]
        ],
        patched.rename(
            columns={
                "지역명":
                    "경제지역키"
            }
        ),
        on="경제지역키",
        how="left",
    )

    missing = check[
        check[
            [
                "사업체수_2024",
                "종사자수_2024",
            ]
        ]
        .isna()
        .any(
            axis=1
        )
    ]

    print()
    print(
        f"A 데이터 지역 수: "
        f"{len(check)}"
    )

    print(
        f"경제 데이터 매칭 성공: "
        f"{len(check) - len(missing)}"
    )

    print(
        f"경제 데이터 미매칭: "
        f"{len(missing)}"
    )

    if not missing.empty:
        print()
        print(
            "[아직 경제 데이터가 없는 지역]"
        )

        print(
            missing[
                [
                    "지역코드",
                    "지역명",
                    "경제지역키",
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
    print("전국사업체조사 기반 경제 데이터 보완")
    print("=" * 70)

    patch = (
        create_patch_data()
    )

    patched = (
        patch_economy(
            patch
        )
    )

    validate_against_a_dataset(
        patched
    )

    print()
    print("=" * 70)
    print("경제 데이터 보완 완료")
    print("=" * 70)

    print()
    print(
        "생성 파일:"
    )

    print(
        "1. economy_2024_patch_census.csv"
    )

    print(
        "2. economy_2024_patched.csv"
    )


if __name__ == "__main__":
    main()