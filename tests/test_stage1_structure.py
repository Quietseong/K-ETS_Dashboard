"""Stage 1: 환경 정리 + 테스트 인프라 검증"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDeletedFiles:
    """삭제된 파일이 실제로 없는지 확인"""

    @pytest.mark.parametrize("filename", [
        "chatbot_app.py",
        "check_data.py",
        "check_data_structure.py",
        "debug_code_generation.py",
        "debug_treemap.py",
        "embedding_manifest.json",
        "package-lock.json",
        "README_FRONTEND.md",
    ])
    def test_file_deleted(self, filename):
        assert not (PROJECT_ROOT / filename).exists(), f"{filename} 가 여전히 존재합니다"

    def test_src_directory_deleted(self):
        assert not (PROJECT_ROOT / "src").exists(), "src/ 디렉토리가 여전히 존재합니다"


class TestNewFiles:
    """신규 파일 존재 확인"""

    def test_pyproject_toml_exists(self):
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    def test_agent_init_exists(self):
        assert (PROJECT_ROOT / "agent" / "__init__.py").exists()

    def test_tests_init_exists(self):
        assert (PROJECT_ROOT / "tests" / "__init__.py").exists()

    def test_tests_conftest_exists(self):
        assert (PROJECT_ROOT / "tests" / "conftest.py").exists()


class TestSysPathRemoval:
    """sys.path.append 잔재가 없는지 확인"""

    FILES_TO_CHECK = [
        "agent/enhanced_carbon_rag_agent.py",
        "agent/doc_agent.py",
        "pages/1_현황_대시보드.py",
        "pages/2_구매_전략.py",
        "pages/3_프로그램_정보.py",
        "pages/4_AI_챗봇.py",
        "pages/5_AI_리포트.py",
    ]

    @pytest.mark.parametrize("filepath", FILES_TO_CHECK)
    def test_no_sys_path_append(self, filepath):
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            pytest.skip(f"{filepath} 파일 없음")
        content = full_path.read_text(encoding="utf-8")
        assert "sys.path.append" not in content, f"{filepath}에 sys.path.append 잔재"
        assert "sys.path.insert" not in content, f"{filepath}에 sys.path.insert 잔재"


class TestDocAgentFix:
    """doc_agent.py에서 chatbot_app 참조 제거 확인"""

    def test_no_chatbot_app_reference(self):
        path = PROJECT_ROOT / "agent" / "doc_agent.py"
        content = path.read_text(encoding="utf-8")
        assert "chatbot_app" not in content, "doc_agent.py에 chatbot_app 참조 잔재"

    def test_pyproject_toml_in_find_root(self):
        path = PROJECT_ROOT / "agent" / "doc_agent.py"
        content = path.read_text(encoding="utf-8")
        assert "pyproject.toml" in content, "_find_project_root()에 pyproject.toml 참조 필요"


class TestGitignore:
    """gitignore에서 test* 와일드카드 제거 확인"""

    def test_no_test_wildcard(self):
        gitignore = PROJECT_ROOT / ".gitignore"
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            # 'test*' 와일드카드가 독립 라인으로 존재하면 안 됨
            if stripped == "test*":
                pytest.fail(".gitignore에 'test*' 와일드카드가 여전히 존재합니다")
