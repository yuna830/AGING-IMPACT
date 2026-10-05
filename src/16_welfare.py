import pdfplumber
import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "infrastructure"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

pdf_path = RAW_DIR / "2026년_노인복지시설현황(1).pdf"

# 시도명 표준화
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

# 각 표의 PDF 인덱스 범위
TABLES = {
    "주거복지시설수": range(27, 37),
    "의료복지시설수": range(37, 47),
    "여가복지시설수": range(47, 57),
    "재가복지시설수": range(57, 67),
    "노인일자리지원기관수": range(67, 77),
    "학대피해노인쉼터수": range(77, 87),
}


def parse_table(pdf, pages, value_name):

    rows = []
    current_sido = None

    # 지역명 / 65세 이상 인구 / 시설수
    #
    # 예:
    # 종로구 30,664 1 ...
    # 수원시 249,xxx 12 ...
    #
    # 지역명에는 숫자가 들어가지 않는다는 점을 이용
    pattern = re.compile(
        r"^([가-힣·]+(?:시|군|구))\s+([\d,]+)\s+([\d,]+)"
    )

    # 시도 합계 행
    sido_pattern = re.compile(
        r"^(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*합계\s*([\d,]+)\s+([\d,]+)"
    )

    for page_num in pages:

        page = pdf.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        for line in text.splitlines():

            line = line.strip()

            # --------------------------------
            # 시도 합계 행
            # --------------------------------
            sido_match = sido_pattern.match(line)

            if sido_match:

                sido_short = sido_match.group(1)

                current_sido = SIDO_MAP[sido_short]

                continue

            # --------------------------------
            # 일반 시군구 행
            # --------------------------------
            match = pattern.match(line)

            if not match:
                continue

            if current_sido is None:
                continue

            region = match.group(1)

            population = int(
                match.group(2).replace(",", "")
            )

            facility_count = int(
                match.group(3).replace(",", "")
            )

            rows.append({
                "시도명": current_sido,
                "시군구명": region,
                "65세이상인구": population,
                value_name: facility_count,
            })

    return pd.DataFrame(rows)


with pdfplumber.open(pdf_path) as pdf:

    dfs = []

    for value_name, pages in TABLES.items():

        df = parse_table(
            pdf,
            pages,
            value_name
        )

        print(
            value_name,
            "추출 지역 수:",
            len(df)
        )

        dfs.append(df)


# -----------------------------------
# 첫 번째 표를 기준으로 병합
# -----------------------------------

result = dfs[0]

for df in dfs[1:]:

    # 인구는 첫 번째 표의 값을 사용
    df = df.drop(
        columns=["65세이상인구"]
    )

    result = result.merge(
        df,
        on=["시도명", "시군구명"],
        how="outer"
    )


# 시설이 없는 지역은 0
facility_cols = list(TABLES.keys())

result[facility_cols] = (
    result[facility_cols]
    .fillna(0)
    .astype(int)
)


# -----------------------------------
# 전체 복지시설 수
# -----------------------------------

result["노인복지시설수"] = (
    result[facility_cols].sum(axis=1)
)


# 정렬
result = result.sort_values(
    ["시도명", "시군구명"]
).reset_index(drop=True)


# -----------------------------------
# 저장
# -----------------------------------

output_path = (
    PROCESSED_DIR /
    "welfare_by_region.csv"
)

result.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)


# -----------------------------------
# 확인
# -----------------------------------

print("\n===== 최종 결과 =====")
print("지역 수:", len(result))

print("\n65세 이상 인구 결측:")
print(result["65세이상인구"].isna().sum())

print("\n시설별 총합:")
print(result[facility_cols].sum())

print(
    "\n노인복지시설 총합:",
    result["노인복지시설수"].sum()
)

print("\n===== 샘플 =====")
print(result.head(30))

print("\n저장 완료:")
print(output_path)

print("\n===== 노인일자리지원기관 시도별 합계 =====")

print(
    result.groupby("시도명")["노인일자리지원기관수"]
    .sum()
    .sort_index()
)