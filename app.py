import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight
from datetime import datetime, timedelta

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 경영분석 v8.0", layout="wide")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.caption("v8.0: 일간/주간/월간 비교 분석 탭 시스템")

st.title("🏛️ 엠버퓨어힐 호텔 경영 분석 대시보드")

uploaded_file = st.file_uploader("PMS 데이터를 업로드하세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # 공통 지표 계산 함수
        def get_metrics(df):
            if df.empty: return 0, 0, 0, 0
            rev = df['총매출액'].sum()
            room_rev = df['객실매출액'].sum()
            rn = df['room_nights'].sum()
            adr = room_rev / rn if rn > 0 else 0
            return rev, room_rev, rn, adr

        # 데이터 분석 날짜 기준 설정 (파일 내 가장 최근 도착일 기준)
        latest_date = data['도착일'].max()
        
        # --- 탭 구성 ---
        tab1, tab2, tab3 = st.tabs(["📅 Daily (일간)", "📊 Weekly (주간)", "📈 Monthly (월간)"])

        # --- Tab 1: 일간 분석 (어제 vs 오늘) ---
        with tab1:
            st.subheader(f"📍 {latest_date.date()} 실적 및 전일 비교")
            
            yesterday = latest_date - timedelta(days=1)
            today_df = data[data['도착일'] == latest_date]
            yest_df = data[data['도착일'] == yesterday]
            
            t_rev, t_rm, t_rn, t_adr = get_metrics(today_df)
            y_rev, y_rm, y_rn, y_adr = get_metrics(yest_df)
            
            def calc_diff(curr, prev):
                if prev == 0: return None
                return ((curr - prev) / prev) * 100

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("오늘 총매출", f"{t_rev:,.0f}원", delta=f"{calc_diff(t_rev, y_rev):.1f}%" if y_rev else "N/A")
            m2.metric("오늘 객실매출", f"{t_rm:,.0f}원", delta=f"{calc_diff(t_rm, y_rm):.1f}%" if y_rm else "N/A")
            m3.metric("오늘 룸나잇", f"{t_rn:,.0f} RN", delta=f"{t_rn - y_rn:,.0f} RN")
            m4.metric("오늘 객실 ADR", f"{t_adr:,.0f}원", delta=f"{calc_diff(t_adr, y_adr):.1f}%" if y_adr else "N/A")
            
            st.divider()
            st.subheader("🏢 어제/오늘 주요 거래처 점유율")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**오늘의 거래처 TOP 5**")
                st.dataframe(today_df.groupby('account')['총매출액'].sum().sort_values(ascending=False).head(5))
            with col2:
                st.write("**어제의 거래처 TOP 5**")
                st.dataframe(yest_df.groupby('account')['총매출액'].sum().sort_values(ascending=False).head(5))

        # --- Tab 2: 주간 분석 (요일별 패턴 및 전주 비교) ---
        with tab2:
            current_week = latest_date.isocalendar().week
            this_week_df = data[data['도착주차'] == current_week]
            prev_week_df = data[data['도착주차'] == current_week - 1]
            
            tw_rev, tw_rm, tw_rn, tw_adr = get_metrics(this_week_df)
            pw_rev, pw_rm, pw_rn, pw_adr = get_metrics(prev_week_df)
            
            st.subheader(f"📅 이번 주 실적 vs 지난 주 (Week {current_week})")
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("이번 주 매출", f"{tw_rev:,.0f}원", delta=f"{calc_diff(tw_rev, pw_rev):.1f}%" if pw_rev else "N/A")
            w2.metric("이번 주 룸나잇", f"{tw_rn:,.0f} RN", delta=f"{tw_rn - pw_rn:,.0f} RN")
            w3.metric("이번 주 ADR", f"{tw_adr:,.0f}원", delta=f"{calc_diff(tw_adr, pw_adr):.1f}%" if pw_adr else "N/A")
            w4.metric("주간 평균 리드타임", f"{this_week_df['lead_time'].mean():.1f}일")

            st.divider()
            
            col3, col4 = st.columns(2)
            with col3:
                st.subheader("🗓️ 요일별 예약 도착 패턴 (RN)")
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                week_trend = this_week_df.groupby('도착요일')['room_nights'].sum().reindex(day_order).reset_index()
                fig_week = px.bar(week_trend, x='도착요일', y='room_nights', color='room_nights', text_auto=True)
                st.plotly_chart(fig_week, use_container_width=True)
            with col4:
                st.subheader("🏢 주간 거래처별 LOS 분석")
                week_acc_los = this_week_df.groupby('account')['los'].mean().sort_values().tail(10).reset_index()
                fig_los = px.bar(week_acc_los, x='los', y='account', orientation='h', color='los', text_auto='.1f')
                st.plotly_chart(fig_los, use_container_width=True)

        # --- Tab 3: 월간 분석 (전월 대비 및 글로벌 분석) ---
        with tab3:
            this_month = latest_date.month
            this_month_df = data[data['도착일'].dt.month == this_month]
            prev_month_df = data[data['도착일'].dt.month == this_month - 1]
            
            tm_rev, tm_rm, tm_rn, tm_adr = get_metrics(this_month_df)
            pm_rev, pm_rm, pm_rn, pm_adr = get_metrics(prev_month_df)
            
            st.subheader(f"📈 {this_month}월 실적 현황")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("이번 달 매출", f"{tm_rev:,.0f}원", delta=f"{calc_diff(tm_rev, pm_rev):.1f}%" if pm_rev else "N/A")
            m2.metric("이번 달 룸나잇", f"{tm_rn:,.0f} RN")
            m3.metric("이번 달 ADR", f"{tm_adr:,.0f}원")
            m4.metric("외국인 투숙 비중", f"{(len(this_month_df[this_month_df['country']!='KOR'])/len(this_month_df)*100):.1f}%" if not this_month_df.empty else "0%")

            st.divider()
            
            st.subheader("🌏 글로벌 OTA 채널별 국적 분포")
            global_ota = this_month_df[this_month_df['is_global_ota'] == True]
            if not global_ota.empty:
                fig_global = px.bar(global_ota, x="account", color="country", barmode="stack", text_auto=True)
                st.plotly_chart(fig_global, use_container_width=True)
            
            st.subheader("🛌 월간 객실 타입별 매출 기여도")
            fig_room = px.treemap(this_month_df, path=['market_segment', 'room_type'], values='객실매출액')
            st.plotly_chart(fig_room, use_container_width=True)

        # AI 분석 공통 버튼 (하단)
        st.divider()
        if st.button("🤖 AI 기간별 통합 경영 리포트 생성"):
            if api_key:
                with st.spinner("AI가 일/주/월간 데이터를 교차 분석 중입니다..."):
                    summary = f"오늘매출:{t_rev:,.0f}(전일비{calc_diff(t_rev, y_rev):.1f}%), 이번주매출:{tw_rev:,.0f}, 이번달매출:{tm_rev:,.0f}"
                    report = get_ai_insight(api_key, summary + " 이 비교 실적을 바탕으로 다음 주 판매 가격(ADR) 조정이 필요한지 분석해줘.")
                    st.success("📝 AI 전문 경영 보고서")
                    st.markdown(report)
            else:
                st.warning("API 키를 입력하세요.")
