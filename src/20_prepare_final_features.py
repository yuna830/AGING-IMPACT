from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 경로 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR
    / "results"
    / "ab_merge"
    / "ab_dataset.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "results"
    / "final_feature_selection"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 데이터 불러오기
# ============================================================

print("\n========================================")
print("1. A+B 최종 데이터 불러오기")
print("========================================")

df = pd.read_csv(
    INPUT_PATH,
    encoding="utf-8-sig",
)

print(f"지역 수: {len(df):,}")
print(f"컬럼 수: {len(df.columns):,}")


# ============================================================
# 전체 분석 후보 변수
# ============================================================

full_features = [
    # ----------------------------------------
    # 고령화
    # ----------------------------------------
    "고령화율_2025",
    "고령화율변화폭_2016_2025",

    # ----------------------------------------
    # 청년 / 인구 변화
    # ----------------------------------------
    "청년비율_2025",
    "청년비율변화폭_2016_2025",
    "인구증감률_2016_2025",
    "청년순이동률_2016_2025",

    # ----------------------------------------
    # 경제
    # ----------------------------------------
    "인구천명당_사업체수_2024",
    "인구천명당_종사자수_2024",
    "사업체당_종사자수_2024",

    # ----------------------------------------
    # 생활 인프라
    # ----------------------------------------
    "노인천명당_병원수",
    "노인천명당_약국수",
    "노인천명당_복지시설수",
    "노인천명당_버스정류장수",
    "노인천명당_철도역수",
]


# ============================================================
# 컬럼 확인
# ============================================================

missing_cols = [
    col
    for col in full_features
    if col not in df.columns
]

if missing_cols:
    raise ValueError(
        "필요한 컬럼이 없습니다: "
        + ", ".join(missing_cols)
    )


# ============================================================
# 높은 상관관계 변수쌍 확인
# ============================================================

print("\n========================================")
print("2. 높은 상관관계 변수 확인")
print("========================================")

corr = (
    df[full_features]
    .corr()
)

high_corr_rows = []

for i in range(len(full_features)):
    for j in range(i + 1, len(full_features)):

        col1 = full_features[i]
        col2 = full_features[j]

        value = corr.loc[
            col1,
            col2,
        ]

        if abs(value) >= 0.8:
            high_corr_rows.append(
                {
                    "변수1": col1,
                    "변수2": col2,
                    "상관계수": value,
                    "절대상관계수": abs(value),
                }
            )


high_corr_df = pd.DataFrame(
    high_corr_rows
)

if not high_corr_df.empty:
    high_corr_df = high_corr_df.sort_values(
        "절대상관계수",
        ascending=False,
    )

print(
    high_corr_df.to_string(
        index=False,
    )
)

