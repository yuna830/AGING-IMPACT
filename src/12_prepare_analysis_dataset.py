from pathlib import Path

import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

RESULT_DIR = (
    PROJECT_ROOT
    / "results"
    / "a_feature_selection"
)

INPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_features.csv"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 설정
# ============================================================

HIGH_CORRELATION_THRESHOLD = 0.80


# ============================================================
# 전체 분석 후보 변수
# ============================================================

FULL_FEATURES = [
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
# A 기준 축약 변수셋
#
# 현재 A 데이터에서 상관성이 매우 높은 변수들의
# 중복 반영을 줄이기 위한 임시 추천 변수셋.
#
# 최종 변수셋은 B 인프라 데이터가 결합된 이후
# 다시 결정한다.
# ============================================================

REDUCED_FEATURES = [
    # 현재 고령화 수준
    "고령화율_2025",

    # 고령화 진행 속도
    "고령화율변화폭_2016_2025",

    # 청년 이동
    "청년순이동률_2016_2025",

    # 지역 경제활동 강도
    "인구천명당_종사자수_2024",

    # 사업체 규모 특성
    "사업체당_종사자수_2024",
]


# ============================================================
# 중복성이 높아 임시 제외하는 변수와 이유
# ============================================================

EXCLUSION_REASONS = {
    "청년비율_2025": (
        "고령화율_2025와 매우 강한 음의 상관관계가 있어 "
        "유사한 인구구조 정보를 중복 반영할 가능성이 있음"
    ),

    "청년비율변화폭_2016_2025": (
        "청년층 변화 특성을 보여주는 보조 변수로 유지 가능하지만 "
        "최종 군집에서는 청년순이동률과 함께 사용할지 재검토 필요"
    ),

    "인구증감률_2016_2025": (
        "청년순이동률_2016_2025와 매우 높은 양의 상관관계가 있어 "
        "동시에 사용하면 인구 이동 특성이 중복 가중될 가능성이 있음"
    ),

    "인구천명당_사업체수_2024": (
        "인구천명당_종사자수_2024와 높은 양의 상관관계가 있어 "
        "경제활동 규모가 중복 반영될 가능성이 있음"
    ),
}


# ============================================================
# 데이터 읽기
# ============================================================

def load_data():
    print()
    print("=" * 70)
    print("1. A 분석용 데이터 읽기")
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

    print(
        f"전체 컬럼 수: {len(df.columns)}"
    )

    return df


# ============================================================
# 분석 후보 변수 검증
# ============================================================

def validate_features(
    df,
):
    print()
    print("=" * 70)
    print("2. 분석 후보 변수 검증")
    print("=" * 70)

    missing_columns = [
        column
        for column in FULL_FEATURES
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "다음 분석 변수가 없습니다:\n"
            + "\n".join(
                missing_columns
            )
        )

    print()
    print(
        f"전체 후보 변수 수: "
        f"{len(FULL_FEATURES)}"
    )

    print()
    print(
        "[후보 변수]"
    )

    for column in FULL_FEATURES:
        print(
            f"- {column}"
        )

    print()
    print(
        "[후보 변수 결측치]"
    )

    print(
        df[
            FULL_FEATURES
        ]
        .isnull()
        .sum()
        .to_string()
    )


# ============================================================
# 상관행렬 생성
# ============================================================

def create_correlation_matrix(
    df,
):
    print()
    print("=" * 70)
    print("3. 후보 변수 상관행렬 생성")
    print("=" * 70)

    correlation = (
        df[
            FULL_FEATURES
        ]
        .corr()
    )

    output_file = (
        RESULT_DIR
        / "feature_correlation.csv"
    )

    correlation.to_csv(
        output_file,
        encoding="utf-8-sig",
    )

    print()
    print(
        correlation
        .round(3)
        .to_string()
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    return correlation


# ============================================================
# 높은 상관관계 탐지
# ============================================================

def find_high_correlations(
    correlation,
):
    print()
    print("=" * 70)
    print("4. 높은 상관관계 변수쌍 확인")
    print("=" * 70)

    rows = []

    columns = list(
        correlation.columns
    )

    for i in range(
        len(columns)
    ):

        for j in range(
            i + 1,
            len(columns),
        ):

            variable1 = columns[i]
            variable2 = columns[j]

            corr_value = (
                correlation.loc[
                    variable1,
                    variable2,
                ]
            )

            if (
                abs(corr_value)
                >= HIGH_CORRELATION_THRESHOLD
            ):

                rows.append(
                    {
                        "변수1": variable1,
                        "변수2": variable2,
                        "상관계수": corr_value,
                        "절대상관계수": abs(
                            corr_value
                        ),
                    }
                )

    high_corr_df = pd.DataFrame(
        rows
    )

    if not high_corr_df.empty:

        high_corr_df = (
            high_corr_df
            .sort_values(
                "절대상관계수",
                ascending=False,
            )
            .reset_index(
                drop=True
            )
        )

    output_file = (
        RESULT_DIR
        / "high_correlation_pairs.csv"
    )

    high_corr_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"기준: |r| >= "
        f"{HIGH_CORRELATION_THRESHOLD}"
    )

    print()

    if high_corr_df.empty:

        print(
            "높은 상관관계 변수쌍이 없습니다."
        )

    else:

        print(
            high_corr_df[
                [
                    "변수1",
                    "변수2",
                    "상관계수",
                ]
            ]
            .round(3)
            .to_string(
                index=False
            )
        )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    return high_corr_df


# ============================================================
# 전체 후보 분석 데이터 생성
# ============================================================

def create_full_analysis_dataset(
    df,
):
    print()
    print("=" * 70)
    print("5. 전체 후보 분석 데이터 생성")
    print("=" * 70)

    columns = [
        "지역코드",
        "시도",
        "지역명",
    ] + FULL_FEATURES

    full_dataset = (
        df[
            columns
        ]
        .copy()
    )

    output_file = (
        RESULT_DIR
        / "a_analysis_full.csv"
    )

    full_dataset.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"지역 수: {len(full_dataset)}"
    )

    print(
        f"분석 변수 수: "
        f"{len(FULL_FEATURES)}"
    )

    print(
        f"[저장] {output_file.name}"
    )

    return full_dataset


