import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime
import pandas as pd
import calendar

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v15.5", layout="wide")

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
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
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
    target_occ_ref = st.number_input("AI 판단 점유율 기준 (%)", value=85)
    st.caption("v15.5: 진짜 최종 무삭제 완결본")

st.title("🏛️ 엠버퓨어힐 전략분석 및 AI 경영 관제탑")

# 3. 데이터 로드 및 처리
col_up1, col_up2 = st.columns(2)
with col_up1: prod_file = st.file_uploader("1. 실적 (Production)", type=['csv', 'xlsx'])
with col_up2: otb_files = st.file_uploader("2. 온더북 (OTB)", type=['csv', 'xlsx'], accept_multiple_files=True)

prod_data = process_data(prod_file, is_otb=False) if prod_file else pd.DataFrame()
otb_data = process_data(otb_files, is_otb=True) if otb_files else pd.DataFrame()

if not prod_data.empty:
    latest_booking_date = prod_data['예약일'].max()
    analysis_month = latest_booking_date.month

    def calc_metrics(df):
        total_sales = df['총매출액'].sum()
        room_sales = df['객실매출액'].sum()
        rn = df['room_nights'].sum()
        adr = room_sales / rn if rn > 0 else 0
        return total_sales, room_sales, rn, adr

    def render_booking_dashboard(curr_df, prev_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        # 성과 계산
        t_tot, t_room, t_rn, t_adr = calc_metrics(curr_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(prev_df)

        st.subheader(f"✅ [{title_label} TOTAL 실적 직관 대조]")
        st.info(f"📊 현재: {current_label} vs 과거: {prev_label}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 매출액 (Gross)", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("객실 ADR (Net)", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")

        # 조식 비중 분석
        st.write("---")
        st.subheader("🍳 조식 포함 예약 비중 (Segment Breakdown)")
        def get_bf_ratio(df):
            if df.empty: return 0
            total = len(df)
            bf = len(df[df['breakfast_status'] == '조식포함'])
            return (bf / total * 100) if total > 0 else 0

        bc1, bc2, bc3 = st.columns(3)
        bf_total_val = get_bf_ratio(curr_df)
        bf_fit_val = get_bf_ratio(curr_df[curr_df['market_segment'] == 'FIT'])
        bc1.metric("전체 조식 비중", f"{bf_total_val:.1f}%")
        bc2.metric("FIT 조식 비중", f"{bf_fit_val:.1f}%")
        bc3.metric("Group 조식 비중", f"{get_bf_ratio(curr_df[curr_df['market_segment'] == 'Group']):.1f}%")

        # Monthly 버짓 게이지
        if title_label == "MONTHLY":
            m_target = targets.get(analysis_month)
            st.write("---")
            st.write(f"### 🎯 {analysis_month}월 누적 버짓 달성 현황")
            gauges = st.columns(4)
            with gauges[0]: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_tot/m_target['rev_won'])*100, title={'text':"매출달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gauges[1]: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_rn/m_target['rn'])*100, title={'text':"RN달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gauges[2]: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_adr/m_target['adr'])*100, title={'text':"ADR달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with gauges[3]: 
                act_occ = (t_rn / (130 * 30)) * 100
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(act_occ/m_target['occ'])*100, title={'text':"OCC달성(%)"})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

        # FIT / Group 세그먼트 성과 대조
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
            st.write("**[FIT 전체 행동 패턴 분석]**")
            fa1, fa2, fa3 = st.columns(3)
            fa1.metric("FIT 평균 리드타임", f"{f_curr['lead_time'].mean():.1f}일")
            fa2.metric("FIT 평균 LOS", f"{f_curr['los'].mean():.1f}박")
            fa3.metric("FIT 최다 투숙 국적", f_curr['country'].value_counts().index[0])
            st.plotly_chart(px.pie(f_curr, names='country', title="FIT 전체 국적 비중", hole=0.4), use_container_width=True)

        st.write("---")
        st.subheader("👥 Group 세그먼트 성과 대조")
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("그룹 총매출", f"{gt_tot:,.0f}원", delta=f"{get_delta_pct(gt_tot, gp_tot)} (전기: {gp_tot:,.0f})")
        gc2.metric("그룹 객실매출", f"{gt_room:,.0f}원", delta=f"{get_delta_pct(gt_room, gp_room)} (전기: {gp_room:,.0f})")
        gc3.metric("그룹 RN", f"{gt_rn:,.0f} RN", delta=f"{int(gt_rn - gp_rn):+d} RN")
        gc4.metric("그룹 ADR (Net)", f"{gt_adr:,.0f}원", delta=f"{get_delta_pct(gt_adr, gp_adr)}")

        st.write("---")
        # FIT 거래처 심층 분석
        st.subheader("📊 FIT 거래처별 심층 분석 (마이스/그룹 제외)")
        pure_f = f_curr[~f_curr['account'].str.contains('마이스|그룹|GRP|MICE', na=False, case=False)]
        acc_stats = pd.DataFrame()
        if not pure_f.empty:
            acc_stats = pure_f.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
            acc_stats['Net_ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
            g_col1, g_col2 = st.columns(2)
            with g_col1: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
            with g_col2: st.plotly_chart(px.bar(acc_stats.sort_values('Net_ADR').tail(10), x='Net_ADR', y='account', orientation='h', title="거래처별 객실 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='Net_ADR'), use_container_width=True)
            g_col3, g_col4 = st.columns(2)
            with g_col3: st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', title="거래처별 평균 LOS", text_auto='.1f', color_continuous_scale='Purples', color='los'), use_container_width=True)
            with g_col4: st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', title="거래처별 평균 리드타임", text_auto='.1f', color_continuous_scale='Oranges', color='lead_time'), use_container_width=True)

        # 글로벌 OTA 분석
        st.write("---")
        gl_ch = ['아고다', 'AGODA', '익스피디아', '부킹', '트립']
        gl_df = f_curr[f_curr['account'].str.upper().str.contains('|'.join(gl_ch), na=False)]
        if not gl_df.empty:
            st.plotly_chart(px.bar(gl_df, x="account", color="country", title="글로벌 OTA 채널별 국적 비중", barmode="stack", text_auto=True), use_container_width=True)
        
        # 조식 선택률 분석
        targets_acc = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        f_acc_df = curr_df[curr_df['account'].str.lower().str.replace(" ", "").isin([a.lower().replace(" ","") for a in targets_acc])]
        if not f_acc_df.empty:
            st.write("---")
            st.subheader("🍳 지정 거래처 조식 선택률 분석")
            bf_s = f_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in bf_s.columns:
                bf_s['ratio'] = (bf_s['조식포함'] / bf_s.iloc[:, 1:].sum(axis=1)) * 100
                st.plotly_chart(px.bar(bf_s.sort_values('ratio', ascending=False), x='ratio', y='account', orientation='h', title="거래처별 조식 선택률 (%)", color_continuous_scale='YlOrRd', color='ratio'), use_container_width=True)

        # 🚀 [v15.7 매트릭스 긴급 복구] 예약생성일 기준 -> 체크인 분포 분석
        if not curr_df.empty:
            st.write("---")
            st.subheader(f"🎯 [{title_label}] 생성 예약의 체크인 날짜별 수요 매트릭스")
            
            # 💡 [핵심 수정] 날짜형 컬럼 중 '예약일'이 아닌 다른 날짜 컬럼(투숙일)을 자동으로 찾습니다.
            all_date_cols = curr_df.select_dtypes(include=['datetime64']).columns.tolist()
            # '예약일'을 제외한 나머지 날짜 컬럼이 실제 투숙일(Stay Date)입니다.
            stay_date_candidates = [c for c in all_date_cols if '예약' not in c]
            
            # 만약 후보가 없다면 '일자' 혹은 '체크인'이라는 이름이 포함된 컬럼을 강제로 찾음
            if not stay_date_candidates:
                stay_date_candidates = [c for c in curr_df.columns if any(x in c for x in ['일자', '체크인', 'Stay', 'Date'])]
            
            if stay_date_candidates:
                target_date_col = stay_date_candidates[0] # 가장 유력한 투숙일 컬럼 선택
                
                # 데이터 집계
                demand_matrix = curr_df.groupby(target_date_col).agg({'room_nights': 'sum', '객실매출액': 'sum'}).reset_index()
                demand_matrix['Net_ADR'] = demand_matrix['객실매출액'] / demand_matrix['room_nights']
                
                # 차트 생성
                fig_matrix = px.scatter(
                    demand_matrix, 
                    x=target_date_col, 
                    y='Net_ADR', 
                    size='room_nights', 
                    color='room_nights',
                    color_continuous_scale='Viridis', 
                    title=f"현재 선택된 예약들({current_label})의 실제 투숙일(체크인) 분포",
                    labels={target_date_col: '체크인 예정일 (Stay Date)', 'Net_ADR': 'ADR(Net)', 'room_nights': '예약량(RN)'}
                )
                
                # 차트 레이아웃 최적화
                fig_matrix.update_layout(hovermode='closest')
                st.plotly_chart(fig_matrix, use_container_width=True)
            else:
                st.warning("⚠️ 투숙일(체크인 날짜) 데이터를 찾을 수 없어 매트릭스를 표시할 수 없습니다. 데이터의 컬럼명을 확인해주세요.")

        

        # 🚀 [v15.6 뾰족한 AI 리포트 로직] 사장님 요청 페르소나 반영
        if st.button(f"🤖 AI 전문가 [{title_label}] 전략 리포트", key=f"ai_{title_label}"):
            if api_key:
                with st.spinner("전문가가 성과를 정밀 진단 중..."):
                    m_bud = targets.get(analysis_month)
                    top_5_acc_list = "없음"
                    if not acc_stats.empty:
                        top_5_acc_list = acc_stats.sort_values('room_nights', ascending=False).head(5)[['account', 'room_nights', 'Net_ADR']].to_dict('records')
                    
                    prompt = f"""
                    너는 글로벌 럭셔리 호텔 20년 경력의 Revenue Management 전문가다. 사장님(CEO)께 보고하듯 '현상-원인-액션아이템' 구조로 매우 뾰족하게 제언하라.
                    
                    [현재 데이터 요약]
                    - 분석 월: {analysis_month}월 / 분석 주기: {title_label} ({current_label})
                    - 실적: 객실매출 {t_room:,.0f}원, RN {t_rn}, ADR {t_adr:,.0f}원
                    - 전기 대비 추이: 객실매출 {get_delta_pct(t_room, p_room)}, ADR {get_delta_pct(t_adr, p_adr)}
                    - FIT 조식 비중: {bf_fit_val:.1f}% / 주요 거래처 성과: {top_5_acc_list}
                    
                    [전략 지시사항]
                    1. 전기 대비 매출 변동 원인을 글로벌 채널(아고다/익스피디아/부킹닷컴/트립닷컴)의 국적 믹스 및 가격 경쟁력 측면에서 분석하라. 특히 ADR 하락 시 이유를 명확히 할 것.
                    2. 현재 시점 버짓 달성을 위해 남은 기간 매일 최소 몇 실을 얼마에 팔아야 하는지(Shortfall 대응) 구체적인 수치 가이드를 제시하라.
                    3. 조식 비중을 높여 부대수익을 극대화할 수 있는 구체적인 채널별 가격 전략(Add-on 패키징)을 제안하라.
                    4. 수요 매트릭스상 체크인 수요가 몰리는 날짜의 가격 인상 폭과, 부진한 날짜를 채우기 위한 'Flash Sale' 권장 판매가를 숫자로 찍어라.
                    
                    형식: 서술형 제외, 임팩트 있는 불렛포인트로 보고할 것.
                    """
                    st.info(get_ai_insight(api_key, prompt))

    # 4. 탭 구성
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🚀 Future OTB (전략관제)"])
    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= (m_start - timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")

# 5. 미래 OTB 및 시뮬레이션 (tab_f)
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 1월 통합 버짓 달성 현황 및 잔여 일수 시뮬레이션")
            
            # 🔥 [v15.9 핵심 수정] OTB 데이터 클리닝 (소계/총합계 행 제거)
            # 날짜 데이터(일자_dt)가 비어있는 '소계'나 '총합계' 행을 필터링하여 계산 오류를 원천 차단합니다.
            otb_clean = otb_data[otb_data['일자_dt'].notna()].copy()
            
            # 미래 페이스 분석을 위한 오늘 이후 데이터 필터링 (차트용)
            otb_future = otb_clean[otb_clean['일자_dt'] >= latest_booking_date]
            
            # 🔥 [달성률 정상화 핵심] 금월(1월)의 전체 달성 현황 계산
            # OTB 리포트는 과거 날짜의 실적과 미래 예약을 모두 포함하고 있습니다. 
            # 1월 1일부터 31일까지 '전체'를 합쳐야 사장님이 말씀하신 90%대 진짜 수치가 나옵니다.
            cur_month = latest_booking_date.month
            m_bud = targets.get(cur_month)
            
            # 1일부터 31일까지 해당 월의 모든 OTB 데이터를 가져옴 (확정 실적 + 미래 예약 합산)
            month_otb_all = otb_clean[otb_clean['일자_dt'].dt.month == cur_month]
            
            if not month_otb_all.empty:
                st.error(f"🚨 {cur_month}월 버짓 달성 통합 시뮬레이션 (Total Month Analysis)")
                
                # 현재 전체 확보 수치 (이미 지나온 1~14일 실적 + 남은 날짜 예약 합계)
                c_rev = month_otb_all['합계_매출'].sum()
                c_rn = month_otb_all['합계_객실'].sum()
                
                # 달성률 계산
                rev_ach_rate = (c_rev / m_bud['rev_won']) * 100
                rn_ach_rate = (c_rn / m_bud['rn']) * 100
                
                # 📊 상단 통합 달성률 메트릭 (여기서 95%대의 수치가 정확히 찍힙니다)
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("1월 총 확보 매출 (실적+OTB)", f"{c_rev:,.0f}원", delta=f"{rev_ach_rate:.1f}% 달성")
                sc2.metric("1월 총 확보 RN", f"{c_rn:,.0f} RN", delta=f"{rn_ach_rate:.1f}% 달성")
                sc3.metric("1월 현재 ADR (통합)", f"{(c_rev/c_rn if c_rn > 0 else 0):,.0f}원")

                # 🚨 숏폴 시뮬레이션 (Shortfall Analysis)
                st.write("---")
                st.write(f"### 🎯 {cur_month}월 버짓 100% 달성까지 남은 과제")
                
                last_day = calendar.monthrange(latest_booking_date.year, cur_month)[1]
                days_left = last_day - latest_booking_date.day
                
                if days_left > 0:
                    short_rev = max(0, m_bud['rev_won'] - c_rev)
                    short_rn = max(0, m_bud['rn'] - c_rn)
                    
                    req_rn_day = short_rn / days_left
                    req_adr = short_rev / short_rn if short_rn > 0 else 0
                    
                    ss1, ss2, ss3 = st.columns(3)
                    ss1.metric("남은 기간", f"{days_left}일")
                    ss2.metric("일일 필요 판매량", f"{req_rn_day:.1f} RN/일")
                    ss3.metric("필요 평균 단가 (Net)", f"{req_adr:,.0f}원")
                    
                    if rev_ach_rate >= 90:
                        st.success(f"💡 **총지배인 가이드:** 사장님, 현재 {rev_ach_rate:.1f}% 확보로 버짓 돌파 직전입니다! 남은 {days_left}일 동안 하루 {req_rn_day:.1f}실을 {req_adr:,.0f}원에만 팔아도 버짓 100% 돌파합니다.")
                    else:
                        st.warning(f"💡 **분석:** 목표 달성을 위해 남은 {days_left}일간 매일 {req_rn_day:.1f}실을 {req_adr:,.0f}원 이상의 단가로 방어해야 합니다.")
                else:
                    st.info("현재 분석일이 월말이므로 금월 시뮬레이션을 종료합니다.")

            # 📌 향후 4개월 월별 상세 달성 현황 (Expanders)
            st.write("---")
            st.subheader("📅 향후 4개월 월별 버짓 달성 현황")
            
            for i in range(4):
                t_m = (cur_month - 1 + i) % 12 + 1
                m_b = targets.get(t_m)
                
                # 데이터 필터링 (소계 제외된 깨끗한 데이터)
                m_data = otb_clean[otb_clean['일자_dt'].dt.month == t_m]
                
                if not m_data.empty:
                    m_rev_val = m_data['합계_매출'].sum()
                    m_rn_val = m_data['합계_객실'].sum()
                    
                    with st.expander(f"📌 {t_m}월 상세 달성 현황", expanded=(i==0)):
                        fg = st.columns(4)
                        # 매출 게이지
                        fg[0].plotly_chart(go.Figure(go.Indicator(
                            mode="gauge+number", 
                            value=(m_rev_val/m_b['rev_won'])*100, 
                            title={'text':"매출달성(%)"},
                            gauge={'bar':{'color':"#FF4B4B"}}
                        )).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        
                        # RN 게이지
                        fg[1].plotly_chart(go.Figure(go.Indicator(
                            mode="gauge+number", 
                            value=(m_rn_val/m_b['rn'])*100, 
                            title={'text':"RN달성(%)"},
                            gauge={'bar':{'color':"#FF4B4B"}}
                        )).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        
                        # ADR 게이지
                        m_adr_val = (m_rev_val/m_rn_val) if m_rn_val > 0 else 0
                        fg[2].plotly_chart(go.Figure(go.Indicator(
                            mode="gauge+number", 
                            value=(m_adr_val/m_b['adr'])*100, 
                            title={'text':"ADR달성(%)"},
                            gauge={'bar':{'color':"#FF4B4B"}}
                        )).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        
                        # OCC 게이지
                        days_in_m = calendar.monthrange(latest_booking_date.year, t_m)[1]
                        m_occ_val = (m_rn_val / (130 * days_in_m)) * 100
                        fg[3].plotly_chart(go.Figure(go.Indicator(
                            mode="gauge+number", 
                            value=(m_occ_val/m_b['occ'])*100, 
                            title={'text':"OCC달성(%)"},
                            gauge={'bar':{'color':"#FF4B4B"}}
                        )).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

            # 📈 미래 예약 가속도(Pace) 분석 차트
            st.divider()
            st.subheader("📈 미래 예약 가속도(Pace) 분석")
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_p.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_p.update_layout(
                yaxis2=dict(overlaying='y', side='right'), 
                title="날짜별 점유율 vs ADR 추이 (Pace 관제)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_p, use_container_width=True)
            
            # 믹스 분석 차트
            cs1, cs2 = st.columns(2)
            with cs1: st.plotly_chart(px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실'], title="세그먼트 믹스 (Room Nights)"), use_container_width=True)
            with cs2: st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자', title="수익 최적화 매트릭스 (Yield Matrix)"), use_container_width=True)

            if st.button("🤖 AI 미래 전략 리포트"):
                if api_key:
                    with st.spinner("AI 전문가가 수익 전략을 분석 중입니다..."):
                        report = get_ai_insight(api_key, f"현재 1월 달성률 {rev_ach_rate:.1f}% 상황을 분석하고, 남은 {days_left}일간 수익 극대화 전략을 제안해줘.")
                        st.info(report)
