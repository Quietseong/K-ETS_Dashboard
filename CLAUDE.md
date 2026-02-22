# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

K-ETS 통합 관리 시스템 — 한국 탄소배출권거래제(K-ETS) Streamlit 대시보드 + FastAPI AI 보고서 생성 서버. 현재 **TDD 기반 리팩토링 진행 중**이며, 상세한 리팩토링 맥락은 `handoff.md`를 참조.

## Commands

### Setup
```bash
# 가상환경 활성화 (Git Bash on Windows)
source venv/Scripts/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 필요)
cp env.example .env
# UPSTAGE_API_KEY, OPENAI_API_KEY, PINECONE_API_KEY 설정
```

### Run
```bash
# Streamlit 대시보드 (현재 main.py에 FastAPI도 혼재 — 분리 예정)
streamlit run main.py --server.port 8501

# FastAPI 서버 (보고서 생성 API)
python main.py
# → http://0.0.0.0:8000 (Swagger: /docs)
```

### Test
```bash
# 테스트 인프라 미구축 상태 — TDD 기반 리팩토링 시 pytest로 구축 예정
pytest tests/
```

## Architecture

### 현재 구조 (리팩토링 전)

**main.py가 두 가지 역할을 겸함 (핵심 문제)**:
- **1~483줄**: Streamlit 메인 페이지 (ESG 랭킹, KPI, 배지 시스템)
- **484~711줄**: FastAPI 서버 (보고서 생성 API, SSE 스트리밍)

**Streamlit 멀티페이지** (`pages/`):
- `1_현황_대시보드.py` — 배출량/시장/할당량 차트 + 시나리오 시뮬레이션 챗봇
- `2_구매_전략.py` — 구매 타이밍/ROI/헤징 전략 (대부분 하드코딩 샘플 데이터)
- `4_프로그램_정보.py` — 시스템 정보 (3번 페이지는 원래 없음)
- `5_AI_챗봇.py` — EnhancedCarbonRAGAgent 기반 데이터 분석 챗봇
- `6_AI_리포트.py` — PDF 업로드 → Pinecone RAG → 보고서 생성

**AI 에이전트 3종** (`agent/`):
- `agent_template.py` — 주제 → 보고서 템플릿/JSON 목차 생성 (Pydantic structured output)
- `enhanced_carbon_rag_agent.py` — **핵심 에이전트**: LLM이 Python 코드 생성 → `exec()` 실행 → 결과 반환 + DocumentRAGAgent 조합
- `doc_agent.py` — PDF → Upstage Document Parse → 텍스트 청크 → Pinecone 저장 → RAG 질의응답. `EmbeddingManifestManager`로 파일 해시 기반 증분 임베딩

**프롬프트** (`prompts/`):
- `code_generation.py` — ~600줄 few-shot 프롬프트 (질문 유형별 코드 생성 예시)
- `interpretation.py` — RAG 답변 해석 프롬프트

### 데이터 흐름

```
사용자 질문 → EnhancedCarbonRAGAgent.ask()
  ├─ 1. code_generation 프롬프트로 Python 코드 생성 (LLM)
  ├─ 2. exec()로 코드 실행 (샌드박스 환경, df/pd/plt/sns/np 제공)
  ├─ 3. DocumentRAGAgent.ask()로 문서 기반 답변 조회
  └─ 4. 분석 결과 + 문서 답변 조합하여 최종 응답 생성
반환: (answer, visualization_flag, table_data, figure_obj) — 4-tuple
```

### 외부 서비스
- **Upstage**: Solar-mini LLM, Document Parse API, Embeddings (4096차원)
- **OpenAI**: GPT-4.1-nano (fallback LLM), text-embedding-3-small (1536차원)
- **Pinecone**: Vector DB — 인덱스 `carbon-multiagent` (doc_agent), `carbone-index` (6_AI_리포트)

## Refactoring Status

**확정된 결정 사항**:
- `main.py` → Streamlit 앱과 FastAPI 서버 **완전 분리**
- `src/` (React), `chatbot_app.py`, debug 파일들 → **제거 대상**
- pages 번호 재정렬 (3번 없음 → 순차 정리)
- 개발 방식: **TDD 기반** (pytest)

## Key Conventions

- CSV 데이터 인코딩: `cp949` → `euc-kr` → `utf-8` 순서로 시도 (한국어 데이터)
- LLM 선택 로직: Upstage API 키 우선, 없으면 OpenAI fallback
- 모든 에이전트에서 `sys.path.append(...)` 패턴 반복 사용 중 (패키지화 시 제거 예정)
- `agent.ask()` 반환값이 호출처마다 다르게 기대됨 (2~4-tuple) — 통일 필요
