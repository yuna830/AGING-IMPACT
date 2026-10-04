from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RESULT_DIR = (
    PROJECT_ROOT
    / "results"
    / "a_sido_summary"
)

INPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_features.csv"
)


# ============================================================
# 결과 폴더 생성
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 한글 폰트 설정
# ============================================================

def setup_korean_font():
    """
    Windows 기준 한글 폰트 설정.
    """

    plt.rcParams[
        "font.family"
    ] = "Malgun Gothic"

    plt.rcParams[
        "axes.unicode_minus"
    ] = False


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
        f"시도 수: {df['시도'].nunique()}"
    )

    print()
    print(
        "[시도별 지역 수]"
    )

    print(
        df[
            "시도"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    return df


# ============================================================
# 시도별 합계 생성
# ============================================================

def create_sido_summary(
    df,
):
    print()
    print("=" * 70)
    print("2. 시도별 합계 및 비율 계산")
    print("=" * 70)

    # --------------------------------------------------------
    # 시도별 지역 수
    # --------------------------------------------------------

    region_count = (
        df
        .groupby(
            "시도"
        )[
            "지역코드"
        ]
        .nunique()
        .rename(
            "분석지역수"
        )
    )

    # --------------------------------------------------------
    # 절대값은 시도 단위로 합산
    # --------------------------------------------------------

    sum_columns = [
        "총인구_2016",
        "총인구_2024",
        "총인구_2025",

        "고령인구_2016",
        "고령인구_2025",

        "청년인구_2016",
        "청년인구_2025",

        "청년전입_누적_2016_2025",
        "청년전출_누적_2016_2025",
        "청년순이동_누적_2016_2025",

        "사업체수_2024",
        "종사자수_2024",
    ]

    summary = (
        df
        .groupby(
            "시도",
            as_index=True,
        )[
            sum_columns
        ]
        .sum()
    )

    summary = (
        summary
        .join(
            region_count
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # 고령화율
    # --------------------------------------------------------

    summary[
        "고령화율_2016"
    ] = (
        summary[
            "고령인구_2016"
        ]
        /
        summary[
            "총인구_2016"
        ]
        * 100
    )

    summary[
        "고령화율_2025"
    ] = (
        summary[
            "고령인구_2025"
        ]
        /
        summary[
            "총인구_2025"
        ]
        * 100
    )

    summary[
        "고령화율변화폭_2016_2025"
    ] = (
        summary[
            "고령화율_2025"
        ]
        -
        summary[
            "고령화율_2016"
        ]
    )

    # --------------------------------------------------------
    # 청년비율
    # --------------------------------------------------------

    summary[
        "청년비율_2016"
    ] = (
        summary[
            "청년인구_2016"
        ]
        /
        summary[
            "총인구_2016"
        ]
        * 100
    )

    summary[
        "청년비율_2025"
    ] = (
        summary[
            "청년인구_2025"
        ]
        /
        summary[
            "총인구_2025"
        ]
        * 100
    )

    summary[
        "청년비율변화폭_2016_2025"
    ] = (
        summary[
            "청년비율_2025"
        ]
        -
        summary[
            "청년비율_2016"
        ]
    )

    # --------------------------------------------------------
    # 인구증감률
    # --------------------------------------------------------

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
    )

    # --------------------------------------------------------
    # 누적 청년순이동률
    #
    # 시군구 이동률의 단순 평균이 아니라
    # 시도 전체 누적 순이동 /
    # 시도 전체 2016 청년인구
    # --------------------------------------------------------

    summary[
        "청년순이동률_2016_2025"
    ] = (
        summary[
            "청년순이동_누적_2016_2025"
        ]
        /
        summary[
            "청년인구_2016"
        ]
        * 100
    )

    # --------------------------------------------------------
    # 인구 천명당 사업체수
    # --------------------------------------------------------

    summary[
        "인구천명당_사업체수_2024"
    ] = (
        summary[
            "사업체수_2024"
        ]
        /
        summary[
            "총인구_2024"
        ]
        * 1000
    )

    # --------------------------------------------------------
    # 인구 천명당 종사자수
    # --------------------------------------------------------

    summary[
        "인구천명당_종사자수_2024"
    ] = (
        summary[
            "종사자수_2024"
        ]
        /
        summary[
            "총인구_2024"
        ]
        * 1000
    )

    # --------------------------------------------------------
    # 사업체당 종사자수
    # --------------------------------------------------------

    summary[
        "사업체당_종사자수_2024"
    ] = (
        summary[
            "종사자수_2024"
        ]
        /
        summary[
            "사업체수_2024"
        ]
    )

    # --------------------------------------------------------
    # 소수점 정리
    # --------------------------------------------------------

    rate_columns = [
        "고령화율_2016",
        "고령화율_2025",
        "고령화율변화폭_2016_2025",

        "청년비율_2016",
        "청년비율_2025",
        "청년비율변화폭_2016_2025",

        "인구증감률_2016_2025",
        "청년순이동률_2016_2025",

        "인구천명당_사업체수_2024",
        "인구천명당_종사자수_2024",
        "사업체당_종사자수_2024",
    ]

    for column in rate_columns:

        summary[
            column
        ] = (
            summary[
                column
            ]
            .round(2)
        )

    return summary


# ============================================================
# 컬럼 순서 정리
# ============================================================

def organize_columns(
    summary,
):
    print()
    print("=" * 70)
    print("3. 시도 요약 컬럼 정리")
    print("=" * 70)

    columns = [
        "시도",
        "분석지역수",

        "총인구_2016",
        "총인구_2024",
        "총인구_2025",

        "고령인구_2016",
        "고령인구_2025",

        "청년인구_2016",
        "청년인구_2025",

        "고령화율_2016",
        "고령화율_2025",
        "고령화율변화폭_2016_2025",

        "청년비율_2016",
        "청년비율_2025",
        "청년비율변화폭_2016_2025",

        "인구증감률_2016_2025",

        "청년전입_누적_2016_2025",
        "청년전출_누적_2016_2025",
        "청년순이동_누적_2016_2025",
        "청년순이동률_2016_2025",

        "사업체수_2024",
        "종사자수_2024",

        "인구천명당_사업체수_2024",
        "인구천명당_종사자수_2024",
        "사업체당_종사자수_2024",
    ]

    return (
        summary[
            columns
        ]
        .copy()
    )


# ============================================================
# 결과 저장
# ============================================================

def save_summary(
    summary,
):
    print()
    print("=" * 70)
    print("4. 시도 요약 CSV 저장")
    print("=" * 70)

    output_file = (
        RESULT_DIR
        / "sido_summary.csv"
    )

    summary.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"[저장] {output_file}"
    )


# ============================================================
# 순위표 생성
# ============================================================

def create_rankings(
    summary,
):
    print()
    print("=" * 70)
    print("5. 시도별 순위")
    print("=" * 70)

    configs = [
        (
            "고령화율_2025",
            False,
            "고령화율 상위",
        ),
        (
            "고령화율변화폭_2016_2025",
            False,
            "고령화 증가폭 상위",
        ),
        (
            "청년순이동률_2016_2025",
            True,
            "청년순유출 심화",
        ),
        (
            "청년순이동률_2016_2025",
            False,
            "청년순유입 상위",
        ),
        (
            "인구증감률_2016_2025",
            True,
            "인구감소 심화",
        ),
        (
            "인구증감률_2016_2025",
            False,
            "인구증가 상위",
        ),
        (
            "인구천명당_사업체수_2024",
            False,
            "인구천명당 사업체수 상위",
        ),
        (
            "인구천명당_종사자수_2024",
            False,
            "인구천명당 종사자수 상위",
        ),
    ]

    ranking_list = []

    for (
        column,
        ascending,
        label,
    ) in configs:

        temp = (
            summary
            .sort_values(
                column,
                ascending=ascending,
            )[
                [
                    "시도",
                    column,
                ]
            ]
            .copy()
        )

        temp[
            "순위"
        ] = range(
            1,
            len(temp) + 1,
        )

        temp[
            "구분"
        ] = label

        temp[
            "지표"
        ] = column

        temp = temp.rename(
            columns={
                column:
                    "값"
            }
        )

        temp = temp[
            [
                "구분",
                "순위",
                "시도",
                "지표",
                "값",
            ]
        ]

        ranking_list.append(
            temp
        )

    rankings = pd.concat(
        ranking_list,
        ignore_index=True,
    )

    output_file = (
        RESULT_DIR
        / "sido_rankings.csv"
    )

    rankings.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    # --------------------------------------------------------
    # 주요 순위 출력
    # --------------------------------------------------------

    print()
    print(
        "[2025 고령화율]"
    )

    print(
        summary
        .sort_values(
            "고령화율_2025",
            ascending=False,
        )[
            [
                "시도",
                "고령화율_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[고령화율 증가폭]"
    )

    print(
        summary
        .sort_values(
            "고령화율변화폭_2016_2025",
            ascending=False,
        )[
            [
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

    print()
    print(
        "[누적 청년순이동률]"
    )

    print(
        summary
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=False,
        )[
            [
                "시도",
                "청년순이동률_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[인구증감률]"
    )

    print(
        summary
        .sort_values(
            "인구증감률_2016_2025",
            ascending=False,
        )[
            [
                "시도",
                "인구증감률_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )


# ============================================================
# 그래프 저장 공통 함수
# ============================================================

def save_figure(
    filename,
):
    output_file = (
        RESULT_DIR
        / filename
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"[저장] {filename}"
    )


# ============================================================
# 시도별 막대그래프
# ============================================================

def plot_sido_bar(
    summary,
    column,
    title,
    ylabel,
    filename,
    ascending=True,
):
    plot_df = (
        summary
        .sort_values(
            column,
            ascending=ascending,
        )
        .copy()
    )

    plt.figure(
        figsize=(12, 7)
    )

    plt.bar(
        plot_df[
            "시도"
        ],
        plot_df[
            column
        ],
    )

    plt.title(
        title,
        fontsize=15,
    )

    plt.xlabel(
        "시도"
    )

    plt.ylabel(
        ylabel
    )

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.grid(
        axis="y",
        alpha=0.25,
    )

    # --------------------------------------------------------
    # 0 기준선
    # --------------------------------------------------------

    if (
        plot_df[
            column
        ].min()
        < 0
    ):
        plt.axhline(
            0,
            linewidth=1,
            alpha=0.6,
        )

    save_figure(
        filename
    )


# ============================================================
# 그래프 생성
# ============================================================

def create_charts(
    summary,
):
    print()
    print("=" * 70)
    print("6. 시도별 그래프 생성")
    print("=" * 70)

    plot_sido_bar(
        summary,
        "고령화율_2025",
        "시도별 2025년 고령화율",
        "고령화율 (%)",
        "01_sido_aging_rate_2025.png",
        ascending=False,
    )

    plot_sido_bar(
        summary,
        "고령화율변화폭_2016_2025",
        "시도별 고령화율 변화폭 (2016~2025)",
        "고령화율 변화폭 (%p)",
        "02_sido_aging_change.png",
        ascending=False,
    )

    plot_sido_bar(
        summary,
        "청년순이동률_2016_2025",
        "시도별 누적 청년순이동률 (2016~2025)",
        "누적 청년순이동률 (%)",
        "03_sido_youth_migration_rate.png",
        ascending=True,
    )

    plot_sido_bar(
        summary,
        "인구증감률_2016_2025",
        "시도별 인구증감률 (2016~2025)",
        "인구증감률 (%)",
        "04_sido_population_change.png",
        ascending=True,
    )

    plot_sido_bar(
        summary,
        "인구천명당_사업체수_2024",
        "시도별 인구 천명당 사업체수 (2024)",
        "인구 천명당 사업체수",
        "05_sido_business_per_1000.png",
        ascending=False,
    )

    plot_sido_bar(
        summary,
        "인구천명당_종사자수_2024",
        "시도별 인구 천명당 종사자수 (2024)",
        "인구 천명당 종사자수",
        "06_sido_employee_per_1000.png",
        ascending=False,
    )


# ============================================================
# 시도 주요 관계 요약
# ============================================================

def create_text_summary(
    summary,
):
    print()
    print("=" * 70)
    print("7. 시도 분석 요약 생성")
    print("=" * 70)

    highest_aging = (
        summary
        .sort_values(
            "고령화율_2025",
            ascending=False,
        )
        .iloc[0]
    )

    fastest_aging = (
        summary
        .sort_values(
            "고령화율변화폭_2016_2025",
            ascending=False,
        )
        .iloc[0]
    )

    highest_inflow = (
        summary
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=False,
        )
        .iloc[0]
    )

    highest_outflow = (
        summary
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=True,
        )
        .iloc[0]
    )

    highest_growth = (
        summary
        .sort_values(
            "인구증감률_2016_2025",
            ascending=False,
        )
        .iloc[0]
    )

    highest_decline = (
        summary
        .sort_values(
            "인구증감률_2016_2025",
            ascending=True,
        )
        .iloc[0]
    )

    lines = [
        "AGING IMPACT - A 시도별 분석 요약",
        "=" * 60,
        "",
        f"분석 시도 수: {len(summary)}",
        "",
        "[2025 고령화율 최고]",
        (
            f"{highest_aging['시도']} "
            f"{highest_aging['고령화율_2025']:.2f}%"
        ),
        "",
        "[2016~2025 고령화율 증가폭 최고]",
        (
            f"{fastest_aging['시도']} "
            f"+{fastest_aging['고령화율변화폭_2016_2025']:.2f}%p"
        ),
        "",
        "[청년순유입률 최고]",
        (
            f"{highest_inflow['시도']} "
            f"{highest_inflow['청년순이동률_2016_2025']:.2f}%"
        ),
        "",
        "[청년순유출률 최대]",
        (
            f"{highest_outflow['시도']} "
            f"{highest_outflow['청년순이동률_2016_2025']:.2f}%"
        ),
        "",
        "[인구증가율 최고]",
        (
            f"{highest_growth['시도']} "
            f"{highest_growth['인구증감률_2016_2025']:.2f}%"
        ),
        "",
        "[인구감소율 최대]",
        (
            f"{highest_decline['시도']} "
            f"{highest_decline['인구증감률_2016_2025']:.2f}%"
        ),
        "",
        "[주의]",
        (
            "시도별 비율은 시군구 비율의 단순 평균이 아니라 "
            "시도별 인구 및 이동량을 합산한 후 다시 계산한 값입니다."
        ),
    ]

    output_file = (
        RESULT_DIR
        / "sido_summary.txt"
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
    print("A 데이터 시도별 요약 분석")
    print("=" * 70)

    setup_korean_font()

    df = load_data()

    summary = (
        create_sido_summary(
            df
        )
    )

    summary = (
        organize_columns(
            summary
        )
    )

    save_summary(
        summary
    )

    create_rankings(
        summary
    )

    create_charts(
        summary
    )

    create_text_summary(
        summary
    )

    print()
    print("=" * 70)
    print("A 시도별 요약 분석 완료")
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