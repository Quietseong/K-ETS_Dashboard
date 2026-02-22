"""공통 테스트 fixture"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def project_root():
    """프로젝트 루트 경로"""
    return PROJECT_ROOT


@pytest.fixture
def sample_emissions_df():
    """테스트용 배출량 DataFrame"""
    return pd.DataFrame({
        "연도": [2019, 2020, 2021],
        "총배출량": [701000.0, 656000.0, 676648.0],
        "에너지": [490000.0, 459000.0, 473000.0],
        "산업공정": [105000.0, 98000.0, 101000.0],
        "농업": [70000.0, 65000.0, 67000.0],
        "폐기물": [36000.0, 34000.0, 35648.0],
    })


@pytest.fixture
def sample_market_df():
    """테스트용 시장 DataFrame"""
    return pd.DataFrame({
        "일자": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        "종목명": ["KAU24", "KAU24", "KAU24"],
        "시가": [8500.0, 8600.0, 8770.0],
        "거래량": [1000.0, 1500.0, 2000.0],
        "거래대금": [8500000.0, 12900000.0, 17540000.0],
    })


@pytest.fixture
def mock_llm():
    """테스트용 Mock LLM"""
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="테스트 응답입니다.")
    return llm
