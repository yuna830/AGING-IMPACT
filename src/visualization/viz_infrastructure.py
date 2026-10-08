from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# =========================================================
# 경로 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "results" / "ab_merge" / "ab_dataset.csv"
OUTPUT_DIR = BASE_DIR / "results" / "visualization" / "infrastructure"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 한글 폰트 설정
# =========================================================
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# =========================================================
# 데이터 불러오기
# =========================================================
df = pd.read_csv(INPUT_PATH)

df["지역표시명"] = df["시도"].astype(str) + " " + df["지역명"].astype(str)

print("데이터 크기:", df.shape)
print("입력 파일:", INPUT_PATH)


# =========================================================
# 생활 인프라 지표
# =========================================================
INFRA_METRICS = {
    "hospital": {
        "column": "노인천명당_병원수",
        "label": "병원",
    },
    "pharmacy": {
        "column": "노인천명당_약국수",
        "label": "약국",
    },
    "welfare": {
        "column": "노인천명당_복지시설수",
        "label": "복지시설",
    },
    "bus": {
        "column": "노인천명당_버스정류장수",
        "label": "버스정류장",
    },
}


# =========================================================
# 상위 / 하위 10개 지역 막대그래프
# =========================================================
def save_ranking_chart(data, column, label, key):
    plot_df = data[["지역표시명", column]].dropna().copy()

    # 동일 값이 있어도 항상 10개 지역만 선택
    bottom10 = plot_df.nsmallest(10, column).sort_values(column, ascending=False)
    top10 = plot_df.nlargest(10, column).sort_values(column)

    # 하위 10개
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(bottom10["지역표시명"], bottom10[column])

    ax.set_title(
        f"노인 1,000명당 {label} 수 하위 10개 지역",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_xlabel(f"노인 1,000명당 {label} 수")
    ax.set_ylabel("지역")
    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()

    output_path = OUTPUT_DIR / f"{key}_bottom10.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    # 상위 10개
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(top10["지역표시명"], top10[column])

    ax.set_title(
        f"노인 1,000명당 {label} 수 상위 10개 지역",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_xlabel(f"노인 1,000명당 {label} 수")
    ax.set_ylabel("지역")
    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()

    output_path = OUTPUT_DIR / f"{key}_top10.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"[완료] {label} 상위/하위 10개")


# =========================================================
# 철도역 시각화
# =========================================================
def save_rail_charts(data):
    column = "노인천명당_철도역수"

    rail_df = data[
        ["지역표시명", "철도역수", column]
    ].dropna(subset=[column]).copy()

    # 철도역 상위 10개 지역
    top10 = rail_df.nlargest(10, column).sort_values(column)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(top10["지역표시명"], top10[column])

    ax.set_title(
        "노인 1,000명당 도시철도 역사 수 상위 10개 지역",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_xlabel("노인 1,000명당 도시철도 역사 수")
    ax.set_ylabel("지역")
    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()

    output_path = OUTPUT_DIR / "rail_top10.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    # 철도역 보유 / 미보유 지역 수
    has_rail = int((data["철도역수"] > 0).sum())
    no_rail = int((data["철도역수"] == 0).sum())

    rail_count = pd.DataFrame(
        {
            "구분": ["도시철도 역사 보유", "도시철도 역사 미보유"],
            "지역수": [has_rail, no_rail],
        }
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    bars = ax.bar(rail_count["구분"], rail_count["지역수"])

    ax.set_title(
        "도시철도 역사 보유 여부에 따른 지역 수",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_ylabel("지역 수")
    ax.grid(axis="y", alpha=0.25)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}개",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()

    output_path = OUTPUT_DIR / "rail_availability.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("[완료] 도시철도 시각화")


# =========================================================
# 고령화율 ↔ 생활 인프라 산점도
# =========================================================
def save_scatter(data, y_column, y_label, key):
    scatter_df = data[
        ["고령화율_2025", y_column]
    ].dropna().copy()

    correlation = scatter_df["고령화율_2025"].corr(
        scatter_df[y_column]
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(
        scatter_df["고령화율_2025"],
        scatter_df[y_column],
        alpha=0.65,
    )

    ax.set_title(
        f"고령화율과 노인 1,000명당 {y_label} 수",
        fontsize=15,
        fontweight="bold",
    )

    ax.set_xlabel("고령화율_2025 (%)")
    ax.set_ylabel(f"노인 1,000명당 {y_label} 수")

    ax.grid(alpha=0.25)

    ax.text(
        0.03,
        0.95,
        f"Pearson r = {correlation:.3f}",
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox={
            "boxstyle": "round",
            "alpha": 0.15,
        },
    )

    plt.tight_layout()

    output_path = OUTPUT_DIR / f"scatter_aging_{key}.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(
        f"[완료] 고령화율 ↔ {y_label} "
        f"(r = {correlation:.3f})"
    )


# =========================================================
# 실행
# =========================================================
def main():
    print("\n===== 생활 인프라 시각화 시작 =====")

    # 결측치 확인
    print("\n인프라 지표 결측치")
    for info in INFRA_METRICS.values():
        column = info["column"]
        print(f"{column}: {df[column].isna().sum()}")

    print(
        "노인천명당_철도역수:",
        df["노인천명당_철도역수"].isna().sum(),
    )

    # 병원 / 약국 / 복지시설 / 버스 상하위 10
    for key, info in INFRA_METRICS.items():
        save_ranking_chart(
            df,
            info["column"],
            info["label"],
            key,
        )

    # 철도
    save_rail_charts(df)

    # 대표 산점도 3개
    save_scatter(
        df,
        "노인천명당_복지시설수",
        "복지시설",
        "welfare",
    )

    save_scatter(
        df,
        "노인천명당_약국수",
        "약국",
        "pharmacy",
    )

    save_scatter(
        df,
        "노인천명당_철도역수",
        "도시철도 역사",
        "rail",
    )

    print("\n===== 모든 시각화 완료 =====")
    print("저장 위치:", OUTPUT_DIR)


if __name__ == "__main__":
    main()