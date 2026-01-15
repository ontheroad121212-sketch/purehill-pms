import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime
import pandas as pd
import calendar

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v15.2", layout="wide")

# 대시보드 스타일 (가독성 및 직관적 대조 강조)
st.markdown("""
<style>
    .stMetric { background-color: #f1f3f9; padding: 20px; border-radius: 12px; border-left: 8px solid #1f77b4; box-shadow: 3px 3px 10px rgba(0,0,0,0.1); }
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; font-size: 1.1rem !important; }
    .reportview-container .main .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# 🚀 [이미지 데이터 기반 12개월 4대 버짓 박제]
BUDGET_DATA = {
    1:  {"rev": 514992575,  "rn": 2270, "adr": 226869, "occ": 56.3},
    2:  {"rev": 786570856,  "rn": 2577, "adr": 305227, "occ": 70.8},
    3:  {"rev": 529599040,  "rn": 2248, "adr": 235587, "occ": 55.8},
    4:  {"rev": 695351004,  "rn": 2414, "adr": 288049, "occ": 61.9},
    5:  {"rev": 903705440,  "rn": 3082, "adr": 293220, "occ": 76.5},
    6:  {"rev": 808203820,  "rn": 2776, "adr": 291140, "occ": 71.2},
    7:  {"rev": 1231949142, "rn": 3671, "adr": 335590, "occ": 91.1},
    8:  {"rev": 1388376999, "rn": 3873, "adr": 358476, "occ": 96.1},
    9:  {"rev": 952171506,  "rn": 2932, "adr": 324752, "occ": 75.2},
    10: {"rev": 897171539,  "rn": 3009, "adr": 298163, "occ": 74.7},
    11: {"rev": 667146771,  "rn": 2402, "adr": 277746, "occ": 61.6},
    12: {"rev": 804030110,  "rn": 2765, "adr": 290788, "occ": 68.6}
}

# 2. 사이드바 (경영 타겟 관리)
with st.sidebar:
    st.header("🎯 경영 타겟 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="키를 입력하세요")
    st.divider()
    
    targets = {}
    with st.expander("📅 12개월 버짓 확인 및 수정", expanded=False):
        st.info("이미지 데이터가 기본값으로 적용되어 있습니다.")
        cols = st.columns(2)
        for i in range(1, 13):
            with cols[0 if i <= 6 else 1]:
                st.write(f"**[{i}월]**")
                rev_val = st.number_input(f"{i}월 매출(억)", value=BUDGET_DATA[i]['rev']/100000000, key=f"r_{i}")
                rn_val = st.number_input(f"{i}월 RN", value=BUDGET_DATA[i]['rn'], key=f"n_{i}")
                targets[i] = {"rev_won": rev_val * 100000000, "rn": rn_val, "occ": BUDGET_DATA[i]['occ'], "adr": BUDGET_DATA[i]['adr']}
    
    st.divider()
    target_occ_ref = st.number_input("AI 판단 점유율 기준", value=85)
    st.caption("v15.2: 전 기능 통합 무삭제 완결본")

st.title("🏛️ 엠버퓨어힐 전략분석 및 AI 경영 관제탑")

# 3. 데이터 로드 및 처리
col_up1, col_up2 = st.columns(2)
with col_up1: prod_file = st.file_uploader("1. 예약 생성 실적 파일 (Production)", type=['csv', 'xlsx'])
with col_up2: otb_files = st.file_uploader("2. 영업 현황 온더북 파일 (OTB)", type=['csv', 'xlsx'], accept_multiple_files=True)

prod_data = process_data(prod_file, is_otb=False) if prod_file else pd.DataFrame()
otb_data = process_data(otb_files, is_otb=True) if otb_files else pd.DataFrame()

if not prod_data.empty:
    latest_booking_date = prod_data['예약일'].max()
    analysis_month = latest_booking_date.month

    # 🚀 [객실매출 기반 ADR 계산 함수]
    def calc_metrics(df):
        total_sales = df['총매출액'].sum()
        room_sales = df['객실매출액'].sum()
        rn = df['room_nights'].sum()
        adr = room_sales / rn if rn > 0 else 0
        return total_sales, room_sales, rn, adr

    # 🚀 [메인 대시보드 함수 - 비교 대조 강화 및 무삭제]
    def render_booking_dashboard(curr_df, prev_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        # 성과 계산
        t_tot, t_room, t_rn, t_adr = calc_metrics(curr_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(prev_df)

        st.subheader(f"✅ [{title_label} TOTAL 실적 직관 대조]")
        st.info(f"📊 현재: {current_label} vs 과거: {prev_label}")
        
        # 1구역: 전체 KPI 직관 대조 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 매출액 (Gross)", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("객실 ADR (Net)", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")

        # 🚀 [추가 지시] 조식 비중 분석 (전체 / FIT / 그룹)
        st.write("---")
        st.subheader("🍳 조식 포함 예약 비중 (Breakfast Ratio)")
        def get_bf_ratio(df):
            total = len(df)
            bf = len(df[df['breakfast_status'] == '조식포함'])
            return (bf / total * 100) if total > 0 else 0

        bf_total = get_bf_ratio(curr_df)
        bf_fit = get_bf_ratio(curr_df[curr_df['market_segment'] == 'FIT'])
        bf_group = get_bf_ratio(curr_df[curr_df['market_segment'] == 'Group'])

        bc1, bc2, bc3 = st.columns(3)
        bc1.metric("전체 조식 비중", f"{bf_total:.1f}%")
        bc2.metric("FIT 조식 비중", f"{bf_fit:.1f}%")
        bc3.metric("Group 조식 비중", f"{bf_group:.1f}%")

        # Monthly 버짓 게이지
        if title_label == "MONTHLY":
            m_target = targets.get(analysis_month)
            st.write("---")
            st.write(f"### 🎯 {analysis_month}월 누적 버짓 달성 현황")
            gc1, gc2, gc3, gc4 = st.columns(4)
            with gc1: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_tot/m_target['rev_won'])*100, title={'text':"매출달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gc2: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_rn/m_target['rn'])*100, title={'text':"RN달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gc3: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_adr/m_target['adr'])*100, title={'text':"ADR달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gc4: 
                act_occ = (t_rn / (130 * 30)) * 100
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(act_occ/m_target['occ'])*100, title={'text':"OCC달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

        # 🚀 [v15.2] FIT / Group 세그먼트별 개별 대조 (무삭제)
        st.write("---")
        f_curr, f_prev = curr_df[curr_df['market_segment'] == 'FIT'], prev_df[prev_df['market_segment'] == 'FIT']
        g_curr, g_prev = curr_df[curr_df['market_segment'] == 'Group'], prev_df[prev_df['market_segment'] == 'Group']
        ft_tot, ft_room, ft_rn, ft_adr = calc_metrics(f_curr)
        fp_tot, fp_room, fp_rn, fp_adr = calc_metrics(f_prev)
        gt_tot, gt_room, gt_rn, gt_adr = calc_metrics(g_curr)
        gp_tot, gp_room, gp_rn, gp_adr = calc_metrics(g_prev)

        st.subheader("👤 FIT 세그먼트 성과 대조")
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("FIT 총매출", f"{ft_tot:,.0f}원", delta=f"{get_delta_pct(ft_tot, fp_tot)} (전기: {fp_tot:,.0f})")
        fc2.metric("FIT 객실매출", f"{ft_room:,.0f}원", delta=f"{get_delta_pct(ft_room, fp_room)} (전기: {fp_room:,.0f})")
        fc3.metric("FIT RN", f"{ft_rn:,.0f} RN", delta=f"{int(ft_rn - fp_rn):+d} RN")
        fc4.metric("FIT ADR (Net)", f"{ft_adr:,.0f}원", delta=f"{get_delta_pct(ft_adr, fp_adr)}")

        if not f_curr.empty:
            st.write("**[FIT 전체 행동 지표]**")
            fa1, fa2, fa3 = st.columns(3)
            fa1.metric("FIT 평균 리드타임", f"{f_curr['lead_time'].mean():.1f}일")
            fa2.metric("FIT 평균 LOS", f"{f_curr['los'].mean():.1f}박")
            fa3.metric("FIT 주요 국적", f_curr['country'].value_counts().index[0] if not f_curr['country'].empty else "N/A")
            st.plotly_chart(px.pie(f_curr, names='country', title="FIT 전체 국적 비중", hole=0.4), use_container_width=True)

        st.write("---")
        st.subheader("👥 Group 세그먼트 성과 대조")
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("그룹 총매출", f"{gt_tot:,.0f}원", delta=f"{get_delta_pct(gt_tot, gp_tot)} (전기: {gp_tot:,.0f})")
        gc2.metric("그룹 객실매출", f"{gt_room:,.0f}원", delta=f"{get_delta_pct(gt_room, gp_room)} (전기: {gp_room:,.0f})")
        gc3.metric("그룹 RN", f"{gt_rn:,.0f} RN", delta=f"{int(gt_rn - gp_rn):+d} RN")
        gc4.metric("그룹 ADR (Net)", f"{gt_adr:,.0f}원", delta=f"{get_delta_pct(gt_adr, gp_adr)}")

        # 🚀 FIT 거래처 심층 분석 (마이스/그룹 제외 - 무삭제 그래프 4종)
        st.write("---")
        st.subheader("📊 거래처별 심층 분석 (Top 10)")
        pure_f = f_curr[~f_curr['account'].str.contains('마이스|그룹|GRP|MICE', na=False, case=False)]
        acc_stats = pure_f.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['Net_ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
        
        g_c1, g_c2 = st.columns(2)
        with g_c1: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with g_c2: st.plotly_chart(px.bar(acc_stats.sort_values('Net_ADR').tail(10), x='Net_ADR', y='account', orientation='h', title="거래처별 Net ADR", text_auto=',.0f', color_continuous_scale='Greens', color='Net_ADR'), use_container_width=True)
        g_c3, g_c4 = st.columns(2)
        with g_c3: st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', title="거래처별 평균 LOS", text_auto='.1f', color_continuous_scale='Purples', color='los'), use_container_width=True)
        with g_c4: st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', title="거래처별 평균 리드타임", text_auto='.1f', color_continuous_scale='Oranges', color='lead_time'), use_container_width=True)

        # 글로벌 OTA 국적 비중 & 조식 분석 (사장님 최애 로직 - 절대 생략 불가)
        st.write("---")
        gl_list = ['아고다', 'AGODA', '익스피디아', '부킹', '트립']
        gl_df = f_curr[f_curr['account'].str.upper().str.contains('|'.join(gl_list), na=False)]
        if not gl_df.empty:
            st.plotly_chart(px.bar(gl_df, x="account", color="country", title="글로벌 OTA 채널별 국적 비중", barmode="stack", text_auto=True), use_container_width=True)
        
        st.write("---")
        st.subheader("🍳 지정 거래처 조식 선택률 분석")
        targets_acc = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        f_acc_df = curr_df[curr_df['account'].str.lower().str.replace(" ","").isin([a.lower().replace(" ","") for a in targets_acc])]
        if not f_acc_df.empty:
            bf_s = f_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in bf_s.columns:
                bf_s['ratio'] = (bf_s['조식포함'] / bf_s.iloc[:, 1:].sum(axis=1)) * 100
                st.plotly_chart(px.bar(bf_s.sort_values('ratio', ascending=False), x='ratio', y='account', orientation='h', title="거래처별 조식 선택률 (%)", color_continuous_scale='YlOrRd', color='ratio'), use_container_width=True)

        # 🚀 [v15.2] 수요 집중도 분석 매트릭스
        st.write("---")
        st.subheader(f"🎯 [{title_label}] 수요 집중도 분석 (Stay Date Matrix)")
        if not curr_df.empty:
            demand_matrix = curr_df.groupby('일자').agg({'room_nights': 'sum', '객실매출액': 'sum'}).reset_index()
            demand_matrix['Net_ADR'] = demand_matrix['객실매출액'] / demand_matrix['room_nights']
            st.plotly_chart(px.scatter(demand_matrix, x='일자', y='Net_ADR', size='room_nights', color='room_nights', color_continuous_scale='Viridis', title="투숙일별 예약 현황 (원 크기=RN)"), use_container_width=True)

        if st.button(f"🤖 AI [{title_label}] 전략 리포트", key=f"ai_{title_label}"):
            if api_key:
                with st.spinner("전문가가 실적을 분석 중..."):
                    m_bud = targets.get(analysis_month)
                    st.info(get_ai_insight(api_key, f"매출:{t_room:,.0f}, RN:{t_rn}, ADR:{t_adr:,.0f} 실적을 버짓 {m_bud['rev_won']:,.0f} 대비 분석해줘."))

    # 4. 탭 구성
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🚀 Future OTB (관제)"])
    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= (m_start - timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")

    # 🚀 [탭 4: 미래 OTB 및 시뮬레이션 최적화 - 무삭제]
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 향후 4개월 월별 버짓 달성 현황 및 긴급 시뮬레이션")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            cur_month = latest_booking_date.month
            m_bud = targets.get(cur_month)
            month_otb = otb_future[otb_future['일자_dt'].dt.month == cur_month]
            
            if m_bud:
                st.error(f"🚨 {cur_month}월 버짓 달성 긴급 시뮬레이션 (Shortfall Analysis)")
                last_day = calendar.monthrange(latest_booking_date.year, cur_month)[1]
                days_left = last_day - latest_booking_date.day
                c_rev, c_rn = month_otb['합계_매출'].sum() if not month_otb.empty else 0, month_otb['합계_객실'].sum() if not month_otb.empty else 0
                s_rev, s_rn = max(0, m_bud['rev_won'] - c_rev), max(0, m_bud['rn'] - c_rn)
                
                if days_left > 0:
                    req_rn = s_rn / days_left
                    req_adr = s_rev / s_rn if s_rn > 0 else 0
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("남은 기간", f"{days_left}일")
                    sc2.metric("매일 필요 판매량", f"{req_rn:.1f} RN/일")
                    sc3.metric("필요 평균 단가", f"{req_adr:,.0f}원")
                    st.warning(f"💡 가이드: 목표 달성을 위해 남은 {days_left}일간 매일 {req_rn:.1f}실을 {req_adr:,.0f}원에 팔아야 합니다.")

            for i in range(4):
                t_m = (cur_month - 1 + i) % 12 + 1
                m_data = otb_future[otb_future['일자_dt'].dt.month == t_m]
                if not m_data.empty:
                    m_b = targets.get(t_m)
                    with st.expander(f"📌 {t_m}월 OTB 상세 달성 현황", expanded=(i==0)):
                        fg = st.columns(4)
                        fg[0].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_매출'].sum()/m_b['rev_won'])*100, title={'text':"매출달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg[1].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_객실'].sum()/m_b['rn'])*100, title={'text':"RN달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg[2].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_ADR'].mean()/m_b['adr'])*100, title={'text':"ADR달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg[3].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['점유율'].mean()/m_b['occ'])*100, title={'text':"OCC달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

            st.divider()
            st.subheader("📈 미래 예약 Pace 및 수익 매트릭스")
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_p.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_p.update_layout(yaxis2=dict(overlaying='y', side='right'), title="날짜별 점유율 vs ADR 추이")
            st.plotly_chart(fig_p, use_container_width=True)
            
            cs1, cs2 = st.columns(2)
            with cs1: st.plotly_chart(px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실'], title="세그먼트 믹스"), use_container_width=True)
            with cs2: st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자', title="수익 최적화 매트릭스"), use_container_width=True)

            if st.button("🤖 AI 미래 전략 리포트"):
                if api_key: st.info(get_ai_insight(api_key, "향후 4개월 버짓 대비 OTB 현황을 보고 수익 극대화 전략을 제안해줘."))
else:
    st.info("실적 파일을 업로드하여 경영 관제를 시작하세요.")
