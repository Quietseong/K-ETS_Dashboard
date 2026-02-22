"""Stage 7: UI 개선/보완 테스트

API 키 미설정 시 에러 핸들링, deprecation 수정, 데이터 범위 정합성을 검증한다.
"""

import pytest
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ===========================================================================
# 7-1: AI 리포트 — API 키 에러 핸들링
# ===========================================================================

class TestAIReportErrorHandling:
    """5_AI_리포트.py에서 API 키 미설정 시 친절한 안내 표시"""

    @pytest.fixture()
    def report_text(self):
        return (PROJECT_ROOT / "pages" / "5_AI_리포트.py").read_text(encoding="utf-8")

    def test_no_bare_openai_constructor(self, report_text):
        """OpenAI() 호출 전에 키 검증이 있어야 한다"""
        # OpenAI(api_key=os.getenv(...)) 가 키 검증 없이 바로 호출되면 안 됨
        lines = report_text.splitlines()
        for i, line in enumerate(lines):
            if "OpenAI(api_key=" in line and "client" in line:
                # 이 라인 위에 키 검증 로직이 있어야 함
                preceding = "\n".join(lines[max(0, i-15):i])
                assert "st.stop()" in preceding or "st.warning" in preceding, \
                    "OpenAI 클라이언트 생성 전에 API 키 검증이 없음"
                break

    def test_has_friendly_warning_message(self, report_text):
        """사용자 친화적 경고 메시지가 있어야 한다"""
        assert "OPENAI_API_KEY" in report_text
        assert "st.warning" in report_text or "st.info" in report_text

    def test_has_setup_instructions(self, report_text):
        """설정 방법 안내가 포함되어야 한다"""
        assert "env.example" in report_text
        assert ".env" in report_text

    def test_graceful_stop_without_key(self, report_text):
        """키 없을 때 st.stop()으로 graceful하게 중단"""
        # st.stop()이 키 검증 블록 안에 있어야 함
        assert "st.stop()" in report_text


# ===========================================================================
# 7-2: AI 챗봇 — API 키 에러 핸들링
# ===========================================================================

class TestAIChatbotErrorHandling:
    """4_AI_챗봇.py에서 API 키 미설정 시 친절한 안내 표시"""

    @pytest.fixture()
    def chatbot_text(self):
        return (PROJECT_ROOT / "pages" / "4_AI_챗봇.py").read_text(encoding="utf-8")

    def test_api_key_precheck(self, chatbot_text):
        """에이전트 호출 전에 API 키 사전 검증이 있어야 한다"""
        # API 키 검증이 에이전트 호출(= 할당)보다 먼저 나와야 함
        key_check_pos = chatbot_text.find("_api_keys_ok")
        if key_check_pos == -1:
            key_check_pos = chatbot_text.find("UPSTAGE_API_KEY")
        # 함수 정의가 아닌 실제 호출 위치 찾기
        agent_call_pos = chatbot_text.find("agent = load_agent()")
        assert agent_call_pos != -1, "load_agent() 호출을 찾을 수 없음"
        assert key_check_pos < agent_call_pos, "API 키 검증이 에이전트 호출보다 먼저 와야 함"

    def test_mentions_required_keys(self, chatbot_text):
        """필요한 API 키 목록이 안내되어야 한다"""
        assert "UPSTAGE_API_KEY" in chatbot_text
        assert "OPENAI_API_KEY" in chatbot_text

    def test_has_setup_instructions(self, chatbot_text):
        """설정 방법 안내가 포함되어야 한다"""
        assert "env.example" in chatbot_text


# ===========================================================================
# 7-3: main.py — deprecation 수정
# ===========================================================================

class TestMainDeprecation:
    """main.py에서 deprecated 파라미터 제거"""

    @pytest.fixture()
    def main_text(self):
        return (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")

    def test_no_use_column_width(self, main_text):
        """use_column_width (deprecated) 파라미터가 없어야 한다"""
        assert "use_column_width" not in main_text


# ===========================================================================
# 7-4: 현황 대시보드 — 데이터 범위 정합성
# ===========================================================================

class TestDashboardDataRange:
    """1_현황_대시보드.py 샘플 데이터가 기본 필터(2025년)를 커버"""

    @pytest.fixture()
    def dashboard_text(self):
        return (PROJECT_ROOT / "pages" / "1_현황_대시보드.py").read_text(encoding="utf-8")

    def test_gauge_data_covers_2025(self, dashboard_text):
        """게이지 데이터가 2025년을 포함해야 한다"""
        # load_gauge_data()의 range가 2026을 포함해야 2025년 데이터 생성
        match = re.search(r"def load_gauge_data.*?return", dashboard_text, re.DOTALL)
        assert match, "load_gauge_data 함수를 찾을 수 없음"
        func_body = match.group()
        # range(2020, 2026) 형태로 2025 포함
        assert "2026" in func_body, "게이지 데이터 range가 2025년을 포함하지 않음"

    def test_timeseries_data_covers_2025(self, dashboard_text):
        """시계열 데이터가 2025년을 포함해야 한다"""
        match = re.search(r"def load_timeseries_data.*?return", dashboard_text, re.DOTALL)
        assert match, "load_timeseries_data 함수를 찾을 수 없음"
        func_body = match.group()
        assert "2026" in func_body, "시계열 데이터 range가 2025년을 포함하지 않음"

    def test_default_year_is_2025(self, dashboard_text):
        """기본 선택 연도가 2025인지 확인"""
        assert "value=2025" in dashboard_text
