from pathlib import Path

import pandas as pd


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"

A_PATH = PROCESSED_DIR / "a_dataset_features.csv"

B_PATH = (
    BASE_DIR
    / "results"
    / "b_infrastructure"
    / "b_infrastructure.csv"
)

OUTPUT_DIR = BASE_DIR / "results" / "ab_merge"
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_PATH = OUTPUT_DIR / "ab_dataset.csv"


# ============================================================
# 시도명 통일
# ============================================================

SIDO_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}


def normalize_region_name(
    sido_name: str,
    region_name: str,
) -> str:
    """
    A/B 데이터의 시군구명을 결합 가능한 형태로 통일한다.

    특히 세종은
    A: 세종특별자치시
    B: 세종시
    형태이므로 세종시로 통일한다.
    """

    sido_name = str(sido_name).strip()
    region_name = str(region_name).strip()

    if sido_name == "세종특별자치시":
        return "세종시"

    return region_name


def create_merge_key(
    sido_name: str,
    region_name: str,
) -> str:
    """
    시도명 + 시군구명을 이용한 결합용 키 생성
    """

    return f"{sido_name}|{region_name}"


# ============================================================
# 1. 데이터 불러오기
# ============================================================

print("\n========================================")
print("1. A / B 데이터 불러오기")
print("========================================")

a = pd.read_csv(
    A_PATH,
    encoding="utf-8-sig",
)

b = pd.read_csv(
    B_PATH,
    encoding="utf-8-sig",
)

print(f"A 데이터 지역 수: {len(a):,}")
print(f"B 데이터 지역 수: {len(b):,}")

print(f"A 컬럼 수: {len(a.columns)}")
print(f"B 컬럼 수: {len(b.columns)}")


# ============================================================
# 2. 필수 컬럼 확인
# ============================================================

print("\n========================================")
print("2. 필수 컬럼 확인")
print("========================================")

required_a_cols = [
    "지역코드",
    "지역명",
    "시도",
    "고령인구_2025",
]

