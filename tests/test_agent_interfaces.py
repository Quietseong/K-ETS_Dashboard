"""Stage 4: 에이전트 인터페이스 정리 검증"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# 1. agent/types.py 존재 및 AgentResponse 정의 검증
# ============================================================

class TestAgentTypesModule:
    """agent/types.py 파일 존재 및 AgentResponse 정의 확인"""

    def test_types_file_exists(self):
        assert (PROJECT_ROOT / "agent" / "types.py").exists()

    def test_types_is_valid_python(self):
        source = (PROJECT_ROOT / "agent" / "types.py").read_text(encoding="utf-8")
        ast.parse(source)

    def test_agent_response_importable(self):
        from agent.types import AgentResponse
        assert AgentResponse is not None

    def test_agent_response_is_namedtuple(self):
        from agent.types import AgentResponse
        # NamedTuple은 tuple의 서브클래스
        assert issubclass(AgentResponse, tuple)

    def test_agent_response_has_required_fields(self):
        from agent.types import AgentResponse
        fields = AgentResponse._fields
        assert "answer" in fields
        assert "visualization" in fields
        assert "table_data" in fields
        assert "figure" in fields

    def test_agent_response_field_count(self):
        from agent.types import AgentResponse
        assert len(AgentResponse._fields) == 4


class TestAgentResponseBehavior:
    """AgentResponse의 동작 검증"""

    def test_construct_with_positional_args(self):
        from agent.types import AgentResponse
        resp = AgentResponse("답변", "plot_generated", None, None)
        assert resp.answer == "답변"
        assert resp.visualization == "plot_generated"

    def test_construct_with_keyword_args(self):
        from agent.types import AgentResponse
        resp = AgentResponse(answer="답변", visualization=None, table_data=None, figure=None)
        assert resp.answer == "답변"

    def test_construct_with_defaults(self):
        from agent.types import AgentResponse
        resp = AgentResponse("답변만")
        assert resp.answer == "답변만"
        assert resp.visualization is None
        assert resp.table_data is None
        assert resp.figure is None

    def test_tuple_unpacking_compatibility(self):
        """기존 tuple unpacking 패턴과 호환되는지 확인"""
        from agent.types import AgentResponse
        resp = AgentResponse("답변", "plot_generated", None, None)
        answer, viz, table, fig = resp
        assert answer == "답변"
        assert viz == "plot_generated"
        assert table is None
        assert fig is None

    def test_index_access_compatibility(self):
        """기존 인덱스 접근 패턴과 호환되는지 확인"""
        from agent.types import AgentResponse
        resp = AgentResponse("답변", "plot_generated", None, None)
        assert resp[0] == "답변"
        assert resp[1] == "plot_generated"


# ============================================================
# 2. enhanced_carbon_rag_agent.py에서 AgentResponse 사용 확인
# ============================================================

class TestEnhancedAgentUsesAgentResponse:
    """enhanced_carbon_rag_agent.py가 AgentResponse를 반환하는지 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "agent" / "enhanced_carbon_rag_agent.py").read_text(encoding="utf-8")

    def test_imports_agent_response(self):
        assert "from agent.types import AgentResponse" in self.source

    def test_ask_return_type_hint(self):
        assert "-> AgentResponse:" in self.source

    def test_returns_agent_response_instances(self):
        assert "return AgentResponse(" in self.source

    def test_no_bare_tuple_returns_in_ask(self):
        """ask() 메서드 내에서 bare tuple return이 없는지 확인"""
        tree = ast.parse(self.source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "ask":
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        # Return 값이 Tuple 리터럴이면 안 됨
                        assert not isinstance(child.value, ast.Tuple), \
                            "ask() 내에서 bare tuple return이 발견되었습니다"


# ============================================================
# 3. 5_AI_리포트.py 수정 확인
# ============================================================

class TestAIReportPageFixed:
    """5_AI_리포트.py deprecated import 수정 및 set_page_config 제거 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "pages" / "5_AI_리포트.py").read_text(encoding="utf-8")

    def test_no_set_page_config(self):
        assert "st.set_page_config" not in self.source

    def test_no_deprecated_text_splitter_import(self):
        assert "from langchain.text_splitter" not in self.source

    def test_no_deprecated_embeddings_import(self):
        assert "from langchain.embeddings" not in self.source

    def test_no_deprecated_chat_models_import(self):
        assert "from langchain.chat_models" not in self.source

    def test_uses_langchain_text_splitters(self):
        assert "from langchain_text_splitters import" in self.source

    def test_uses_langchain_openai_embeddings(self):
        assert "OpenAIEmbeddings" in self.source
        assert "langchain_openai" in self.source

    def test_uses_langchain_openai_chat(self):
        assert "ChatOpenAI" in self.source
        assert "langchain_openai" in self.source

    def test_is_valid_python(self):
        ast.parse(self.source)


# ============================================================
# 4. app_api.py에서 속성 접근 사용 확인
# ============================================================

class TestAppApiUsesAttributeAccess:
    """app_api.py가 AgentResponse 속성 접근을 사용하는지 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")

    def test_no_index_access_on_agent_response(self):
        """agent_response[0] 같은 인덱스 접근이 없는지 확인"""
        assert "agent_response[0]" not in self.source

    def test_uses_attribute_access(self):
        """agent_response.answer 속성 접근을 사용하는지 확인"""
        assert "agent_response.answer" in self.source

    def test_is_valid_python(self):
        ast.parse(self.source)


# ============================================================
# 5. pages/4_AI_챗봇.py 호환성 확인
# ============================================================

class TestChatbotPageCompatibility:
    """4_AI_챗봇.py가 여전히 유효한 Python인지 확인"""

    def test_is_valid_python(self):
        source = (PROJECT_ROOT / "pages" / "4_AI_챗봇.py").read_text(encoding="utf-8")
        ast.parse(source)

    def test_uses_tuple_unpacking(self):
        """tuple unpacking 패턴이 유지되는지 확인 (AgentResponse NamedTuple과 호환)"""
        source = (PROJECT_ROOT / "pages" / "4_AI_챗봇.py").read_text(encoding="utf-8")
        assert "agent.ask(" in source
