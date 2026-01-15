import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight

# 화면 설정
st.set_page_config(page_title="퓨어힐 PMS 프리미엄 리포트", layout="wide")

# 사이드바 설정 (API 키 입력 및 보안)
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="키를 입력하세요")
    st.info("입력하신 키는 세션이 종료되면 자동으로 파기됩니다.")
    st.divider()
    st.caption("v2.0: 어카운트(OTA) 분석 기능 추가됨")

st.title("🏛️ 퓨어힐 호텔 경영 분석 대시보드")
st.caption("PMS 데이터를 기반으로 AI가 실시간 경영 전략을 제안합니다.")

# 파일 업로드
uploaded_file = st.file_uploader("PMS 엑셀 파일을 업로드하세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # --- 1구역: 핵심 경영 지표 ---
        st.subheader("📌 주요 실적 요약")
        c1, c2, c3, c4 = st.columns(4)
        
        total_rev = data['판매금액'].sum()
        best_acc = data.groupby('account')['판매금액'].sum().idxmax()
        
        c1.metric("누적 매출액", f"{total_rev:,.0f}원")
        c2.metric("최고 매출 거래처", best_acc)
        c3.metric("평균 리드타임", f"{data['lead_time'].mean():.1f}일")
        c4.metric("평균 객단가(ADR)", f"{total_rev/data['los'].sum():,.0f}원" if data['los'].sum() > 0 else "0원")

        st.divider()

        # --- 2구역: 시각화 분석 (거래처 & 채널) ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏢 거래처별 매출 TOP 10 (아고다, 부킹닷컴 등)")
            # 거래처별 매출 합계 계산 및 정렬
            acc_revenue = data.groupby('account')['판매금액'].sum().sort_values(ascending=True).tail(10).reset_index()
            fig_acc = px.bar(acc_revenue, x='판매금액', y='account', orientation='h',
                             color='판매금액', text_auto=',.0f', 
                             color_continuous_scale='Blues')
            st.plotly_chart(fig_acc, use_container_width=True)

        with col2:
            st.subheader("🌐 예약 경로(Channel) 비중")
            fig_pie = px.pie(data, values='판매금액', names='channel', hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 3구역: 객실 및 트렌드 분석 ---
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🏨 객실 타입별 선호도")
            room_stats = data['room_type'].value_counts().reset_index()
            fig_bar = px.bar(room_stats, x='room_type', y='count', color='count',
                             text_auto=True, color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col4:
            st.subheader("📅 예약 발생 추이")
            daily_trend = data.groupby(data['예약일'].dt.date).size().reset_index(name='건수')
            fig_line = px.line(daily_trend, x='예약일', y='건수', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        # --- 4구역: AI 전략 제언 ---
        st.divider()
        if st.button("🤖 AI 전문가에게 마케팅 전략 리포트 받기"):
            if not api_key:
                st.warning("왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
            else:
                with st.spinner("데이터를 정밀 분석 중입니다..."):
                    # 풍부한 정보를 AI에게 전달 (어카운트 정보 포함)
                    acc_top3 = data.groupby('account')['판매금액'].sum().sort_values(ascending=False).head(3).to_dict()
                    summary = f"""
                    [퓨어힐 실적 요약]
                    - 총 매출: {total_rev:,.0f}원
                    - 상위 3개 거래처: {acc_top3}
                    - 인기 객실: {data['room_type'].value_counts().idxmax()}
                    - 평균 리드타임: {data['lead_time'].mean():.1f}일
                    - 주 고객 국적: {data['country'].value_counts().head(2).to_dict()}
                    """
                    report = get_ai_insight(api_key, summary)
                    st.success("📝 AI 생성 전략 리포트")
                    st.markdown(report)
        
        # 상세 데이터 표
        with st.expander("📝 어카운트별 상세 실적표 보기"):
            acc_table = data.groupby('account').agg({
                '판매금액': 'sum',
                '예약일': 'count',
                'los': 'mean'
            }).rename(columns={'예약일': '예약건수', 'los': '평균박수'}).sort_values('판매금액', ascending=False)
            st.dataframe(acc_table.style.format({'판매금액': '{:,.0f}원', '평균박수': '{:.1f}박'}))

    else:
        st.error("데이터를 분석할 수 없습니다. 파일 형식을 다시 확인해주세요.")