required_b_cols = [
    "시도명",
    "시군구명",
    "65세이상인구",
    "병원수",
    "약국수",
    "노인복지시설수",
    "버스정류장수",
    "철도역수",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

missing_a_cols = [
    col
    for col in required_a_cols
    if col not in a.columns
]

missing_b_cols = [
    col
    for col in required_b_cols
    if col not in b.columns
]

if missing_a_cols:
    raise ValueError(
        "A 데이터에 필요한 컬럼이 없습니다: "
        + ", ".join(missing_a_cols)
    )

if missing_b_cols:
    raise ValueError(
        "B 데이터에 필요한 컬럼이 없습니다: "
        + ", ".join(missing_b_cols)
    )

print("A 필수 컬럼 확인 완료")
print("B 필수 컬럼 확인 완료")


# ============================================================
# 3. A 데이터의 시도명 표준화
# ============================================================

print("\n========================================")
print("3. 지역명 표준화")
print("========================================")

a["시도_표준"] = (
    a["시도"]
    .astype(str)
    .str.strip()
    .map(SIDO_MAP)
)

unknown_sido = (
    a.loc[
        a["시도_표준"].isna(),
        "시도",
    ]
    .drop_duplicates()
    .tolist()
)

if unknown_sido:
    raise ValueError(
        "시도 매핑에 없는 값이 있습니다: "
        + ", ".join(
            map(
                str,
                unknown_sido,
            )
        )
    )

a["지역명_표준"] = a.apply(
    lambda row: normalize_region_name(
        row["시도_표준"],
        row["지역명"],
    ),
    axis=1,
)


# ============================================================
# 4. B 데이터 지역명 표준화
# ============================================================

b["시도_표준"] = (
    b["시도명"]
    .astype(str)
    .str.strip()
)

b["지역명_표준"] = b.apply(
    lambda row: normalize_region_name(
        row["시도_표준"],
        row["시군구명"],
    ),
    axis=1,
)


# ============================================================
# 5. 결합 키 생성
# ============================================================

a["merge_key"] = a.apply(
    lambda row: create_merge_key(
        row["시도_표준"],
        row["지역명_표준"],
    ),
    axis=1,
)

b["merge_key"] = b.apply(
    lambda row: create_merge_key(
        row["시도_표준"],
        row["지역명_표준"],
    ),
    axis=1,
)

print("\nA 지역 예시:")
print(
    a[
        [
            "시도",
            "지역명",
            "시도_표준",
            "지역명_표준",
            "merge_key",
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nB 지역 예시:")
print(
    b[
        [
            "시도명",
            "시군구명",
            "시도_표준",
            "지역명_표준",
            "merge_key",
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ============================================================
# 6. 중복 지역 검사
# ============================================================

print("\n========================================")
print("4. 지역 중복 검사")
print("========================================")

a_duplicates = a[
    a["merge_key"].duplicated(
        keep=False,
    )
].copy()

b_duplicates = b[
    b["merge_key"].duplicated(
        keep=False,
    )
].copy()

if not a_duplicates.empty:
    duplicate_path = (
        OUTPUT_DIR
        / "a_duplicate_regions.csv"
    )

    a_duplicates.to_csv(
        duplicate_path,
        index=False,
        encoding="utf-8-sig",
    )

    raise ValueError(
        "A 데이터에 중복 지역이 있습니다. "
        f"{duplicate_path} 확인 필요"
    )

if not b_duplicates.empty:
    duplicate_path = (
        OUTPUT_DIR
        / "b_duplicate_regions.csv"
    )

    b_duplicates.to_csv(
        duplicate_path,
        index=False,
        encoding="utf-8-sig",
    )

    raise ValueError(
        "B 데이터에 중복 지역이 있습니다. "
        f"{duplicate_path} 확인 필요"
    )

print("A 중복 지역: 0")
print("B 중복 지역: 0")


# ============================================================
# 7. A / B 지역 매칭 여부 확인
# ============================================================

print("\n========================================")
print("5. A / B 지역 매칭 검사")
print("========================================")

a_keys = set(
    a["merge_key"]
)

b_keys = set(
    b["merge_key"]
)

only_a_keys = (
    a_keys
    - b_keys
)

only_b_keys = (
    b_keys
    - a_keys
)

only_a = a[
    a["merge_key"].isin(
        only_a_keys
    )
].copy()

only_b = b[
    b["merge_key"].isin(
        only_b_keys
    )
].copy()

print(
    f"A에만 존재하는 지역: "
    f"{len(only_a):,}"
)

print(
    f"B에만 존재하는 지역: "
    f"{len(only_b):,}"
)

if not only_a.empty:
    only_a_path = (
        OUTPUT_DIR
        / "only_a_regions.csv"
    )

    only_a[
        [
            "지역코드",
            "시도",
            "지역명",
            "시도_표준",
            "지역명_표준",
            "merge_key",
        ]
    ].to_csv(
        only_a_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n[A에만 존재하는 지역]"
    )

    print(
        only_a[
            [
                "시도",
                "지역명",
                "merge_key",
            ]
        ].to_string(
            index=False,
        )
    )


if not only_b.empty:
    only_b_path = (
        OUTPUT_DIR
        / "only_b_regions.csv"
    )

    only_b[
        [
            "시도명",
            "시군구명",
            "시도_표준",
            "지역명_표준",
            "merge_key",
        ]
    ].to_csv(
        only_b_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n[B에만 존재하는 지역]"
    )

    print(
        only_b[
            [
                "시도명",
                "시군구명",
                "merge_key",
            ]
        ].to_string(
            index=False,
        )
    )


if (
    not only_a.empty
    or not only_b.empty
):
    raise ValueError(
        "\nA/B 지역이 완전히 일치하지 않습니다.\n"
        "results/ab_merge 폴더의 "
        "only_a_regions.csv 또는 "
        "only_b_regions.csv를 확인하세요."
    )

print(
    "A/B 전체 지역 매칭 완료"
)


# ============================================================
# 8. B 데이터에서 결합할 컬럼 정리
# ============================================================

b_merge_cols = [
    "merge_key",
    "65세이상인구",
    "병원수",
    "약국수",
    "주거복지시설수",
    "의료복지시설수",
    "여가복지시설수",
    "재가복지시설수",
    "노인일자리지원기관수",
    "학대피해노인쉼터수",
    "노인복지시설수",
    "버스정류장수",
    "철도역수",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

b_for_merge = b[
    b_merge_cols
].copy()

b_for_merge = b_for_merge.rename(
    columns={
        "65세이상인구": "고령인구_B_2025",
    }
)


# ============================================================
# 9. A + B 결합
# ============================================================

print("\n========================================")
print("6. A + B 데이터 결합")
print("========================================")

merged = a.merge(
    b_for_merge,
    on="merge_key",
    how="left",
    validate="one_to_one",
)

print(
    f"결합 후 지역 수: "
    f"{len(merged):,}"
)


# ============================================================
# 10. 고령인구 값 비교
# ============================================================

print("\n========================================")
print("7. 고령인구 값 일치 여부 확인")
print("========================================")

merged[
    "고령인구_차이_A_B"
] = (
    merged["고령인구_2025"]
    - merged["고령인구_B_2025"]
)

population_mismatch = merged[
    merged[
        "고령인구_차이_A_B"
    ].abs() > 0
].copy()

print(
    "고령인구 값 불일치 지역 수:",
    len(population_mismatch),
)

if not population_mismatch.empty:
    mismatch_path = (
        OUTPUT_DIR
        / "population_mismatch.csv"
    )

    population_mismatch[
        [
            "지역코드",
            "시도",
            "지역명",
            "고령인구_2025",
            "고령인구_B_2025",
            "고령인구_차이_A_B",
        ]
    ].to_csv(
        mismatch_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n주의: A/B 고령인구가 "
        "일치하지 않는 지역이 있습니다."
    )

    print(
        population_mismatch[
            [
                "시도",
                "지역명",
                "고령인구_2025",
                "고령인구_B_2025",
                "고령인구_차이_A_B",
            ]
        ]
        .head(20)
        .to_string(
            index=False,
        )
    )

else:
    print(
        "A/B 고령인구 값 전체 일치"
    )


# ============================================================
# 11. 결측치 검사
# ============================================================

print("\n========================================")
print("8. 결측치 확인")
print("========================================")

infra_cols = [
    "병원수",
    "약국수",
    "노인복지시설수",
    "버스정류장수",
    "철도역수",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

missing_summary = (
    merged[
        infra_cols
    ]
    .isna()
    .sum()
    .sort_values(
        ascending=False,
    )
)

print(
    missing_summary
)


# ============================================================
# 12. 강원 고성군 버스 결측 여부 확인
# ============================================================

print("\n========================================")
print("9. 강원 고성군 확인")
print("========================================")

goseong = merged[
    (
        merged["시도"]
        == "강원"
    )
    & (
        merged["지역명"]
        == "고성군"
    )
]

if goseong.empty:
    print(
        "강원 고성군 행을 찾지 못했습니다."
    )

else:
    print(
        goseong[
            [
                "지역코드",
                "시도",
                "지역명",
                "고령인구_2025",
                "버스정류장수",
                "노인천명당_버스정류장수",
            ]
        ].to_string(
            index=False,
        )
    )


# ============================================================
# 13. 최종 데이터 정리
# ============================================================

# B의 고령인구는 검증용으로만 사용했기 때문에
# 최종 분석 데이터에서는 제거한다.
drop_cols = [
    "시도_표준",
    "지역명_표준",
    "merge_key",
    "고령인구_B_2025",
    "고령인구_차이_A_B",
]

final = merged.drop(
    columns=drop_cols,
)

# 지역코드를 문자열로 유지
final["지역코드"] = (
    final["지역코드"]
    .astype(str)
    .str.zfill(5)
)


# ============================================================
# 14. 최종 검증
# ============================================================

print("\n========================================")
print("10. 최종 검증")
print("========================================")

print(
    f"최종 지역 수: "
    f"{len(final):,}"
)

print(
    f"최종 컬럼 수: "
    f"{len(final.columns):,}"
)

if len(final) != 229:
    raise ValueError(
        "최종 지역 수가 229개가 아닙니다. "
        f"현재: {len(final)}개"
    )

if final["지역코드"].duplicated().any():
    duplicated_codes = final[
        final["지역코드"].duplicated(
            keep=False,
        )
    ]

    print(
        duplicated_codes[
            [
                "지역코드",
                "시도",
                "지역명",
            ]
        ].to_string(
            index=False,
        )
    )

    raise ValueError(
        "지역코드 중복이 존재합니다."
    )

print(
    "지역 수 229개 확인 완료"
)

print(
    "지역코드 중복 없음"
)


# ============================================================
# 15. 최종 저장
# ============================================================

final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

print("\n========================================")
print("A + B 결합 완료")
print("========================================")

print(
    f"저장 위치:\n{OUTPUT_PATH}"
)


# ============================================================
# 16. 최종 주요 컬럼 확인
# ============================================================

print("\n===== 최종 주요 컬럼 =====")

preview_cols = [
    "지역코드",
    "시도",
    "지역명",
    "총인구_2025",
    "고령인구_2025",
    "고령화율_2025",
    "청년순이동률_2016_2025",
    "인구천명당_종사자수_2024",
    "병원수",
    "약국수",
    "노인복지시설수",
    "버스정류장수",
    "철도역수",
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]

print(
    final[
        preview_cols
    ]
    .head(10)
    .to_string(
        index=False,
    )
)