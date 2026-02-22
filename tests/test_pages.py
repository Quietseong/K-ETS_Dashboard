"""Stage 5: 페이지 정리 검증"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"


# ============================================================
# 1. 페이지 번호 순차 정렬 확인
# ============================================================

class TestPageNumbering:
    """페이지 파일이 1~5 순서로 존재하는지 확인"""

    EXPECTED_PAGES = [
        "1_현황_대시보드.py",
        "2_구매_전략.py",
        "3_프로그램_정보.py",
        "4_AI_챗봇.py",
        "5_AI_리포트.py",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_PAGES)
    def test_page_exists(self, filename):
        assert (PAGES_DIR / filename).exists(), f"{filename} 파일이 없습니다"

    def test_page_count(self):
        """pages 디렉토리에 정확히 5개의 .py 파일만 있는지 확인"""
        py_files = list(PAGES_DIR.glob("*.py"))
        assert len(py_files) == 5, f"예상 5개, 실제 {len(py_files)}개: {[f.name for f in py_files]}"

    @pytest.mark.parametrize("filename", EXPECTED_PAGES)
    def test_page_is_valid_python(self, filename):
        source = (PAGES_DIR / filename).read_text(encoding="utf-8")
        ast.parse(source)


# ============================================================
# 2. 이전 파일명이 존재하지 않는지 확인
# ============================================================

class TestOldPagesRemoved:
    """리네이밍 전 파일명이 남아있지 않은지 확인"""

    OLD_PAGES = [
        "4_프로그램_정보.py",
        "5_AI_챗봇.py",
        "6_AI_리포트.py",
    ]

    @pytest.mark.parametrize("filename", OLD_PAGES)
    def test_old_page_does_not_exist(self, filename):
        assert not (PAGES_DIR / filename).exists(), f"이전 파일 {filename}이 아직 존재합니다"


# ============================================================
# 3. 테스트 파일 내 참조 일관성 확인
# ============================================================

class TestReferenceConsistency:
    """기존 테스트 파일에서 이전 파일명 참조가 없는지 확인"""

    TEST_FILES = [
        "test_stage1_structure.py",
        "test_agent_interfaces.py",
    ]

    OLD_NAMES = [
        "4_프로그램_정보",
        "5_AI_챗봇",
        "6_AI_리포트",
    ]

    @pytest.mark.parametrize("test_file", TEST_FILES)
    def test_no_old_page_references_in_tests(self, test_file):
        source = (PROJECT_ROOT / "tests" / test_file).read_text(encoding="utf-8")
        for old_name in self.OLD_NAMES:
            assert old_name not in source, \
                f"{test_file}에서 이전 파일명 '{old_name}' 참조가 남아있습니다"


# ============================================================
# 4. 페이지 번호 연속성 확인
# ============================================================

class TestPageSequence:
    """페이지 번호가 1부터 연속으로 이어지는지 확인"""

    def test_sequential_numbering(self):
        py_files = sorted(PAGES_DIR.glob("*.py"))
        numbers = []
        for f in py_files:
            prefix = f.name.split("_")[0]
            assert prefix.isdigit(), f"{f.name}의 접두사가 숫자가 아닙니다"
            numbers.append(int(prefix))
        assert numbers == list(range(1, len(numbers) + 1)), \
            f"페이지 번호가 연속적이지 않습니다: {numbers}"
