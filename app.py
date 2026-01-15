import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 경영분석 v9.1", layout="wide")

# 대시보드 스타일
st.markdown("""<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }</style>""", unsafe_allow_html=True)

# 2. 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.info("입력하신 키는 세션 종료 시 자동으로 파기됩니다.")
    st.divider()
    st.caption("v9.1: 조식 분석 에러 수정 및 전체 지표 통합")

st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 분석 대시보드")
st.caption("예약 생성일 기준 실적 및 세그먼트별 조식 기여도 정밀 리포트")

# 4. 파일 업로드
uploaded_file = st.file_uploader("전체 PMS 데이터를 올려주세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # 기준일 설정 (예약일 기준)
        latest_booking_date = data['예약일'].max()
        
        # 지표 계산용 함수
        def calc_metrics(df):
            total_sales = df['총매출액'].sum()
            room_sales = df['객실매출액'].sum()
            rn = df['room_nights'].sum()
            adr = room_sales / rn if rn > 0 else 0
            return total_sales, room_sales, rn, adr

        # --- 메인 대시보드 함수 (무삭제 통합) ---
        def render_booking_dashboard(target_df, compare_df, title_label):
            def get_delta_pct(curr, prev):
                if prev == 0: return "N/A"
                return f"{((curr - prev) / prev * 100):.1f}%"

            # 데이터 세그먼트 분리
            f_curr = target_df[target_df['market_segment'] == 'FIT']
            f_prev = compare_df[compare_df['market_segment'] == 'FIT']
            g_curr = target_df[target_df['market_segment'] == 'Group']
            g_prev = compare_df[compare_df['market_segment'] == 'Group']

            # 실적 산출
            t_tot, t_room, t_rn, t_adr = calc_metrics(target_df)
            p_tot, p_room, p_rn, p_adr = calc_metrics(compare_df)

            # --- 1구역: TOTAL ---
            st.subheader(f"✅ [{title_label} TOTAL 예약실적]")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 예약금액", f"{t_tot:,.0f}원", delta=get_delta_pct(t_tot, p_tot))
            c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=get_delta_pct(t_room, p_room))
            c3.metric("판매 룸나잇 (RN)", f"{t_rn:,.0f} RN", delta=f"{t_rn - p_rn:,.0f}")
            c4.metric("평균 판매단가 (ADR)", f"{t_adr:,.0f}원", delta=get_delta_pct(t_adr, p_adr))
            st.write("---")

            # --- 2구역: FIT ---
            st.subheader(f"👤 [{title_label} FIT 예약]")
            fc_tot, fc_room, fc_rn, fc_adr = calc_metrics(f_curr)
            fp_tot, fp_room, fp_rn, fp_adr = calc_metrics(f_prev)
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("FIT 예약금액", f"{fc_tot:,.0f}원", delta=get_delta_pct(fc_tot, fp_tot))
            f2.metric("FIT 객실매출", f"{fc_room:,.0f}원", delta=get_delta_pct(fc_room, fp_room))
            f3.metric("FIT 룸나잇", f"{fc_rn:,.0f} RN", delta=f"{fc_rn - fp_rn:,.0f}")
            f4.metric("FIT ADR", f"{fc_adr:,.0f}원", delta=get_delta_pct(fc_adr, fp_adr))
            st.write("---")

            # --- 3구역: GROUP ---
            st.subheader(f"👥 [{title_label} GROUP 예약]")
            gc_tot, gc_room, gc_rn, gc_adr = calc_metrics(g_curr)
            gp_tot, gp_room, gp_rn, gp_adr = calc_metrics(g_prev)
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("그룹 예약금액", f"{gc_tot:,.0f}원", delta=get_delta_pct(gc_tot, gp_tot))
            g2.metric("그룹 객실매출", f"{gc_room:,.0f}원", delta=get_delta_pct(gc_room, gp_room))
            g3.metric("그룹 룸나잇", f"{gc_rn:,.0f} RN", delta=f"{gc_rn - gp_rn:,.0f}")
            g4.metric("그룹 ADR", f"{gc_adr:,.0f}원", delta=get_delta_pct(gc_adr, gp_adr))

            st.divider()

            # --- 4구역: 행동 지표 (FIT 중심) ---
            st.subheader("📊 고객 행동 분석 (FIT 고객 중심)")
            b1, b2, b3 = st.columns(3)
            fit_lead = f_curr['lead_time'].mean() if not f_curr.empty else 0
            fit_los = f_curr['los'].mean() if not f_curr.empty else 0
            b1.metric("📅 평균 리드타임 (FIT)", f"{fit_lead:.1f}일")
            b2.metric("🌙 평균 숙박일수 (FIT LOS)", f"{fit_los:.1f}박")
            nc = f_curr['country'].value_counts(normalize=True).head(3) * 100
            b3.metric("🌍 FIT 주요 국적비", " / ".join([f"{k}: {v:.1f}%" for k, v in nc.to_dict().items()]))

            st.divider()

            # --- 5구역: 조식 비중 분석 ---
            st.subheader("🍳 조식 포함 비중 분석")
            col_bf1, col_bf2 = st.columns(2)
            
            with col_bf1:
                st.write("**전체 vs FIT 조식 포함 비중**")
                bf_all = target_df['breakfast_status'].value_counts().reset_index()
                bf_fit = f_curr['breakfast_status'].value_counts().reset_index()
                bf_fit['segment'] = 'FIT'
                bf_all['segment'] = 'TOTAL'
                bf_combined = pd.concat([bf_all, bf_fit])
                fig_bf_pie = px.sunburst(bf_combined, path=['segment', 'breakfast_status'], values='count', 
                                         color='breakfast_status', color_discrete_map={'조식포함':'#FFD700', '조식불포함':'#E1E4E8'})
                st.plotly_chart(fig_bf_pie, use_container_width=True)

            with col_bf2:
                st.write("**거래처별 조식 포함 비중 (TOP 10)**")
                acc_bf = target_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0)
                if '조식포함' in acc_bf.columns:
                    # 문법 오류 수정: 바다코끼리 연산자 제거하고 표준 방식으로 계산
                    row_sums = acc_bf.sum(axis=1)
                    acc_bf['조식선택률'] = (acc_bf['조식포함'] / row_sums) * 100
                    acc_bf_plot = acc_bf.sort_values('조식선택률', ascending=False).head(10).reset_index()
                    fig_acc_bf = px.bar(acc_bf_plot, x='조식선택률', y='account', orientation='h', 
                                        text_auto='.1f', title="거래처별 조식 포함 예약 비중 (%)",
                                        color_continuous_scale='YlOrRd', color='조식선택률')
                    st.plotly_chart(fig_acc_bf, use_container_width=True)
                else:
                    st.info("조식 포함 예약 데이터가 없습니다.")

            st.divider()

            # --- 6구역: 기존 시각화 그래프 5종 (무삭제) ---
            st.subheader("📈 채널 및 거래처 심층 시각화")
            pure_acc = f_curr[~f_curr['account'].str.contains('마이스|그룹', na=False)]
            acc_stats = pure_acc.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
            acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.write("**거래처별 룸나잇 생산성**")
                st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', color='room_nights', text_auto=True, color_continuous_scale='Blues'), use_container_width=True)
            with g_col2:
                st.write("**거래처별 객실 ADR**")
                st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', color='ADR', text_auto=',.0f', color_continuous_scale='Greens'), use_container_width=True)

            g_col3, g_col4 = st.columns(2)
            with g_col3:
                st.write("**거래처별 평균 숙박일수 (LOS)**")
                st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', color='los', text_auto='.1f', color_continuous_scale='Purples'), use_container_width=True)
            with g_col4:
                st.write("**거래처별 평균 리드타임**")
                st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', color='lead_time', text_auto='.1f', color_continuous_scale='Oranges'), use_container_width=True)

            st.write("**글로벌 OTA 국적 비중 분석**")
            global_ota = f_curr[f_curr['is_global_ota'] == True]
            if not global_ota.empty:
                st.plotly_chart(px.bar(global_ota, x="account", color="country", barmode="stack", text_auto=True), use_container_width=True)

        # --- 탭 구성 및 날짜 필터링 ---
        tab1, tab2, tab3 = st.tabs(["📅 Daily (일간 예약)", "📊 Weekly (주간 예약)", "📈 Monthly (월간 예약)"])

        with tab1:
            st.info(f"오늘 예약 생성일 기준: {latest_booking_date.date()}")
            render_booking_dashboard(data[data['예약일'] == latest_booking_date], data[data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY")
        
        with tab2:
            this_week_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
            prev_week_start = this_week_start - timedelta(days=7)
            render_booking_dashboard(data[data['예약일'] >= this_week_start], data[(data['예약일'] >= prev_week_start) & (data['예약일'] < this_week_start)], "WEEKLY")
            
        with tab3:
            this_month_start = latest_booking_date.replace(day=1)
            prev_month_end = this_month_start - timedelta(days=1)
            prev_month_start = prev_month_end.replace(day=1)
            render_booking_dashboard(data[data['예약일'] >= this_month_start], data[(data['예약일'] >= prev_month_start) & (data['예약일'] < this_month_start)], "MONTHLY")

        # AI 분석 버튼
        st.divider()
        if st.button("🤖 AI 전문가 수익 & 조식 전략 리포트"):
            if api_key:
                with st.spinner("AI가 수익 및 조식 비중을 분석 중입니다..."):
                    summary = f"오늘 예약매출:{data[data['예약일']==latest_booking_date]['객실매출액'].sum():,.0f}원, 조식포함비중:{len(data[data['breakfast_status']=='조식포함'])/len(data)*100:.1f}%"
                    st.info(get_ai_insight(api_key, summary + " 조식 포함 비중과 거래처별 특성을 분석하여 부대시설 매출 증대 방안을 제안해줘."))
            else:
                st.warning("사이드바에 API Key를 넣어주세요.")
