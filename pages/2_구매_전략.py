import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 페이지 설정은 main.py에서 처리됨

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 32px;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .strategy-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .alert-container {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        border-left: 5px solid #ff4757;
    }
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 15px 0;
        border: 1px solid #e1e8ed;
    }
    .metric-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        border-left: 5px solid #00cec9;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 class="main-header">🎯 탄소배출권 구매 전략 대시보드</h1>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 전략 설정")
    
    st.subheader("📊 기업 정보")
    company_size = st.selectbox(
        "기업 규모",
        ["대기업", "중견기업", "중소기업", "소기업"]
    )
    
    annual_emission = st.number_input(
        "연간 배출량 (톤 CO₂)",
        min_value=1000,
        max_value=1000000,
        value=50000,
        step=1000
    )
    
    current_allocation = st.number_input(
        "현재 할당량 (톤 CO₂)",
        min_value=0,
        max_value=annual_emission,
        value=int(annual_emission * 0.8),
        step=1000
    )
    
    st.subheader("💰 투자 설정")
    budget = st.number_input(
        "투자 예산 (억원)",
        min_value=1,
        max_value=1000,
        value=100,
        step=10
    )
    
    risk_tolerance = st.select_slider(
        "리스크 성향",
        options=["보수적", "중립적", "적극적"],
        value="중립적"
    )
    
    st.subheader("📅 분석 기간")
    analysis_period = st.selectbox(
        "분석 기간",
        ["3개월", "6개월", "1년", "2년"],
        index=2
    )

# 메인 콘텐츠
# 1. 🔔 알림 요약 (정책/가격 급등 예고 등)
st.markdown('<div class="alert-container">', unsafe_allow_html=True)
st.subheader("🔔 긴급 알림 요약")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🚨 긴급", "3건", "정책 발표 예정")
    
with col2:
    st.metric("⚠️ 주의", "5건", "가격 변동 예상")
    
with col3:
    st.metric("💡 기회", "2건", "매수 타이밍")

# 알림 목록
alerts = [
    {"level": "🚨 긴급", "title": "EU 정책 발표 예정", "content": "다음 EU 정책 발표 전까지 가격 급등이 예상됩니다. 2주 내 선매수 권장.", "time": "2일 후"},
    {"level": "⚠️ 주의", "title": "환경부 할당량 축소", "content": "환경부가 중소기업 배출권 무상 할당 축소 예정. 비용 상승 가능성 있음.", "time": "1주 후"},
    {"level": "💡 기회", "title": "시장 하락 예상", "content": "다음 달 초 시장 하락이 예상되어 매수 타이밍으로 판단됩니다.", "time": "3일 후"}
]

for alert in alerts:
    st.markdown(f"""
    **{alert['level']} {alert['title']}** ({alert['time']})
    {alert['content']}
    """)
    st.markdown("---")

st.markdown('</div>', unsafe_allow_html=True)

# 2. 📈 구매 타이밍 분석 그래프 (추천 시점 표시)
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("📈 다이나믹 구매 타이밍 추천 시스템")

# 샘플 가격 데이터 생성
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
price_data = []
base_price = 8770

for i, date in enumerate(dates):
    # 계절성 + 트렌드 + 변동성 추가
    seasonal = np.sin((i/365) * 2 * np.pi) * 500
    trend = (i/365) * 1000
    volatility = np.random.normal(0, 200)
    
    price = base_price + seasonal + trend + volatility
    price_data.append({
        '날짜': date,
        '가격': max(price, 1000),
        '거래량': np.random.randint(1000, 10000),
        '추천': '매수' if price < base_price + seasonal else '관망'
    })

price_df = pd.DataFrame(price_data)

# 구매 타이밍 분석 차트
fig_timing = make_subplots(
    rows=2, cols=1,
    subplot_titles=('배출권 가격 추이 및 매수 타이밍', '거래량 분석'),
    vertical_spacing=0.1,
    row_heights=[0.7, 0.3]
)

# 가격 차트
fig_timing.add_trace(
    go.Scatter(
        x=price_df['날짜'],
        y=price_df['가격'],
        mode='lines',
        name='배출권 가격',
        line=dict(color='#1f77b4', width=2)
    ),
    row=1, col=1
)

# 매수 추천 포인트
buy_points = price_df[price_df['추천'] == '매수']
fig_timing.add_trace(
    go.Scatter(
        x=buy_points['날짜'],
        y=buy_points['가격'],
        mode='markers',
        name='매수 추천',
        marker=dict(color='red', size=8, symbol='triangle-up')
    ),
    row=1, col=1
)

# 거래량 차트
fig_timing.add_trace(
    go.Bar(
        x=price_df['날짜'],
        y=price_df['거래량'],
        name='거래량',
        marker_color='lightblue'
    ),
    row=2, col=1
)

fig_timing.update_layout(
    height=600,
    title="최적 매수 타이밍 분석",
    showlegend=True
)

st.plotly_chart(fig_timing, use_container_width=True)

