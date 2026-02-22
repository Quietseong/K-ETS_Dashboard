"""K-ETS AI 보고서 생성 FastAPI 서버

Streamlit 대시보드(main.py)와 분리된 독립 API 서버.
보고서 목차 생성, 본문 스트리밍, 파일 다운로드 기능을 제공합니다.

실행: python app_api.py 또는 uvicorn app_api:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import json
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal
from urllib.parse import quote

from utils import create_docx, create_pdf

# .env 파일 로드
load_dotenv()

# --- 에이전트 임포트 ---
try:
    from agent.agent_template import ReportTemplateAgent
    from agent.enhanced_carbon_rag_agent import EnhancedCarbonRAGAgent
except Exception as e:
    print(f"에이전트 임포트 중 오류 발생: {e}")
    sys.exit(1)


# --- 에이전트 초기화 ---
try:
    template_agent = ReportTemplateAgent()
    report_agent = EnhancedCarbonRAGAgent()
    print("✅ 모든 에이전트가 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"❌ 에이전트 초기화 실패: {e}")
    template_agent = None
    report_agent = None


# --- FastAPI 앱 초기화 ---
app = FastAPI(
    title="K-ETS 대시보드 AI 보고서 생성기 API",
    description="주제를 기반으로 보고서의 목차를 생성하고, 목차에 따라 본문을 스트리밍하는 API입니다.",
    version="1.0.0"
)

# --- CORS 미들웨어 설정 ---
origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic 데이터 모델 정의 ---

class TopicRequest(BaseModel):
    topic: str = Field(...,
                       description="생성할 보고서의 주제",
                       example="국내 탄소 배출 현황 및 감축 전략")


class OutlineResponse(BaseModel):
    template_text: str = Field(...,
                               description="LLM이 생성한 보고서의 뼈대(템플릿) 텍스트")
    outline: Dict[str, Any] = Field(...,
                                    description="템플릿 텍스트를 기반으로 생성된 구조화된 목차(JSON)")


class ReportRequest(BaseModel):
    topic: str = Field(..., description="원본 보고서 주제")
    outline: Dict[str, Any] = Field(..., description="사용자가 수정 완료한 최종 목차 JSON")


class ReportDownloadRequest(BaseModel):
    title: str = Field(..., description="보고서 제목")
    content: str = Field(..., description="생성된 보고서의 전체 텍스트 내용")


# --- API 엔드포인트 구현 ---

@app.get("/", summary="API 상태 확인")
async def read_root():
    """API 서버가 정상적으로 실행 중인지 확인하는 기본 엔드포인트입니다."""
    return {"status": "K-ETS AI Report Generator API is running"}


@app.post("/generate-outline-from-topic", response_model=OutlineResponse, summary="주제 기반 보고서 구조 생성")
async def generate_outline(request: TopicRequest):
    """
    사용자가 입력한 주제를 받아, 보고서 템플릿(텍스트)과 구조화된 목차(JSON)를 생성하여 반환합니다.
    """
    if not template_agent:
        raise HTTPException(status_code=503, detail="보고서 구조 생성 에이전트를 사용할 수 없습니다.")

    topic = request.topic
    print(f"--- 주제 기반 구조 생성 요청: '{topic}' ---")

    try:
        template_text = template_agent.generate_report_template(topic)
        if not template_text:
            raise HTTPException(status_code=500, detail="보고서 템플릿 생성에 실패했습니다.")

        outline_json = template_agent.generate_structured_outline(template_text)
        if not outline_json:
            raise HTTPException(status_code=500, detail="구조화된 목차 생성에 실패했습니다.")

        print("--- ✅ 구조 생성 완료 ---")
        return OutlineResponse(template_text=template_text, outline=outline_json)
    except Exception as e:
        print(f"❌ 구조 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def report_streamer(topic: str, outline: Dict[str, Any]):
    """목차(outline)를 순회하며 각 섹션의 내용을 생성하고 스트리밍하는 비동기 제너레이터"""

    async def _traverse_outline(outline_nodes: List[Dict[str, Any]]):
        """재귀적으로 목차 노드를 탐색하고 컨텐츠를 생성"""
        for node in outline_nodes:
            section_title = node.get("title", "제목 없음")

            # 섹션 제목 스트리밍
            title_payload = {"type": "section_title", "payload": section_title}
            yield f"data: {json.dumps(title_payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            # 에이전트에게 전달할 구체적인 질문 생성
            question = f"'{topic}'에 대한 보고서를 작성 중입니다. '{section_title}' 섹션에 들어갈 내용을 데이터와 문서를 기반으로 분석하고, 전문적인 보고서 형식의 서술형 문장으로 작성해주세요."

            content_stream = None
            try:
                loop = asyncio.get_running_loop()
                agent_response = await loop.run_in_executor(
                    None,
                    report_agent.ask,
                    question,
                    section_title
                )
                content_stream = agent_response.answer

            except Exception as e:
                print("-" * 50)
                print(f"!!! Agent 호출 중 에러 발생 ('{section_title}') !!!")
                print(f"에러: {e}")
                print("-" * 50)
                error_payload = {"type": "error", "payload": f"'{section_title}' 생성 중 에러: {e}"}
                yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

            print("-" * 50)
            print(f"Agent 응답 ('{section_title}'):")
            print(f"응답 내용: {content_stream}")
            print(f"타입: {type(content_stream)}")
            print("-" * 50)

            if content_stream and isinstance(content_stream, str):
                paragraphs = content_stream.split('\n')
                for para in paragraphs:
                    if para.strip():
                        content_payload = {"type": "content", "payload": para.strip()}
                        yield f"data: {json.dumps(content_payload, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.05)

            # 하위 섹션이 있으면 재귀적으로 처리
            if "sections" in node and node["sections"]:
                async for item in _traverse_outline(node["sections"]):
                    yield item

    # 최상위 챕터부터 순회 시작
    if "chapters" in outline and outline["chapters"]:
        async for item in _traverse_outline(outline["chapters"]):
            yield item

    # 모든 작업 완료 신호 전송
    done_payload = {"type": "done", "payload": "보고서 생성이 완료되었습니다."}
    yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"


@app.post("/generate-report", summary="보고서 본문 생성 및 실시간 스트리밍")
async def generate_report_streaming(request: ReportRequest):
    """
    사용자가 수정한 최종 목차를 받아, 각 섹션의 본문을 실시간으로 생성하여 Server-Sent Events (SSE)로 스트리밍
    """
    topic = request.topic
    outline = request.outline
    return StreamingResponse(report_streamer(topic, outline), media_type="text/event-stream")


@app.post("/download-report", summary="생성된 보고서를 파일로 다운로드")
async def download_report(
    request: ReportDownloadRequest,
    format: Literal['docx', 'pdf'] = 'docx'
):
    """
    클라이언트로부터 받은 보고서의 전체 텍스트를
    지정된 파일 형식(DOCX 또는 PDF)으로 변환하여 다운로드합니다.
    """
    title = request.title
    content = request.content

    if format == 'docx':
        file_stream = create_docx(title, content)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{title}.docx"
    elif format == 'pdf':
        file_stream = create_pdf(title, content)
        media_type = "application/pdf"
        filename = f"{title}.pdf"
    else:
        return Response(status_code=400, content="Unsupported file format")

    encoded_filename = quote(filename)
    headers = {
        'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
    }

    return Response(content=file_stream.read(), media_type=media_type, headers=headers)


# --- 서버 실행 (Uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    uvicorn.run("app_api:app", host="0.0.0.0", port=8000, reload=is_dev)
