import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 경영분석 v9.3", layout="wide")

# 대시보드 스타일
st.markdown("""<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }</style>""", unsafe_allow_html=True)

# 2. 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.info("입력하신 키는 세션 종료 시 자동으로 파기됩니다.")
    st.divider()
    st.caption("v9.3: 전체/FIT 조식 비중 지표화 및 거래처 필터링")

st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 분석 대시보드")
st.caption("예약 생성일 기준 실적 및 세그먼트/거래처별 조식 기여도 정밀 리포트")

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

            # --- 4구역: 조식 핵심 지표 (사장님 요청사항: 전체 및 FIT 분리) ---
            st.subheader(f"🍳 [{title_label}] 조식 포함 비중 핵심 요약")
            bf1, bf2, bf3 = st.columns(3)
            
            # 전체 조식 비중
            total_count = len(target_df)
            bf_total_count = len(target_df[target_df['breakfast_status'] == '조식포함'])
            bf_total_ratio = (bf_total_count / total_count * 100) if total_count > 0 else 0
            
            # FIT 조식 비중
            fit_total_count = len(f_curr)
            bf_fit_count = len(f_curr[f_curr['breakfast_status'] == '조식포함'])
            bf_fit_ratio = (bf_fit_count / fit_total_count * 100) if fit_total_count > 0 else 0
            
            bf1.metric("전체 예약 중 조식 비중", f"{bf_total_ratio:.1f}%", f"{bf_total_count}건 / {total_count}건")
            bf2.metric("FIT 예약 중 조식 비중", f"{bf_fit_ratio:.1f}%", f"{bf_fit_count}건 / {fit_total_count}건")
            bf3.write("💡 그룹을 제외한 개별 고객(FIT)의 조식 선택 성향을 확인하세요.")

            st.divider()

            # --- 5구역: 조식 상세 그래프 (지정 거래처 필터링) ---
            st.subheader("📈 지정 거래처별 조식 포함 예약 비중")
            
            # 사장님 요청 거래처 리스트
            target_accounts = [
                '아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', 
                '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', 
                '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal'
            ]
            
            def normalize_acc(x):
                return str(x).lower().replace(" ", "")

            target_df['acc_norm'] = target_df['account'].apply(normalize_acc)
            normalized_targets = [normalize_acc(a) for a in target_accounts]
            
            filtered_acc_df = target_df[target_df['acc_norm'].isin(normalized_targets)]
            
            if not filtered_acc_df.empty:
                acc_bf_stats = filtered_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0)
                if '조식포함' in acc_bf_stats.columns:
                    row_totals = acc_bf_stats.sum(axis=1)
                    acc_bf_stats['조식선택률'] = (acc_bf_stats['조식포함'] / row_totals) * 100
                    acc_bf_stats['예약건수'] = row_totals
                    acc_bf_plot = acc_bf_stats.reset_index().sort_values('조식선택률', ascending=False)
                    
                    fig_acc_bf = px.bar(acc_bf_plot, x='조식선택률', y='account', orientation='h',
                                        text=acc_bf_plot.apply(lambda r: f"{r['조식선택률']:.1f}% ({int(r['예약건수'])}건)", axis=1),
                                        color='조식선택률', color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig_acc_bf, use_container_width=True)
                else:
                    st.info("지정된 거래처 중 조식 포함 예약이 없습니다.")
            else:
                st.info("지정된 거래처 데이터가 없습니다.")

            st.divider()

            # --- 6구역: 행동 지표 (FIT 중심) ---
            st.subheader("📊 고객 행동 분석 (FIT 고객 중심)")
            b1, b2, b3 = st.columns(3)
            fit_lead = f_curr['lead_time'].mean() if not f_curr.empty else 0
            fit_los = f_curr['los'].mean() if not f_curr.empty else 0
            b1.metric("📅 평균 리드타임 (FIT)", f"{fit_lead:.1f}일")
            b2.metric("🌙 평균 숙박일수 (FIT LOS)", f"{fit_los:.1f}박")
            nc = f_curr['country'].value_counts(normalize=True).head(3) * 100
            b3.metric("🌍 FIT 주요 국적비", " / ".join([f"{k}: {v:.1f}%" for k, v in nc.to_dict().items()]))

            st.divider()

            # --- 7구역: 기존 시각화 그래프 5종 (무삭제 유지) ---
            st.subheader("📈 채널 및 거래처 심층 시각화")
            pure_acc = f_curr[~f_curr['account'].str.contains('마이스|그룹', na=False, case=False)]
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

        # --- 탭 구성 ---
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
                with st.spinner("AI가 분석 중입니다..."):
                    summary = f"전체조식비율:{bf_total_ratio:.1f}%, FIT조식비율:{bf_fit_ratio:.1f}%"
                    st.info(get_ai_insight(api_key, summary + " 조식 비중을 분석하여 업셀링 전략을 제안해줘."))
