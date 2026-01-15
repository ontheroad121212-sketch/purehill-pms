import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v12.9", layout="wide")

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
    
    # 실시간 수정 가능한 targets 딕셔너리 생성
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
    st.caption("v12.9: 사장님 전용 무삭제 관제탑")

st.title("🏛️ 엠버퓨어힐 전략분석 및 AI 경영 관제탑")

# 3. 파일 업로드 및 데이터 처리
col_up1, col_up2 = st.columns(2)
with col_up1:
    prod_file = st.file_uploader("1. 예약 생성 실적 파일 (Production)", type=['csv', 'xlsx'])
with col_up2:
    otb_files = st.file_uploader("2. 영업 현황 온더북 파일 (OTB)", type=['csv', 'xlsx'], accept_multiple_files=True)

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

        # 데이터 분리
        f_curr = curr_df[curr_df['market_segment'] == 'FIT']
        g_curr = curr_df[curr_df['market_segment'] == 'Group']
        
        # 전체 성과 계산
        t_tot, t_room, t_rn, t_adr = calc_metrics(curr_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(prev_df)

        st.subheader(f"✅ [{title_label} 실적 직관 대조]")
        st.info(f"📊 현재 분석: {current_label} | 비교 대상: {prev_label}")
        
        # 1구역: KPI 직관 대조 카드 (사장님 요청: 전일/전주 데이터 노출)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 매출액(Gross)", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("객실 ADR (Net)", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")

        # Monthly 탭에서만 버짓 게이지 표시
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

        st.write("---")
        # 2구역: FIT vs Group 세그먼트별 매출/RN/객단가 (무삭제)
        st.subheader("👤 세그먼트별 상세 성과 (순수 객실 기준)")
        fc_tot, fc_room, fc_rn, fc_adr = calc_metrics(f_curr)
        gc_tot, gc_room, gc_rn, gc_adr = calc_metrics(g_curr)
        
        col_f, col_g = st.columns(2)
        with col_f:
            st.write("**[FIT 세그먼트]**")
            st.metric("FIT 매출", f"{fc_room:,.0f}원", f"{fc_rn:,.0f} RN")
            st.metric("FIT 객단가(ADR)", f"{fc_adr:,.0f}원")
        with col_g:
            st.write("**[Group 세그먼트]**")
            st.metric("그룹 매출", f"{gc_room:,.0f}원", f"{gc_rn:,.0f} RN")
            st.metric("그룹 객단가(ADR)", f"{gc_adr:,.0f}원")

        st.write("---")
        # 3구역: 거래처별 심층 분석 (LOS, 리드타임 포함 4종 그래프 - 무삭제)
        st.subheader("📊 거래처별 심층 분석 (마이스/그룹 제외 FIT)")
        pure_f = f_curr[~f_curr['account'].str.contains('마이스|그룹|GRP|MICE', na=False, case=False)]
        acc_stats = pure_f.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['Net_ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']

        cg1, cg2 = st.columns(2)
        with cg1: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with cg2: st.plotly_chart(px.bar(acc_stats.sort_values('Net_ADR').tail(10), x='Net_ADR', y='account', orientation='h', title="거래처별 객실 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='Net_ADR'), use_container_width=True)
        
        cg3, cg4 = st.columns(2)
        with cg3: st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', title="거래처별 평균 LOS (박수)", text_auto='.1f', color_continuous_scale='Purples', color='los'), use_container_width=True)
        with cg4: st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', title="거래처별 평균 리드타임 (일)", text_auto='.1f', color_continuous_scale='Oranges', color='lead_time'), use_container_width=True)

        # 4구역: 글로벌 채널 국적 비중 (무삭제)
        st.write("---")
        g_channels = ['아고다', 'AGODA', '익스피디아', 'EXPEDIA', '부킹', 'BOOKING', '트립', 'TRIP']
        gl_df = f_curr[f_curr['account'].str.upper().str.contains('|'.join(g_channels), na=False)]
        if not gl_df.empty:
            st.plotly_chart(px.bar(gl_df, x="account", color="country", title="글로벌 OTA 채널별 국적 비중", barmode="stack", text_auto=True), use_container_width=True)

        # 5구역: 조식 분석 (v11.9 로직 무삭제 보존)
        st.write("---")
        st.subheader("🍳 지정 거래처 조식 선택률 분석")
        targets_acc = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        f_acc_df = curr_df[curr_df['account'].str.lower().str.replace(" ", "").isin([a.lower().replace(" ","") for a in targets_acc])]
        if not f_acc_df.empty:
            bf_s = f_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in bf_s.columns:
                bf_s['ratio'] = (bf_s['조식포함'] / bf_s.iloc[:, 1:].sum(axis=1)) * 100
                st.plotly_chart(px.bar(bf_s.sort_values('ratio', ascending=False), x='ratio', y='account', orientation='h', title="거래처별 조식 선택률 (%)", text_auto='.1f', color='ratio', color_continuous_scale='YlOrRd'), use_container_width=True)

        if st.button(f"🤖 AI [{title_label}] 경영 리포트", key=f"ai_{title_label}"):
            if api_key:
                with st.spinner("AI가 데이터를 정밀 분석 중..."):
                    st.info(get_ai_insight(api_key, f"매출:{t_tot:,.0f}, RN:{t_rn}, ADR:{t_adr:,.0f} 실적을 과거 대비 분석하여 뾰족한 전략을 제안해줘."))

    # 4. 탭 구성 및 날짜 필터링 (v12.9 직관적 대조 연동)
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🚀 Future OTB (전략관제)"])

    with tab_d:
        render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], 
                                prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], 
                                "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], 
                                prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], 
                                "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], 
                                prod_data[(prod_data['예약일'] >= (m_start - timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], 
                                "MONTHLY", "이번달", "지난달")

    # 5. 미래 OTB 관제탑 (무삭제 로직)
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 향후 4개월 월별 버짓 달성 현황 (OTB 확정 데이터)")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            
            cur_m = latest_booking_date.month
            for i in range(4):
                t_m = (cur_m - 1 + i) % 12 + 1
                m_data = otb_future[otb_future['일자_dt'].dt.month == t_m]
                if not m_data.empty:
                    m_b = targets.get(t_m)
                    with st.expander(f"📌 {t_m}월 OTB 버짓 달성도 상세보기", expanded=(i==0)):
                        fg1, fg2, fg3, fg4 = st.columns(4)
                        fg1.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_매출'].sum()/m_b['rev_won'])*100, title={'text':"매출달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg2.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_객실'].sum()/m_b['rn'])*100, title={'text':"RN달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg3.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['합계_ADR'].mean()/m_b['adr'])*100, title={'text':"ADR달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg4.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(m_data['점유율'].mean()/m_b['occ'])*100, title={'text':"OCC달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            
            st.divider()
            st.subheader("📈 미래 예약 페이스(Pace) 분석")
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_p.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_p.update_layout(yaxis2=dict(overlaying='y', side='right'), title="날짜별 점유율 vs ADR 추이")
            st.plotly_chart(fig_p, use_container_width=True)
            
            cs1, cs2 = st.columns(2)
            with cs1: st.plotly_chart(px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실'], title="세그먼트 믹스 (Room Nights)"), use_container_width=True)
            with cs2: st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자', title="수익 최적화 매트릭스"), use_container_width=True)

            if st.button("🤖 AI 미래 전략 리포트"):
                if api_key: st.info(get_ai_insight(api_key, "향후 4개월 버짓 대비 OTB 현황을 보고 수익 극대화 전략을 제안해줘."))
else:
    st.info("실적 파일을 업로드하여 경영 관제를 시작하세요.")
