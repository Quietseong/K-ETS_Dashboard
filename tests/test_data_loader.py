"""Stage 2: 데이터 레이어 통합 검증"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data_loader import (
    load_csv,
    load_emissions_data,
    load_market_data,
    load_allocation_data,
    load_combined_analysis_data,
    get_data_context,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class TestLoadCsv:
    """load_csv 인코딩 폴백 테스트"""

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_csv(tmp_path / "nonexistent.csv")
        assert result is None

    def test_loads_utf8_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.to_csv(csv_path, index=False, encoding="utf-8")
        result = load_csv(csv_path)
        assert result is not None
        assert len(result) == 2
        assert list(result.columns) == ["a", "b"]


class TestLoadEmissionsData:
    """load_emissions_data 반환 구조 검증"""

    @pytest.mark.skipif(
        not (DATA_DIR / "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv").exists(),
        reason="배출량 CSV 파일 없음"
    )
    def test_returns_dataframe_with_expected_columns(self):
        df = load_emissions_data(DATA_DIR)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        expected_cols = {"연도", "총배출량", "에너지", "산업공정", "농업", "폐기물"}
        assert expected_cols.issubset(set(df.columns))

    @pytest.mark.skipif(
        not (DATA_DIR / "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv").exists(),
        reason="배출량 CSV 파일 없음"
    )
    def test_year_range(self):
        df = load_emissions_data(DATA_DIR)
        assert df["연도"].min() >= 1990
        assert df["연도"].max() <= 2030

    def test_returns_empty_for_missing_dir(self, tmp_path):
        df = load_emissions_data(tmp_path / "nope")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestLoadMarketData:
    """load_market_data 반환 구조 검증"""

    @pytest.mark.skipif(
        not (DATA_DIR / "배출권_거래데이터.csv").exists(),
        reason="시장 CSV 파일 없음"
    )
    def test_returns_dataframe_with_datetime(self):
        df = load_market_data(DATA_DIR)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert pd.api.types.is_datetime64_any_dtype(df["일자"])
        assert "시가" in df.columns
        assert "거래량" in df.columns

    def test_returns_empty_for_missing_dir(self, tmp_path):
        df = load_market_data(tmp_path / "nope")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestLoadAllocationData:
    """load_allocation_data 반환 구조 검증"""

    @pytest.mark.skipif(
        not (DATA_DIR / "01. 3차_사전할당_20250613090824.csv").exists(),
        reason="할당량 CSV 파일 없음"
    )
    def test_returns_dataframe_with_expected_columns(self):
        df = load_allocation_data(DATA_DIR)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        expected_cols = {"연도", "업체명", "업종", "대상년도별할당량"}
        assert expected_cols.issubset(set(df.columns))

    def test_returns_empty_for_missing_dir(self, tmp_path):
        df = load_allocation_data(tmp_path / "nope")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestLoadCombinedAnalysisData:
    """load_combined_analysis_data 검증"""

    def test_returns_empty_for_missing_dir(self, tmp_path):
        df = load_combined_analysis_data(tmp_path / "nope")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.skipif(
        not (DATA_DIR / "배출권_거래데이터.csv").exists(),
        reason="데이터 파일 없음"
    )
    def test_has_datasource_column(self):
        df = load_combined_analysis_data(DATA_DIR)
        assert "데이터소스" in df.columns


class TestGetDataContext:
    """get_data_context 검증"""

    def test_returns_string(self):
        result = get_data_context(DATA_DIR)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_fallback_for_missing_dir(self, tmp_path):
        result = get_data_context(tmp_path / "nope")
        assert "데이터 파일" in result


class TestConsumerIntegration:
    """소비자 코드에서 기존 로컬 load 함수가 제거되었는지 확인"""

    def test_dashboard_no_local_load_functions(self):
        path = PROJECT_ROOT / "pages" / "1_현황_대시보드.py"
        content = path.read_text(encoding="utf-8")
        # 로컬 함수 정의가 없어야 함
        assert "def load_emissions_data" not in content
        assert "def load_market_data" not in content
        assert "def load_allocation_data" not in content
        # data_loader import가 있어야 함
        assert "from data_loader import" in content

    def test_utils_no_local_get_data_context(self):
        path = PROJECT_ROOT / "utils.py"
        content = path.read_text(encoding="utf-8")
        # 함수 정의가 아닌 import만 있어야 함
        assert "def get_data_context" not in content
        assert "from data_loader import get_data_context" in content

    def test_agent_uses_data_loader(self):
        path = PROJECT_ROOT / "agent" / "enhanced_carbon_rag_agent.py"
        content = path.read_text(encoding="utf-8")
        assert "from data_loader import load_combined_analysis_data" in content
