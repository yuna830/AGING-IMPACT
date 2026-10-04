from pathlib import Path
import pandas as pd


# ============================================================
# 기본 경로
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"

POPULATION_DIR = RAW_DIR / "population"
MIGRATION_DIR = RAW_DIR / "migration"
BUSINESS_DIR = RAW_DIR / "business"
EMPLOYEE_DIR = RAW_DIR / "employee"


# ============================================================
# CSV 안전하게 읽기
# ============================================================

def read_csv_auto(file_path: Path):
    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp949",
        "euc-kr",
    ]

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                low_memory=False,
            )

            return df, encoding

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"CSV 인코딩을 확인할 수 없습니다: {file_path}"
    )


# ============================================================
# CSV 파일 확인
# ============================================================

def inspect_csv_folder(folder_path: Path, title: str):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    files = sorted(folder_path.glob("*.csv"))

    if not files:
        print("CSV 파일이 없습니다.")
        return

    for file_path in files:
        print()
        print("-" * 80)
        print(f"파일명: {file_path.name}")

        try:
            df, encoding = read_csv_auto(file_path)

            print(f"인코딩: {encoding}")
            print(f"행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")

            print()
            print("[컬럼 목록]")

            for index, column in enumerate(
                df.columns,
                start=1,
            ):
                print(
                    f"{index:>3}. {column}"
                )

            print()
            print("[상위 5행]")

            print(
                df.head().to_string()
            )

        except Exception as e:
            print(
                f"읽기 실패: {e}"
            )


# ============================================================
# Excel 파일 확인
# ============================================================

def inspect_excel_folder(folder_path: Path, title: str):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    files = sorted(folder_path.glob("*.xlsx"))

    if not files:
        print("XLSX 파일이 없습니다.")
        return

    for file_path in files:
        print()
        print("-" * 80)
        print(f"파일명: {file_path.name}")

        try:
            excel = pd.ExcelFile(file_path)

            print(
                f"시트 목록: {excel.sheet_names}"
            )

            for sheet_name in excel.sheet_names:
                print()
                print(
                    f"[시트: {sheet_name}]"
                )

                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                )

                print(
                    f"행 수: {len(df)}"
                )

                print(
                    f"열 수: {len(df.columns)}"
                )

                print()
                print("[컬럼 목록]")

                for index, column in enumerate(
                    df.columns,
                    start=1,
                ):
                    print(
                        f"{index:>3}. {column}"
                    )

                print()
                print("[상위 5행]")

                print(
                    df.head().to_string()
                )

        except Exception as e:
            print(
                f"읽기 실패: {e}"
            )


# ============================================================
# 메인
# ============================================================

def main():
    print()
    print("AGING IMPACT")
    print("A 담당 원자료 구조 확인")
    print()

    inspect_csv_folder(
        POPULATION_DIR,
        "1. 주민등록 인구 데이터",
    )

    inspect_csv_folder(
        MIGRATION_DIR,
        "2. 인구 이동 데이터",
    )

    inspect_excel_folder(
        BUSINESS_DIR,
        "3. 사업체 데이터",
    )

    inspect_excel_folder(
        EMPLOYEE_DIR,
        "4. 종사자 데이터",
    )


if __name__ == "__main__":
    main()