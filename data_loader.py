"""
통합 데이터 로더

3곳에 분산된 데이터 로딩 로직을 단일 모듈로 통합:
- utils.py → get_data_context()
- pages/1_현황_대시보드.py → load_emissions_data(), load_market_data(), load_allocation_data()
- agent/enhanced_carbon_rag_agent.py → _load_data()
"""

import io
from pathlib import Path
from typing import Optional

import pandas as pd


# 기본 인코딩 폴백 순서
DEFAULT_ENCODINGS = ("cp949", "euc-kr", "utf-8", "utf-8-sig")

# 기본 데이터 디렉토리 (프로젝트 루트 기준)
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"

# CSV 파일명 상수
EMISSIONS_CSV = "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv"
MARKET_CSV = "배출권_거래데이터.csv"
ALLOCATION_CSV = "01. 3차_사전할당_20250613090824.csv"
ENERGY_CSV = "한국에너지공단_산업부문 에너지사용 및 온실가스배출량 통계_20231231.csv"


def load_csv(
    filepath: Path,
    encodings: tuple[str, ...] = DEFAULT_ENCODINGS,
) -> Optional[pd.DataFrame]:
    """CSV 파일을 다양한 인코딩으로 시도하여 로드한다.

    Args:
        filepath: CSV 파일 경로
        encodings: 시도할 인코딩 순서

    Returns:
        DataFrame 또는 로드 실패 시 None
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return None

    for enc in encodings:
        try:
            return pd.read_csv(filepath, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    return None


def load_emissions_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """국가 온실가스 인벤토리 배출량 데이터를 로드한다.

    Returns:
        컬럼: 연도, 총배출량, 에너지, 산업공정, 농업, 폐기물
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    df = load_csv(data_dir / EMISSIONS_CSV)
    if df is None:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    emissions_data = []
    for _, row in df.iterrows():
        try:
            year = int(row.iloc[0])
            if not (1990 <= year <= 2030):
                continue
            total_emission = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
            energy = float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else 0
            industrial = float(row.iloc[45]) if len(row) > 45 and pd.notna(row.iloc[45]) else 0
            agriculture = float(row.iloc[96]) if len(row) > 96 and pd.notna(row.iloc[96]) else 0
            waste = float(row.iloc[147]) if len(row) > 147 and pd.notna(row.iloc[147]) else 0

            emissions_data.append({
                "연도": year,
                "총배출량": total_emission,
                "에너지": energy,
                "산업공정": industrial,
                "농업": agriculture,
                "폐기물": waste,
            })
        except (IndexError, KeyError, ValueError, TypeError):
            continue

    return pd.DataFrame(emissions_data)


def load_market_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """배출권 거래 데이터를 로드한다.

    Returns:
        컬럼: 일자(datetime), 종목명, 시가, 거래량, 거래대금, 연도, 월, 연월
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    df = load_csv(data_dir / MARKET_CSV)
    if df is None:
        return pd.DataFrame()

    kau = df[df["종목명"] == "KAU24"].copy()
    kau["일자"] = pd.to_datetime(kau["일자"])
    kau["시가"] = kau["시가"].str.replace(",", "").astype(float)
    kau["거래량"] = kau["거래량"].str.replace(",", "").astype(float)
    kau["거래대금"] = kau["거래대금"].str.replace(",", "").astype(float)
    kau = kau[kau["시가"] > 0]
    kau["연도"] = kau["일자"].dt.year
    kau["월"] = kau["일자"].dt.month
    kau["연월"] = kau["일자"].dt.strftime("%Y-%m")
    return kau


def load_allocation_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """3차 사전할당 데이터를 로드한다.

    Returns:
        컬럼: 연도, 업체명, 업종, 대상년도별할당량
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    df = load_csv(data_dir / ALLOCATION_CSV)
    if df is None:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    allocation_data = []
    for _, row in df.iterrows():
        try:
            company = row.iloc[2]
            industry = row.iloc[1]
            for year in [2021, 2022, 2023, 2024, 2025]:
                # 컬럼명이 '2021' 또는 '2021년' 일 수 있음
                col_name = None
                if str(year) in df.columns:
                    col_name = str(year)
                elif f"{year}년" in df.columns:
                    col_name = f"{year}년"
                if col_name is not None:
                    alloc = row[col_name]
                    if pd.notna(alloc) and alloc != 0:
                        allocation_data.append({
                            "연도": year,
                            "업체명": company,
                            "업종": industry,
                            "대상년도별할당량": float(alloc),
                        })
        except (IndexError, KeyError):
            continue

    return pd.DataFrame(allocation_data)


def load_combined_analysis_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """에이전트용 통합 분석 DataFrame을 반환한다.

    4개 CSV를 concat하여 '데이터소스' 컬럼을 추가한다.
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    csv_files = [EMISSIONS_CSV, MARKET_CSV, ALLOCATION_CSV, ENERGY_CSV]
    frames = []

    for filename in csv_files:
        df = load_csv(data_dir / filename)
        if df is not None:
            df["데이터소스"] = filename
            frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def get_data_context(data_dir: Optional[Path] = None) -> str:
    """LLM에 전달할 데이터 컨텍스트 문자열을 생성한다."""
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    csv_files = [EMISSIONS_CSV, MARKET_CSV, ENERGY_CSV]
    frames = []

    for filename in csv_files:
        df = load_csv(data_dir / filename)
        if df is not None:
            frames.append(df)

    if not frames:
        return "데이터 파일을 찾거나 로드할 수 없어 데이터 컨텍스트를 생성할 수 없습니다."

    combined = pd.concat(frames, ignore_index=True, sort=False)

    buf = io.StringIO()
    combined.info(buf=buf)
    info_str = buf.getvalue()
    desc_str = combined.describe(include="number").to_string()

    return f"""### 데이터 개요 (Data Overview)
{info_str}

### 주요 수치 데이터 통계 (Key Numerical Statistics)
{desc_str}

### 데이터 샘플 (상위 5개 행)
{combined.head().to_string()}"""
