from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULT_DIR = PROJECT_ROOT / "results" / "a_eda"

INPUT_FILE = (
    PROCESSED_DIR
    / "a_dataset_features.csv"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 분석 변수
# ============================================================

CORRELATION_COLUMNS = [
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
# 한글 폰트 설정
# ============================================================

def setup_korean_font():
    """
    Windows 기준 한글 폰트 설정.

    맑은 고딕이 설치되어 있다는 전제로 사용한다.
    """

    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 데이터 읽기
# ============================================================

def load_data() -> pd.DataFrame:
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
        f"컬럼 수: {len(df.columns)}"
    )

    return df


# ============================================================
# 그래프 저장 공통 함수
# ============================================================

def save_current_figure(
    filename: str,
):
    """
    현재 matplotlib figure 저장.
    """

    output_path = (
        RESULT_DIR / filename
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"[저장] {output_path.name}"
    )


# ============================================================
# 히스토그램
# ============================================================

def plot_histogram(
    df: pd.DataFrame,
    column: str,
    title: str,
    xlabel: str,
    filename: str,
):
    plt.figure(
        figsize=(9, 6)
    )

    plt.hist(
        df[column].dropna(),
        bins=20,
        edgecolor="black",
        alpha=0.8,
    )

    plt.title(
        title,
        fontsize=14,
    )

    plt.xlabel(
        xlabel
    )

    plt.ylabel(
        "지역 수"
    )

    plt.grid(
        axis="y",
        alpha=0.25,
    )

    save_current_figure(
        filename
    )


# ============================================================
# 산점도
# ============================================================

def plot_scatter(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
):
    plt.figure(
        figsize=(9, 6)
    )

    plt.scatter(
        df[x_column],
        df[y_column],
        alpha=0.7,
    )

    plt.axhline(
        0,
        linewidth=1,
        alpha=0.5,
    )

    plt.axvline(
        0,
        linewidth=1,
        alpha=0.5,
    )

    plt.title(
        title,
        fontsize=14,
    )

    plt.xlabel(
        xlabel
    )

    plt.ylabel(
        ylabel
    )

    plt.grid(
        alpha=0.25,
    )

    # 상관계수
    corr = (
        df[
            [
                x_column,
                y_column,
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    plt.text(
        0.02,
        0.98,
        f"상관계수 r = {corr:.3f}",
        transform=plt.gca().transAxes,
        va="top",
        ha="left",
        fontsize=11,
    )

    save_current_figure(
        filename
    )


# ============================================================
# 히스토그램 생성
# ============================================================

def create_distribution_plots(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("2. 분포 그래프 생성")
    print("=" * 70)

    plot_histogram(
        df,
        "고령화율_2025",
        "2025년 고령화율 분포",
        "고령화율 (%)",
        "01_hist_aging_rate_2025.png",
    )

    plot_histogram(
        df,
        "고령화율변화폭_2016_2025",
        "2016~2025 고령화율 변화폭 분포",
        "고령화율 변화폭 (%p)",
        "02_hist_aging_change.png",
    )

    plot_histogram(
        df,
        "청년순이동률_2016_2025",
        "2016~2025 누적 청년순이동률 분포",
        "누적 청년순이동률 (%)",
        "03_hist_youth_migration_rate.png",
    )

    plot_histogram(
        df,
        "인구증감률_2016_2025",
        "2016~2025 인구증감률 분포",
        "인구증감률 (%)",
        "04_hist_population_change.png",
    )


# ============================================================
# 관계 그래프 생성
# ============================================================

def create_scatter_plots(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("3. 변수 관계 산점도 생성")
    print("=" * 70)

    plot_scatter(
        df,
        "고령화율_2025",
        "인구증감률_2016_2025",
        "고령화율과 인구증감률",
        "고령화율_2025 (%)",
        "인구증감률_2016_2025 (%)",
        "05_scatter_aging_vs_population_change.png",
    )

    plot_scatter(
        df,
        "고령화율_2025",
        "청년순이동률_2016_2025",
        "고령화율과 청년순이동률",
        "고령화율_2025 (%)",
        "청년순이동률_2016_2025 (%)",
        "06_scatter_aging_vs_youth_migration.png",
    )

    plot_scatter(
        df,
        "고령화율변화폭_2016_2025",
        "청년순이동률_2016_2025",
        "고령화율 변화폭과 청년순이동률",
        "고령화율 변화폭 (%p)",
        "청년순이동률_2016_2025 (%)",
        "07_scatter_aging_change_vs_youth_migration.png",
    )

    plot_scatter(
        df,
        "청년비율변화폭_2016_2025",
        "청년순이동률_2016_2025",
        "청년비율 변화폭과 청년순이동률",
        "청년비율 변화폭 (%p)",
        "청년순이동률_2016_2025 (%)",
        "08_scatter_youth_change_vs_youth_migration.png",
    )

    plot_scatter(
        df,
        "고령화율_2025",
        "인구천명당_사업체수_2024",
        "고령화율과 인구 천명당 사업체수",
        "고령화율_2025 (%)",
        "인구 천명당 사업체수",
        "09_scatter_aging_vs_business_per_1000.png",
    )

    plot_scatter(
        df,
        "고령화율_2025",
        "인구천명당_종사자수_2024",
        "고령화율과 인구 천명당 종사자수",
        "고령화율_2025 (%)",
        "인구 천명당 종사자수",
        "10_scatter_aging_vs_employee_per_1000.png",
    )


# ============================================================
# 상관행렬
# ============================================================

def create_correlation_analysis(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("4. 상관분석")
    print("=" * 70)

    corr = (
        df[
            CORRELATION_COLUMNS
        ]
        .corr()
    )

    # CSV 저장
    corr_file = (
        RESULT_DIR
        / "correlation_matrix.csv"
    )

    corr.to_csv(
        corr_file,
        encoding="utf-8-sig",
    )

    print()
    print(
        "[상관행렬]"
    )

    print(
        corr
        .round(3)
        .to_string()
    )

    print()
    print(
        f"[저장] {corr_file.name}"
    )

    # --------------------------------------------------------
    # Heatmap 직접 그리기
    # seaborn 없이 matplotlib 사용
    # --------------------------------------------------------

    plt.figure(
        figsize=(12, 10)
    )

    image = plt.imshow(
        corr.values,
        aspect="auto",
        vmin=-1,
        vmax=1,
    )

    plt.colorbar(
        image,
        label="상관계수",
    )

    plt.xticks(
        range(
            len(
                corr.columns
            )
        ),
        corr.columns,
        rotation=60,
        ha="right",
    )

    plt.yticks(
        range(
            len(
                corr.index
            )
        ),
        corr.index,
    )

    # 각 셀 숫자 표시
    for row in range(
        len(corr.index)
    ):
        for col in range(
            len(corr.columns)
        ):
            plt.text(
                col,
                row,
                f"{corr.iloc[row, col]:.2f}",
                ha="center",
                va="center",
                fontsize=8,
            )

    plt.title(
        "A 데이터 핵심 변수 상관행렬",
        fontsize=14,
    )

    save_current_figure(
        "11_correlation_heatmap.png"
    )

    return corr


# ============================================================
# 상관관계 Top 확인
# ============================================================

def print_top_correlations(
    corr: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("5. 주요 상관관계")
    print("=" * 70)

    pairs = []

    columns = list(
        corr.columns
    )

    for i in range(
        len(columns)
    ):
        for j in range(
            i + 1,
            len(columns),
        ):
            col1 = columns[i]
            col2 = columns[j]

            value = (
                corr.loc[
                    col1,
                    col2,
                ]
            )

            pairs.append(
                {
                    "변수1": col1,
                    "변수2": col2,
                    "상관계수": value,
                    "절대값": abs(
                        value
                    ),
                }
            )

    pair_df = pd.DataFrame(
        pairs
    )

    pair_df = (
        pair_df
        .sort_values(
            "절대값",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    print()
    print(
        "[절대 상관계수 상위 15개]"
    )

    print(
        pair_df[
            [
                "변수1",
                "변수2",
                "상관계수",
            ]
        ]
        .head(15)
        .round(3)
        .to_string(
            index=False
        )
    )

    pair_file = (
        RESULT_DIR
        / "correlation_pairs.csv"
    )

    pair_df.drop(
        columns=[
            "절대값"
        ]
    ).to_csv(
        pair_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"[저장] {pair_file.name}"
    )


# ============================================================
# Top / Bottom 지역 요약
# ============================================================

def create_top_bottom_summary(
    df: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("6. Top / Bottom 지역 분석")
    print("=" * 70)

    results = []

    ranking_configs = [
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

    for (
        column,
        ascending,
        category,
    ) in ranking_configs:

        temp = (
            df
            .sort_values(
                column,
                ascending=ascending,
            )
            .head(10)[
                [
                    "지역코드",
                    "지역명",
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
        ] = category

        temp = (
            temp.rename(
                columns={
                    column:
                        "값"
                }
            )
        )

        temp[
            "지표"
        ] = column

        results.append(
            temp[
                [
                    "구분",
                    "순위",
                    "지역코드",
                    "시도",
                    "지역명",
                    "지표",
                    "값",
                ]
            ]
        )

    summary = pd.concat(
        results,
        ignore_index=True,
    )

    output_file = (
        RESULT_DIR
        / "top_bottom_regions.csv"
    )

    summary.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"[저장] {output_file.name}"
    )

    print()
    print(
        "[고령화율 상위 10개]"
    )

    print(
        df
        .sort_values(
            "고령화율_2025",
            ascending=False,
        )
        .head(10)[
            [
                "지역코드",
                "시도",
                "지역명",
                "고령화율_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "[청년순유출 심화 10개]"
    )

    print(
        df
        .sort_values(
            "청년순이동률_2016_2025",
            ascending=True,
        )
        .head(10)[
            [
                "지역코드",
                "시도",
                "지역명",
                "청년순이동률_2016_2025",
            ]
        ]
        .to_string(
            index=False
        )
    )


# ============================================================
# EDA 요약 텍스트 생성
# ============================================================

def create_eda_summary(
    df: pd.DataFrame,
    corr: pd.DataFrame,
):
    print()
    print("=" * 70)
    print("7. EDA 요약 파일 생성")
    print("=" * 70)

    summary_file = (
        RESULT_DIR
        / "eda_summary.txt"
    )

    aging_population_corr = (
        corr.loc[
            "고령화율_2025",
            "인구증감률_2016_2025",
        ]
    )

    aging_migration_corr = (
        corr.loc[
            "고령화율_2025",
            "청년순이동률_2016_2025",
        ]
    )

    aging_change_migration_corr = (
        corr.loc[
            "고령화율변화폭_2016_2025",
            "청년순이동률_2016_2025",
        ]
    )

    youth_change_migration_corr = (
        corr.loc[
            "청년비율변화폭_2016_2025",
            "청년순이동률_2016_2025",
        ]
    )

    aging_business_corr = (
        corr.loc[
            "고령화율_2025",
            "인구천명당_사업체수_2024",
        ]
    )

    aging_employee_corr = (
        corr.loc[
            "고령화율_2025",
            "인구천명당_종사자수_2024",
        ]
    )

    lines = [
        "AGING IMPACT - A 데이터 EDA 요약",
        "=" * 60,
        "",
        f"전체 분석 지역 수: {len(df)}",
        "",
        "[주요 상관계수]",
        (
            "고령화율_2025 ↔ 인구증감률_2016_2025: "
            f"{aging_population_corr:.3f}"
        ),
        (
            "고령화율_2025 ↔ 청년순이동률_2016_2025: "
            f"{aging_migration_corr:.3f}"
        ),
        (
            "고령화율변화폭_2016_2025 ↔ "
            "청년순이동률_2016_2025: "
            f"{aging_change_migration_corr:.3f}"
        ),
        (
            "청년비율변화폭_2016_2025 ↔ "
            "청년순이동률_2016_2025: "
            f"{youth_change_migration_corr:.3f}"
        ),
        (
            "고령화율_2025 ↔ "
            "인구천명당_사업체수_2024: "
            f"{aging_business_corr:.3f}"
        ),
        (
            "고령화율_2025 ↔ "
            "인구천명당_종사자수_2024: "
            f"{aging_employee_corr:.3f}"
        ),
        "",
        "[기초통계]",
        (
            df[
                CORRELATION_COLUMNS
            ]
            .describe()
            .round(2)
            .to_string()
        ),
    ]

    summary_file.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"[저장] {summary_file.name}"
    )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("=" * 70)
    print("AGING IMPACT")
    print("A 데이터 탐색적 분석")
    print("=" * 70)

    setup_korean_font()

    df = load_data()

    create_distribution_plots(
        df
    )

    create_scatter_plots(
        df
    )

    corr = (
        create_correlation_analysis(
            df
        )
    )

    print_top_correlations(
        corr
    )

    create_top_bottom_summary(
        df
    )

    create_eda_summary(
        df,
        corr,
    )

    print()
    print("=" * 70)
    print("A 데이터 EDA 완료")
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