high_corr_df.to_csv(
    OUTPUT_DIR / "high_correlation_pairs.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 중복 정보가 큰 변수 제거
# ============================================================

"""
제거 기준

1. 청년비율_2025
   - 고령화율_2025와 r ≈ -0.877
   - 지역 연령구조를 대표하는 변수로 고령화율 유지

2. 인구증감률_2016_2025
   - 청년순이동률_2016_2025와 r ≈ +0.901
   - 본 프로젝트의 청년 유출 질문을 직접 반영하기 위해
     청년순이동률 유지

3. 인구천명당_사업체수_2024
   - 인구천명당_종사자수_2024와 r ≈ +0.837
   - 실제 경제활동 인력 규모를 나타내는
     인구천명당 종사자수 유지
"""

removed_features = [
    "청년비율_2025",
    "인구증감률_2016_2025",
    "인구천명당_사업체수_2024",
]


candidate_features = [
    col
    for col in full_features
    if col not in removed_features
]


print("\n========================================")
print("3. 최종 후보 변수")
print("========================================")

print(
    f"전체 후보 변수: {len(full_features)}개"
)

print(
    f"중복성으로 제외: {len(removed_features)}개"
)

print(
    f"남은 후보 변수: {len(candidate_features)}개"
)

print("\n[제외 변수]")

for col in removed_features:
    print("-", col)

print("\n[후보 변수]")

for col in candidate_features:
    print("-", col)


# ============================================================
# 변수 역할 정리
# ============================================================

feature_roles = pd.DataFrame(
    [
        {
            "변수": "고령화율_2025",
            "영역": "고령화",
            "역할": "현재 고령화 수준",
        },
        {
            "변수": "고령화율변화폭_2016_2025",
            "영역": "고령화",
            "역할": "고령화 진행 속도",
        },
        {
            "변수": "청년비율변화폭_2016_2025",
            "영역": "인구구조",
            "역할": "청년층 비중 변화",
        },
        {
            "변수": "청년순이동률_2016_2025",
            "영역": "인구이동",
            "역할": "청년 순유입·순유출",
        },
        {
            "변수": "인구천명당_종사자수_2024",
            "영역": "경제",
            "역할": "인구 대비 지역 고용 규모",
        },
        {
            "변수": "사업체당_종사자수_2024",
            "영역": "경제",
            "역할": "사업체 평균 고용 규모",
        },
        {
            "변수": "노인천명당_병원수",
            "영역": "의료",
            "역할": "고령인구 대비 병원 공급",
        },
        {
            "변수": "노인천명당_약국수",
            "영역": "의료",
            "역할": "고령인구 대비 약국 공급",
        },
        {
            "변수": "노인천명당_복지시설수",
            "영역": "복지",
            "역할": "고령인구 대비 복지시설 공급",
        },
        {
            "변수": "노인천명당_버스정류장수",
            "영역": "교통",
            "역할": "고령인구 대비 버스정류장 공급",
        },
        {
            "변수": "노인천명당_철도역수",
            "영역": "교통",
            "역할": "고령인구 대비 도시철도 공급",
        },
    ]
)

feature_roles.to_csv(
    OUTPUT_DIR / "feature_roles.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 결측치 확인
# ============================================================

print("\n========================================")
print("4. 후보 변수 결측치")
print("========================================")

missing_summary = (
    df[candidate_features]
    .isna()
    .sum()
    .sort_values(
        ascending=False,
    )
)

print(
    missing_summary
)

missing_summary.to_csv(
    OUTPUT_DIR / "candidate_missing_summary.csv",
    encoding="utf-8-sig",
)


# ============================================================
# 강원 고성군 버스 결측 처리
# ============================================================

"""
강원 고성군 버스정류장 값은
실제 0이 아니라 원자료에서 확인되지 않은 결측값이다.

K-Means는 NaN을 처리할 수 없으므로
강원특별자치도 내 다른 지역의 중앙값을 이용하여 보완한다.

원본 값은 수정하지 않고
K-Means용 데이터에만 적용한다.
"""

cluster_df = df.copy()

goseong_mask = (
    (cluster_df["시도"] == "강원")
    & (cluster_df["지역명"] == "고성군")
)

gangwon_bus_values = cluster_df.loc[
    (cluster_df["시도"] == "강원")
    & (~goseong_mask),
    "노인천명당_버스정류장수",
].dropna()

gangwon_bus_median = (
    gangwon_bus_values.median()
)

print("\n========================================")
print("5. 강원 고성군 버스 결측값 처리")
print("========================================")

print(
    "강원 지역 버스정류장 지표 중앙값:",
    round(
        gangwon_bus_median,
        3,
    ),
)

print("\n보완 전:")

print(
    cluster_df.loc[
        goseong_mask,
        [
            "지역코드",
            "시도",
            "지역명",
            "노인천명당_버스정류장수",
        ],
    ].to_string(
        index=False,
    )
)

cluster_df.loc[
    goseong_mask,
    "노인천명당_버스정류장수",
] = gangwon_bus_median

print("\n보완 후:")

print(
    cluster_df.loc[
        goseong_mask,
        [
            "지역코드",
            "시도",
            "지역명",
            "노인천명당_버스정류장수",
        ],
    ].to_string(
        index=False,
    )
)


# ============================================================
# 왜도 확인
# ============================================================

print("\n========================================")
print("6. 후보 변수 왜도")
print("========================================")

skewness = (
    cluster_df[candidate_features]
    .skew()
    .sort_values(
        key=lambda x: x.abs(),
        ascending=False,
    )
)

skew_df = (
    skewness
    .rename("왜도")
    .reset_index()
    .rename(
        columns={
            "index": "변수",
        }
    )
)

skew_df["절대왜도"] = (
    skew_df["왜도"].abs()
)

print(
    skew_df.to_string(
        index=False,
    )
)

skew_df.to_csv(
    OUTPUT_DIR / "feature_skewness.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# IQR 이상치 확인
# ============================================================

print("\n========================================")
print("7. IQR 이상치 개수")
print("========================================")

outlier_rows = []

for col in candidate_features:

    series = (
        cluster_df[col]
        .dropna()
    )

    q1 = series.quantile(
        0.25
    )

    q3 = series.quantile(
        0.75
    )

    iqr = q3 - q1

    lower = (
        q1
        - 1.5 * iqr
    )

    upper = (
        q3
        + 1.5 * iqr
    )

    outlier_mask = (
        (series < lower)
        | (series > upper)
    )

    count = int(
        outlier_mask.sum()
    )

    outlier_rows.append(
        {
            "변수": col,
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "하한": lower,
            "상한": upper,
            "이상치수": count,
            "이상치비율": (
                count
                / len(series)
                * 100
            ),
        }
    )


outlier_df = pd.DataFrame(
    outlier_rows
)

outlier_df = outlier_df.sort_values(
    "이상치수",
    ascending=False,
)

print(
    outlier_df.to_string(
        index=False,
    )
)

outlier_df.to_csv(
    OUTPUT_DIR / "feature_outlier_summary.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# K-Means용 후보 데이터 생성
# ============================================================

id_cols = [
    "지역코드",
    "시도",
    "지역명",
]

final_candidate_df = cluster_df[
    id_cols
    + candidate_features
].copy()

final_candidate_df["지역코드"] = (
    final_candidate_df["지역코드"]
    .astype(str)
    .str.zfill(5)
)


# ============================================================
# 최종 결측 확인
# ============================================================

remaining_missing = (
    final_candidate_df[
        candidate_features
    ]
    .isna()
    .sum()
)

if remaining_missing.sum() != 0:

    print("\n남은 결측치:")

    print(
        remaining_missing[
            remaining_missing > 0
        ]
    )

    raise ValueError(
        "K-Means 후보 데이터에 "
        "결측치가 남아 있습니다."
    )


# ============================================================
# 후보 데이터 저장
# ============================================================

candidate_path = (
    OUTPUT_DIR
    / "final_feature_candidates.csv"
)

final_candidate_df.to_csv(
    candidate_path,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 전체 / 제외 변수 기록
# ============================================================

selection_rows = []

for col in full_features:

    if col in removed_features:

        status = "제외"

        if col == "청년비율_2025":
            reason = (
                "고령화율_2025와 높은 상관"
            )

        elif col == "인구증감률_2016_2025":
            reason = (
                "청년순이동률_2016_2025와 높은 상관"
            )

        elif col == "인구천명당_사업체수_2024":
            reason = (
                "인구천명당_종사자수_2024와 높은 상관"
            )

        else:
            reason = "중복성"

    else:
        status = "후보"
        reason = "최종 군집분석 후보"

    selection_rows.append(
        {
            "변수": col,
            "상태": status,
            "선정근거": reason,
        }
    )


selection_df = pd.DataFrame(
    selection_rows
)

selection_df.to_csv(
    OUTPUT_DIR / "feature_selection.csv",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 요약 파일
# ============================================================

summary_path = (
    OUTPUT_DIR
    / "feature_selection_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "AGING IMPACT - 최종 변수 선정 준비\n"
    )

    f.write(
        "=" * 60
        + "\n\n"
    )

    f.write(
        f"분석 지역 수: {len(df)}\n"
    )

    f.write(
        f"전체 변수 수: {len(full_features)}\n"
    )

    f.write(
        f"제외 변수 수: {len(removed_features)}\n"
    )

    f.write(
        f"후보 변수 수: {len(candidate_features)}\n\n"
    )

    f.write(
        "[높은 상관관계 변수쌍]\n"
    )

    f.write(
        high_corr_df.to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[제외 변수]\n"
    )

    for col in removed_features:
        f.write(
            f"- {col}\n"
        )

    f.write(
        "\n[최종 후보 변수]\n"
    )

    for col in candidate_features:
        f.write(
            f"- {col}\n"
        )

    f.write(
        "\n[왜도]\n"
    )

    f.write(
        skew_df.to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[IQR 이상치]\n"
    )

    f.write(
        outlier_df.to_string(
            index=False,
        )
    )

    f.write(
        "\n\n[강원 고성군 버스정류장 결측 처리]\n"
    )

    f.write(
        "원자료 부재에 따른 결측값이므로 "
        "0으로 대체하지 않음.\n"
    )

    f.write(
        "K-Means 분석용 데이터에 한하여 "
        "강원 지역 중앙값으로 보완.\n"
    )

    f.write(
        f"보완값: {gangwon_bus_median:.3f}\n"
    )


# ============================================================
# 완료
# ============================================================

print("\n========================================")
print("최종 변수 선정 준비 완료")
print("========================================")

print(
    f"후보 변수 수: "
    f"{len(candidate_features)}"
)

print(
    f"저장 위치:\n{OUTPUT_DIR}"
)

print("\n생성 파일:")

for path in sorted(
    OUTPUT_DIR.iterdir()
):
    print(
        "-",
        path.name,
    )