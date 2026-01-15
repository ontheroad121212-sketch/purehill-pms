import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight
from datetime import datetime, timedelta

st.set_page_config(page_title="엠버퓨어힐 경영분석 v8.5", layout="wide")

# 스타일 설정
st.markdown("""<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key", type="password")

st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 분석 (탭 버전)")

uploaded_file = st.file_uploader("PMS 데이터를 업로드하세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # [핵심 로직] 각 탭에서 사용할 "실적 출력기" - 사장님이 만든 그 대시보드 구조 그대로
        def render_dashboard(display_df, title_prefix):
            # 지표 계산용
            def calc_metrics(df):
                total_rev = df['총매출액'].sum()
                room_rev = df['객실매출액'].sum()
                rn = df['room_nights'].sum()
                adr = room_rev / rn if rn > 0 else 0
                return total_rev, room_rev, rn, adr

            # 1단: TOTAL
            st.subheader(f"✅ [{title_prefix} TOTAL] 매출액 / 룸나잇 / 객단가")
            t_total, t_room, t_rn, t_adr = calc_metrics(display_df)
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("총매출액", f"{t_total:,.0f}원")
            tc2.metric("객실매출액", f"{t_room:,.0f}원")
            tc3.metric("총 룸나잇", f"{t_rn:,.0f} RN")
            tc4.metric("객실 ADR", f"{t_adr:,.0f}원")
            
            # 2단: FIT
            st.subheader(f"👤 [{title_prefix} FIT] 매출액 / 룸나잇 / 객단가")
            fit_df = display_df[display_df['market_segment'] == 'FIT']
            f_total, f_room, f_rn, f_adr = calc_metrics(fit_df)
            fc1, fc2, fc3, fc4 = st.columns(4)
            fc1.metric("FIT 총매출", f"{f_total:,.0f}원")
            fc2.metric("FIT 객실매출", f"{f_room:,.0f}원")
            fc3.metric("FIT 룸나잇", f"{f_rn:,.0f} RN")
            fc4.metric("FIT ADR", f"{f_adr:,.0f}원")

            # 3단: GROUP
            st.subheader(f"👥 [{title_prefix} GROUP] 매출액 / 룸나잇 / 객단가")
            grp_df = display_df[display_df['market_segment'] == 'Group']
            g_total, g_room, g_rn, g_adr = calc_metrics(grp_df)
            gc1, gc2, gc3, gc4 = st.columns(4)
            gc1.metric("그룹 총매출", f"{g_total:,.0f}원")
            gc2.metric("그룹 객실매출", f"{g_room:,.0f}원")
            gc3.metric("그룹 룸나잇", f"{g_rn:,.0f} RN")
            gc4.metric("그룹 ADR", f"{g_adr:,.0f}원")

            st.divider()

            # 4단: 행동 지표
            st.subheader("📊 리드타임 / LOS / 국적비")
            b1, b2, b3 = st.columns(3)
            b1.metric("평균 리드타임", f"{display_df['lead_time'].mean():.1f}일")
            b2.metric("평균 숙박일수", f"{display_df['los'].mean():.1f}박")
            counts = display_df['country'].value_counts(normalize=True).head(3) * 100
            b3.metric("주요 국적비", " / ".join([f"{k}: {v:.1f}%" for k, v in counts.to_dict().items()]))

            st.divider()

            # 5단: 그래프 5종 세트 (사장님 요청사항 무삭제)
            st.subheader("📈 상세 시각화 분석")
            pure_acc = fit_df[~fit_df['account'].str.contains('마이스|그룹', na=False)]
            acc_stats = pure_acc.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
            acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']

            col1, col2 = st.columns(2)
            with col1:
                st.write("**거래처별 룸나잇 생산성**")
                st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', color='room_nights', text_auto=True), use_container_width=True)
            with col2:
                st.write("**거래처별 객실 ADR**")
                st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', color='ADR', text_auto=',.0f'), use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                st.write("**거래처별 평균 숙박일수 (LOS)**")
                st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', color='los', text_auto='.1f'), use_container_width=True)
            with col4:
                st.write("**거래처별 평균 리드타임**")
                st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', color='lead_time', text_auto='.1f'), use_container_width=True)

            st.write("**글로벌 OTA 국적 비중 분석**")
            global_ota = display_df[display_df['is_global_ota'] == True]
            if not global_ota.empty:
                st.plotly_chart(px.bar(global_ota, x="account", color="country", barmode="stack", text_auto=True), use_container_width=True)

        # --- 탭 구성 및 날짜 필터링 ---
        tab1, tab2, tab3 = st.tabs(["📅 Daily (일간)", "📊 Weekly (주간)", "📈 Monthly (월간)"])
        
        latest_date = data['도착일'].max()

        with tab1:
            render_dashboard(data[data['도착일'] == latest_date], "DAILY")
        
        with tab2:
            start_of_week = latest_date - timedelta(days=latest_date.weekday())
            render_dashboard(data[data['도착일'] >= start_of_week], "WEEKLY")
            
        with tab3:
            render_dashboard(data[data['도착일'].dt.month == latest_date.month], "MONTHLY")

        # AI 분석
        if st.button("🤖 AI 전문가 리포트 생성"):
            summary = f"오늘ADR:{data[data['도착일']==latest_date]['객실매출액'].mean():,.0f}"
            st.info(get_ai_insight(api_key, summary))
