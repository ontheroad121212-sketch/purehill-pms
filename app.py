import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight

st.set_page_config(page_title="퓨어힐 PMS 프리미엄 리포트", layout="wide")

# 사이드바: 설정 및 보안
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.info("API Key는 브라우저에만 유지되며 저장되지 않습니다.")

st.title("🏛️ 퓨어힐 호텔 경영 분석 대시보드")
st.caption("PMS 데이터를 기반으로 AI가 실시간 경영 전략을 제안합니다.")

uploaded_file = st.file_uploader("PMS 엑셀 파일을 업로드하세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # --- 1구역: 핵심 지표 ---
        st.subheader("📌 주요 경영 지표")
        c1, c2, c3, c4 = st.columns(4)
        total_rev = data['판매금액'].sum()
        c1.metric("누적 매출액", f"{total_rev:,.0f}원")
        c2.metric("총 예약 건수", f"{len(data)}건")
        c3.metric("평균 리드타임", f"{data['lead_time'].mean():.1f}일")
        c4.metric("평균 객단가(ADR)", f"{data['판매금액'].sum()/data['los'].sum():,.0f}원" if data['los'].sum() > 0 else "0원")

        st.divider()

        # --- 2구역: 시각화 분석 ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌐 채널별 매출 비중")
            fig_pie = px.pie(data, values='판매금액', names='channel', hole=0.5,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader("📅 예약 발생 추이")
            daily_trend = data.groupby(data['예약일'].dt.date).size().reset_index(name='건수')
            fig_line = px.line(daily_trend, x='예약일', y='건수', markers=True, 
                               line_shape='spline', color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig_line, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🏨 객실 타입별 선호도")
            room_stats = data['room_type'].value_counts().reset_index()
            fig_bar = px.bar(room_stats, x='room_type', y='count', color='count',
                             text_auto=True, color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col4:
            st.subheader("🌍 국적별 고객 분포")
            country_stats = data['country'].value_counts().reset_index().head(5)
            fig_sun = px.pie(country_stats, values='count', names='country',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sun, use_container_width=True)

        # --- 3구역: AI 전략 제언 ---
        st.divider()
        if st.button("🤖 AI 전문가에게 경영 전략 리포트 받기"):
            if not api_key:
                st.warning("사이드바에 API Key를 먼저 입력해주세요!")
            else:
                with st.spinner("데이터를 정밀 분석 중입니다..."):
                    # 풍부한 정보를 AI에게 전달
                    summary = f"""
                    [퓨어힐 실적 요약]
                    - 총 매출: {total_rev:,.0f}원
                    - 점유율 상위 채널: {data['channel'].value_counts().idxmax()}
                    - 최고 인기 객실: {data['room_type'].value_counts().idxmax()}
                    - 평균 리드타임: {data['lead_time'].mean():.1f}일
                    - 주 고객 국적: {data['country'].value_counts().head(2).to_dict()}
                    """
                    report = get_ai_insight(api_key, summary)
                    st.success("📝 AI 생성 전략 리포트")
                    st.markdown(report)
        
        # 상세 데이터 보기
        with st.expander("📝 원본 데이터 상세 보기"):
            st.dataframe(data)

    else:
        st.error("데이터를 분석할 수 없습니다. 파일 형식을 다시 확인해주세요.")
