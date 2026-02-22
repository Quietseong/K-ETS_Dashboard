"""에이전트 공통 타입 정의"""

from typing import NamedTuple, Optional

import pandas as pd


class AgentResponse(NamedTuple):
    """EnhancedCarbonRAGAgent.ask() 반환 타입.

    NamedTuple이므로 기존 tuple unpacking과 호환됩니다:
        answer, viz, table, fig = agent.ask(question)
    속성 접근도 가능합니다:
        resp = agent.ask(question)
        resp.answer, resp.visualization, ...
    """

    answer: str
    visualization: Optional[str] = None
    table_data: Optional[pd.DataFrame] = None
    figure: Optional[object] = None