# ============================================================
# 축약 분석 데이터 생성
# ============================================================

def create_reduced_analysis_dataset(
    df,
):
    print()
    print("=" * 70)
    print("6. A 기준 축약 변수셋 생성")
    print("=" * 70)

    columns = [
        "지역코드",
        "시도",
        "지역명",
    ] + REDUCED_FEATURES

    reduced_dataset = (
        df[
            columns
        ]
        .copy()
    )

    output_file = (
        RESULT_DIR
        / "a_analysis_reduced.csv"
    )

    reduced_dataset.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        "[임시 추천 변수]"
    )

    for feature in REDUCED_FEATURES:
        print(
            f"- {feature}"
        )

    print()
    print(
        f"지역 수: "
        f"{len(reduced_dataset)}"
    )

    print(
        f"분석 변수 수: "
        f"{len(REDUCED_FEATURES)}"
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    return reduced_dataset


# ============================================================
# 제외 후보 출력
# ============================================================

def print_exclusion_reasons():
    print()
    print("=" * 70)
    print("7. 중복 가능 변수 검토")
    print("=" * 70)

    for (
        feature,
        reason,
    ) in EXCLUSION_REASONS.items():

        print()
        print(
            f"[{feature}]"
        )

        print(
            reason
        )


# ============================================================
# 축약 변수셋 내부 상관관계 확인
# ============================================================

def check_reduced_correlations(
    df,
):
    print()
    print("=" * 70)
    print("8. 축약 변수셋 내부 상관관계 확인")
    print("=" * 70)

    corr = (
        df[
            REDUCED_FEATURES
        ]
        .corr()
    )

    print()
    print(
        corr
        .round(3)
        .to_string()
    )

    max_pair = None
    max_corr = 0

    for i in range(
        len(REDUCED_FEATURES)
    ):

        for j in range(
            i + 1,
            len(REDUCED_FEATURES),
        ):

            variable1 = (
                REDUCED_FEATURES[i]
            )

            variable2 = (
                REDUCED_FEATURES[j]
            )

            value = (
                corr.loc[
                    variable1,
                    variable2,
                ]
            )

            if abs(value) > abs(
                max_corr
            ):

                max_corr = value

                max_pair = (
                    variable1,
                    variable2,
                )

    print()

    if max_pair:

        print(
            "축약 변수셋에서 가장 높은 "
            "절대 상관관계:"
        )

        print(
            f"{max_pair[0]}"
        )

        print(
            "↔"
        )

        print(
            f"{max_pair[1]}"
        )

        print(
            f"r = {max_corr:.3f}"
        )

    return corr


# ============================================================
# 변수 역할 정리
# ============================================================

def create_feature_role_table():
    print()
    print("=" * 70)
    print("9. 변수 역할 정리")
    print("=" * 70)

    rows = [
        {
            "변수":
                "고령화율_2025",

            "분석축":
                "고령화 수준",

            "역할":
                "현재 지역의 고령화 정도",
        },

        {
            "변수":
                "고령화율변화폭_2016_2025",

            "분석축":
                "고령화 속도",

            "역할":
                "2016~2025 고령화 진행 속도",
        },

        {
            "변수":
                "청년순이동률_2016_2025",

            "분석축":
                "청년 이동",

            "역할":
                "청년층의 장기 누적 순유입/순유출",
        },

        {
            "변수":
                "인구천명당_종사자수_2024",

            "분석축":
                "경제활동",

            "역할":
                "인구 규모를 보정한 지역 경제활동 강도",
        },

        {
            "변수":
                "사업체당_종사자수_2024",

            "분석축":
                "사업체 규모",

            "역할":
                "사업체 하나당 평균 고용 규모",
        },
    ]

    role_df = pd.DataFrame(
        rows
    )

    output_file = (
        RESULT_DIR
        / "reduced_feature_roles.csv"
    )

    role_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        role_df.to_string(
            index=False
        )
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    return role_df


# ============================================================
# 요약 파일 생성
# ============================================================

def create_summary_file(
    high_corr_df,
    reduced_corr,
):
    print()
    print("=" * 70)
    print("10. 변수선정 요약 파일 생성")
    print("=" * 70)

    output_file = (
        RESULT_DIR
        / "feature_selection_summary.txt"
    )

    lines = [
        "AGING IMPACT - A 분석 변수 선정",
        "=" * 70,
        "",
        "[목적]",
        (
            "최종 군집분석 전에 A 데이터 내에서 "
            "서로 중복성이 높은 변수들을 확인하고 "
            "분석 후보 변수를 정리한다."
        ),
        "",
        "[전체 후보 변수]",
    ]

    for feature in FULL_FEATURES:
        lines.append(
            f"- {feature}"
        )

    lines.extend(
        [
            "",
            (
                "[높은 상관관계 기준] "
                f"|r| >= "
                f"{HIGH_CORRELATION_THRESHOLD}"
            ),
            "",
        ]
    )

    if high_corr_df.empty:

        lines.append(
            "해당 기준을 넘는 변수쌍 없음"
        )

    else:

        for _, row in (
            high_corr_df.iterrows()
        ):

            lines.append(
                (
                    f"- {row['변수1']} ↔ "
                    f"{row['변수2']}: "
                    f"{row['상관계수']:.3f}"
                )
            )

    lines.extend(
        [
            "",
            "[A 기준 임시 축약 변수셋]",
        ]
    )

    for feature in REDUCED_FEATURES:
        lines.append(
            f"- {feature}"
        )

    lines.extend(
        [
            "",
            "[임시 제외 또는 보류 변수]",
        ]
    )

    for (
        feature,
        reason,
    ) in EXCLUSION_REASONS.items():

        lines.append(
            f"- {feature}"
        )

        lines.append(
            f"  이유: {reason}"
        )

    lines.extend(
        [
            "",
            "[주의]",
            (
                "이 변수셋은 A 데이터만 기준으로 만든 "
                "임시 후보이다."
            ),
            (
                "B 담당 생활 인프라 데이터가 결합된 이후 "
                "전체 상관관계를 다시 계산한 뒤 "
                "최종 군집분석 변수를 결정한다."
            ),
            (
                "현재 단계에서는 K-Means 군집 결과를 "
                "최종 결론으로 사용하지 않는다."
            ),
        ]
    )

    output_file.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("A 분석 후보 변수 정리")
    print("=" * 70)

    df = load_data()

    validate_features(
        df
    )

    correlation = (
        create_correlation_matrix(
            df
        )
    )

    high_corr_df = (
        find_high_correlations(
            correlation
        )
    )

    create_full_analysis_dataset(
        df
    )

    create_reduced_analysis_dataset(
        df
    )

    print_exclusion_reasons()

    reduced_corr = (
        check_reduced_correlations(
            df
        )
    )

    create_feature_role_table()

    create_summary_file(
        high_corr_df,
        reduced_corr,
    )

    print()
    print("=" * 70)
    print("A 분석 후보 변수 정리 완료")
    print("=" * 70)

    print()
    print(
        "결과 폴더:"
    )

    print(
        RESULT_DIR
    )

    print()
    print(
        "중요:"
    )

    print(
        "현재 REDUCED 변수셋은 "
        "A 데이터만 기준으로 만든 임시 후보입니다."
    )

    print(
        "B 데이터 결합 후 최종 변수선정을 다시 진행합니다."
    )


if __name__ == "__main__":
    main()