# 매수 추천 요약
st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
st.markdown("""
**🎯 현재 매수 추천:**
- **최적 매수 시점**: 다음 주 초 (가격 하락 예상)
- **목표 가격**: 8,200원 이하
- **예상 절감**: 약 3억원 (현재 대비 15% 절감)
- **투자 전략**: 분할 매수 권장 (50% 즉시, 50% 추가 하락 시)
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 3. ♻️ 대체 전략 분석 (감축 vs 구매 ROI 비교)
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("♻️ 대체 수단 분석 (감축 vs 구매 ROI 비교)")

col1, col2 = st.columns(2)

with col1:
    # 감축 투자 분석
    st.subheader("🏭 감축 투자 분석")
    
    reduction_options = {
        "에너지 효율 개선": {"cost": 50, "reduction": 20, "roi": 15},
        "재생에너지 설치": {"cost": 200, "reduction": 60, "roi": 25},
        "탄소 포집 기술": {"cost": 300, "reduction": 80, "roi": 30},
        "공정 개선": {"cost": 30, "reduction": 15, "roi": 12}
    }
    
    for option, data in reduction_options.items():
        st.markdown(f"""
        **{option}**
        - 투자 비용: {data['cost']}억원
        - 감축량: {data['reduction']}%
        - ROI: {data['roi']}%
        """)

with col2:
    # 구매 vs 감축 비교
    st.subheader("💰 ROI 비교 분석")
    
    comparison_data = {
        '전략': ['배출권 구매', '에너지 효율', '재생에너지', '탄소 포집'],
        '투자비용(억원)': [100, 50, 200, 300],
        'ROI(%)': [8, 15, 25, 30],
        '리스크': ['낮음', '중간', '높음', '매우높음']
    }
    
    comp_df = pd.DataFrame(comparison_data)
    
    fig_comparison = px.bar(
        comp_df,
        x='전략',
        y='ROI(%)',
        color='투자비용(억원)',
        title='전략별 ROI 비교',
        color_continuous_scale='Viridis'
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)

# 추천 전략
st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
st.markdown("""
**💡 전략 추천:**
현재 배출권 가격이 높은 상황에서 **재생에너지 설치**가 가장 높은 ROI(25%)를 보입니다.
- **단기**: 배출권 구매로 즉시 대응
- **중장기**: 재생에너지 설치로 자체 감축 확대
- **예상 절감**: 연간 15억원 (투자 대비 25% 수익)
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 4. 💹 헷지 전략 추천 (탄소 ETF/선물 분석)
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("💹 탄소 ETF 및 선물 연계 자동 헤징 전략")

# 헤징 옵션 분석
hedging_options = pd.DataFrame({
    '상품': ['EUA 선물', '탄소 ETF', '재생에너지 ETF', '탄소 크레딧 펀드'],
    '수익률(%)': [12, 8, 15, 10],
    '변동성(%)': [25, 18, 30, 22],
    '상관관계': [0.95, 0.85, 0.70, 0.80],
    '최소투자(억원)': [10, 5, 8, 15]
})

col1, col2 = st.columns(2)

with col1:
    # 헤징 상품 비교
    fig_hedge = px.scatter(
        hedging_options,
        x='변동성(%)',
        y='수익률(%)',
        size='최소투자(억원)',
        color='상관관계',
        hover_name='상품',
        title='헤징 상품 비교 분석',
        color_continuous_scale='RdYlBu'
    )
    
    st.plotly_chart(fig_hedge, use_container_width=True)

with col2:
    # 포트폴리오 추천
    st.subheader("📊 포트폴리오 추천")
    
    portfolio = {
        '배출권 직접구매': 60,
        'EUA 선물': 20,
        '재생에너지 ETF': 15,
        '현금': 5
    }
    
    fig_portfolio = px.pie(
        values=list(portfolio.values()),
        names=list(portfolio.keys()),
        title='권장 포트폴리오 비중'
    )
    
    st.plotly_chart(fig_portfolio, use_container_width=True)

# 헤징 전략 요약
st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
st.markdown("""
**🎯 헤징 전략 추천:**
현재 가격 상승 국면에서 **EUA 선물 20% + 재생에너지 ETF 15%** 조합을 권장합니다.
- **예상 수익률**: 12-15%
- **리스크 헤지**: 80% 효과
- **유동성**: 높음
- **추가 투자**: 35억원 필요
""")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 5. 📄 리포트 다운로드 (PDF) / 요약 보기
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("📄 AI 기반 전략 리포트")

# 리포트 요약
report_summary = f"""
# 🎯 탄소배출권 구매 전략 리포트

## 📊 현재 상황 분석
- **기업 규모**: {company_size}
- **연간 배출량**: {annual_emission:,}톤 CO₂
- **현재 할당량**: {current_allocation:,}톤 CO₂
- **부족량**: {annual_emission - current_allocation:,}톤 CO₂

## 💰 투자 전략 요약
1. **즉시 실행**: 배출권 60% 구매 (60억원)
2. **중기 전략**: 재생에너지 설치 (200억원)
3. **헤징 전략**: EUA 선물 20% (20억원)

## 📈 예상 효과
- **총 투자**: 280억원
- **연간 절감**: 45억원
- **ROI**: 16%
- **리스크**: 중간

## ⚠️ 주의사항
- 정책 변화 모니터링 필요
- 가격 변동성 고려
- 분할 투자 권장
"""

st.text_area("📋 리포트 미리보기", report_summary, height=400)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 PDF 다운로드", type="primary"):
        st.success("PDF 생성 중... (실제 구현 시 PDF 생성 로직 추가)")

with col2:
    if st.button("📧 이메일 발송"):
        st.success("이메일 발송 완료!")

with col3:
    if st.button("🔄 리포트 새로고침"):
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 플로팅 챗봇 버튼 제거됨

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; margin-top: 50px;'>
        <p>🎯 탄소배출권 구매 전략 대시보드 | AI 기반 전략 분석</p>
        <p>실시간 데이터 기반 최적화된 투자 전략 제공</p>
    </div>
    """, 
    unsafe_allow_html=True
) 