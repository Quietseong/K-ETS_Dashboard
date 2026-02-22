"""Stage 3: main.py 분리 (Streamlit/FastAPI) 검증"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# 1. app_api.py 존재 및 구조 검증
# ============================================================

class TestAppApiExists:
    """app_api.py 파일 존재 및 기본 구조 확인"""

    def test_app_api_file_exists(self):
        assert (PROJECT_ROOT / "app_api.py").exists(), "app_api.py 파일이 없습니다"

    def test_app_api_is_valid_python(self):
        source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")
        ast.parse(source)  # 문법 오류 시 SyntaxError 발생


class TestAppApiImports:
    """app_api.py에 필요한 import가 있는지 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")

    def test_imports_fastapi(self):
        assert "from fastapi import" in self.source

    def test_imports_cors(self):
        assert "CORSMiddleware" in self.source

    def test_imports_pydantic(self):
        assert "from pydantic import" in self.source

    def test_imports_streaming_response(self):
        assert "StreamingResponse" in self.source

    def test_imports_utils(self):
        assert "from utils import create_docx, create_pdf" in self.source

    def test_imports_agents(self):
        assert "ReportTemplateAgent" in self.source
        assert "EnhancedCarbonRAGAgent" in self.source


class TestAppApiFastAppInstance:
    """FastAPI 앱 인스턴스 및 CORS 설정 검증"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")

    def test_fastapi_app_created(self):
        assert "app = FastAPI(" in self.source

    def test_cors_uses_env_variable(self):
        assert 'CORS_ORIGINS' in self.source

    def test_cors_middleware_added(self):
        assert "app.add_middleware" in self.source


class TestAppApiPydanticModels:
    """Pydantic 모델 정의 존재 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")

    def test_topic_request_model(self):
        assert "class TopicRequest(BaseModel):" in self.source

    def test_outline_response_model(self):
        assert "class OutlineResponse(BaseModel):" in self.source

    def test_report_request_model(self):
        assert "class ReportRequest(BaseModel):" in self.source

    def test_report_download_request_model(self):
        assert "class ReportDownloadRequest(BaseModel):" in self.source


class TestAppApiEndpoints:
    """4개 엔드포인트 존재 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")

    def test_root_endpoint(self):
        assert '@app.get("/")' in self.source or "@app.get(\"/\"" in self.source

    def test_generate_outline_endpoint(self):
        assert "/generate-outline-from-topic" in self.source

    def test_generate_report_endpoint(self):
        assert "/generate-report" in self.source

    def test_download_report_endpoint(self):
        assert "/download-report" in self.source


class TestAppApiStreamer:
    """SSE 스트리밍 함수 존재 확인"""

    def test_report_streamer_exists(self):
        source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")
        assert "async def report_streamer" in source or "def report_streamer" in source


class TestAppApiUvicorn:
    """Uvicorn 실행 설정 확인"""

    def test_uvicorn_references_app_api(self):
        source = (PROJECT_ROOT / "app_api.py").read_text(encoding="utf-8")
        assert '"app_api:app"' in source or "'app_api:app'" in source


# ============================================================
# 2. main.py에서 FastAPI 코드 제거 확인
# ============================================================

class TestMainPyCleaned:
    """main.py에서 FastAPI 관련 코드가 제거되었는지 확인"""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")

    def test_no_fastapi_import(self):
        assert "from fastapi import" not in self.source
        assert "from fastapi." not in self.source

    def test_no_pydantic_import(self):
        assert "from pydantic import" not in self.source

    def test_no_asyncio_import(self):
        assert "import asyncio" not in self.source

    def test_no_sys_import(self):
        assert "import sys" not in self.source

    def test_no_uvicorn(self):
        assert "uvicorn" not in self.source

    def test_no_create_docx_import(self):
        assert "from utils import create_docx" not in self.source

    def test_no_fastapi_app_instance(self):
        assert "app = FastAPI(" not in self.source

    def test_no_cors_middleware(self):
        assert "CORSMiddleware" not in self.source

    def test_no_fastapi_endpoints(self):
        assert "@app.get" not in self.source
        assert "@app.post" not in self.source

    def test_no_react_iframe_js(self):
        # React iframe JavaScript (window.addEventListener message) 제거 확인
        assert "event.origin" not in self.source
        assert "TOGGLE_SIDEBAR" not in self.source
        assert "localhost:3000" not in self.source


class TestMainPyStillWorks:
    """main.py가 여전히 유효한 Python 파일인지 확인"""

    def test_main_is_valid_python(self):
        source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)

    def test_main_has_streamlit_import(self):
        source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
        assert "import streamlit as st" in self.source if hasattr(self, 'source') else "import streamlit as st" in source

    def test_main_has_page_config(self):
        source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
        assert "st.set_page_config" in source

    def test_main_has_esg_ranking(self):
        source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
        assert "ESG" in source


# ============================================================
# 3. env.example 업데이트 확인
# ============================================================

class TestEnvExample:
    """env.example에 CORS_ORIGINS 추가 확인"""

    def test_cors_origins_in_env_example(self):
        content = (PROJECT_ROOT / "env.example").read_text(encoding="utf-8")
        assert "CORS_ORIGINS" in content


# ============================================================
# 4. 실행 스크립트 업데이트 확인
# ============================================================

class TestRunScripts:
    """실행 스크립트에 FastAPI 서버 시작 명령 포함 확인"""

    def test_bat_has_fastapi_start(self):
        content = (PROJECT_ROOT / "run_dashboard.bat").read_text(encoding="utf-8")
        assert "app_api" in content

    def test_ps1_has_fastapi_start(self):
        content = (PROJECT_ROOT / "run_dashboard.ps1").read_text(encoding="utf-8")
        assert "app_api" in content
