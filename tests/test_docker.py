"""Stage 6: Docker 컨테이너화 테스트

Docker 설정 파일의 구조와 정합성을 검증한다.
"""

import pytest
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# conftest.py에서 PROJECT_ROOT 재사용
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ===========================================================================
# 6-1: requirements.txt 정리
# ===========================================================================

class TestRequirementsCleaned:
    """미사용 패키지가 제거되었는지 확인"""

    REMOVED_PACKAGES = [
        "dash",
        "dash-bootstrap-components",
        "sentence-transformers",
        "faiss-cpu",
        "chromadb",
        "langchain-experimental",
        "langchain-community",
        "langchain-anthropic",
        "langchain-elasticsearch",
        "langchain-cohere",
        "langchain-milvus",
        "langchain-google-genai",
        "langchain-huggingface",
        "langchain-azure-ai",
        "langchain-teddynote",
        "anthropic",
        "cohere",
    ]

    @pytest.fixture()
    def requirements_text(self):
        return (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")

    @pytest.mark.parametrize("pkg", REMOVED_PACKAGES)
    def test_unused_package_removed(self, requirements_text, pkg):
        """미사용 패키지가 requirements.txt에 없어야 한다"""
        # 주석이 아닌 실제 패키지 라인에서만 검사
        for line in requirements_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            # 패키지명 추출 (>=, ==, ~= 등 버전 지정자 앞 부분)
            pkg_name = re.split(r"[>=<~!\[]", stripped)[0].strip().lower()
            assert pkg_name != pkg.lower(), f"{pkg}가 여전히 requirements.txt에 존재"


class TestRequiredPackagesPresent:
    """실제 사용 중인 패키지가 포함되어 있는지 확인"""

    REQUIRED_PACKAGES = [
        "streamlit",
        "pandas",
        "plotly",
        "numpy",
        "fastapi",
        "uvicorn",
        "pydantic",
        "langchain",
        "langchain-core",
        "langchain-openai",
        "langchain-text-splitters",
        "langchain-upstage",
        "langchain-pinecone",
        "pinecone-client",
        "openai",
        "matplotlib",
        "seaborn",
        "requests",
        "python-dotenv",
        "pillow",
        "pymupdf",
        "pdfplumber",
        "python-docx",
        "reportlab",
    ]

    @pytest.fixture()
    def installed_packages(self):
        """requirements.txt에서 패키지명 목록 추출"""
        text = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
        pkgs = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            pkg_name = re.split(r"[>=<~!\[]", stripped)[0].strip().lower()
            pkgs.append(pkg_name)
        return pkgs

    @pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
    def test_required_package_present(self, installed_packages, pkg):
        """필수 패키지가 requirements.txt에 존재해야 한다"""
        assert pkg.lower() in installed_packages, f"{pkg}가 requirements.txt에 없음"


class TestRequirementsDev:
    """개발 의존성 파일 검증"""

    def test_dev_requirements_exists(self):
        assert (PROJECT_ROOT / "requirements-dev.txt").exists()

    def test_dev_inherits_production(self):
        """requirements-dev.txt가 requirements.txt를 include하는지 확인"""
        text = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        assert "-r requirements.txt" in text

    def test_dev_has_pytest(self):
        text = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        assert "pytest" in text.lower()


# ===========================================================================
# 6-2: Dockerfile 검증
# ===========================================================================

class TestDockerfile:
    """Dockerfile 구조 검증"""

    @pytest.fixture()
    def dockerfile_text(self):
        return (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_base_image_python_slim(self, dockerfile_text):
        """경량 Python 베이스 이미지 사용"""
        assert re.search(r"FROM\s+python:3\.\d+-slim", dockerfile_text)

    def test_nanum_font_installed(self, dockerfile_text):
        """한글 폰트(나눔) 설치"""
        assert "fonts-nanum" in dockerfile_text

    def test_matplotlib_backend(self, dockerfile_text):
        """headless matplotlib 백엔드 설정"""
        assert "MPLBACKEND=Agg" in dockerfile_text

    def test_requirements_copy_before_source(self, dockerfile_text):
        """requirements.txt를 먼저 복사하여 Docker 캐시 활용"""
        req_pos = dockerfile_text.find("COPY requirements.txt")
        source_pos = dockerfile_text.find("COPY agent/")
        assert req_pos != -1 and source_pos != -1
        assert req_pos < source_pos, "requirements.txt가 소스코드보다 먼저 COPY되어야 함"

    def test_pip_no_cache(self, dockerfile_text):
        """pip --no-cache-dir로 이미지 경량화"""
        assert "--no-cache-dir" in dockerfile_text

    def test_exposes_both_ports(self, dockerfile_text):
        """Streamlit(8501)과 FastAPI(8000) 포트 노출"""
        assert "8501" in dockerfile_text
        assert "8000" in dockerfile_text

    def test_source_files_copied(self, dockerfile_text):
        """핵심 소스 파일이 COPY되는지 확인"""
        for item in ["agent/", "pages/", "prompts/", "data/", "docs/", "main.py", "app_api.py", "data_loader.py", "utils.py"]:
            assert item in dockerfile_text, f"{item}이 Dockerfile에서 COPY되지 않음"

    def test_no_env_file_copied(self, dockerfile_text):
        """.env 파일이 이미지에 포함되지 않아야 함"""
        # COPY .env 같은 패턴이 없어야 함
        assert not re.search(r"COPY\s+\.env\s", dockerfile_text)


# ===========================================================================
# 6-3: docker-compose.yml 검증
# ===========================================================================

class TestDockerCompose:
    """docker-compose.yml 구조 검증"""

    @pytest.fixture()
    def compose_text(self):
        return (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    def test_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_streamlit_service_defined(self, compose_text):
        assert "streamlit:" in compose_text

    def test_fastapi_service_defined(self, compose_text):
        assert "fastapi:" in compose_text

    def test_streamlit_port_mapping(self, compose_text):
        """Streamlit 8501 포트 매핑"""
        assert '"8501:8501"' in compose_text or "8501:8501" in compose_text

    def test_fastapi_port_mapping(self, compose_text):
        """FastAPI 8000 포트 매핑"""
        assert '"8000:8000"' in compose_text or "8000:8000" in compose_text

    def test_env_file_configured(self, compose_text):
        """env_file로 환경변수 전달 (optional)"""
        assert "env_file" in compose_text
        assert ".env" in compose_text
        # .env 없이도 기동 가능하도록 required: false
        assert "required: false" in compose_text

    def test_healthcheck_defined(self, compose_text):
        """헬스체크 설정"""
        assert "healthcheck" in compose_text

    def test_streamlit_headless(self, compose_text):
        """Streamlit headless 모드"""
        assert "headless" in compose_text

    def test_streamlit_command(self, compose_text):
        """Streamlit 실행 커맨드"""
        assert "streamlit run main.py" in compose_text

    def test_fastapi_command(self, compose_text):
        """FastAPI 실행 커맨드"""
        assert "python app_api.py" in compose_text


# ===========================================================================
# 6-4: .dockerignore 검증
# ===========================================================================

class TestDockerignore:
    """.dockerignore 파일 검증"""

    MUST_IGNORE = [
        "venv/",
        ".git/",
        "__pycache__/",
        ".env",
        "tests/",
        ".claude/",
    ]

    @pytest.fixture()
    def dockerignore_text(self):
        return (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

    def test_dockerignore_exists(self):
        assert (PROJECT_ROOT / ".dockerignore").exists()

    @pytest.mark.parametrize("pattern", MUST_IGNORE)
    def test_must_ignore_pattern(self, dockerignore_text, pattern):
        """필수 제외 패턴이 .dockerignore에 존재해야 함"""
        assert pattern in dockerignore_text, f"{pattern}이 .dockerignore에 없음"

    def test_env_file_ignored(self, dockerignore_text):
        """.env가 이미지에 포함되지 않도록 설정"""
        assert ".env" in dockerignore_text
