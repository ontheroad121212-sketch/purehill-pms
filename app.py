import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 전략관제 v12.5", layout="wide")

# 대시보드 스타일
st.markdown("""
<style>
    .stMetric { background-color: #f1f3f9; padding: 20px; border-radius: 12px; border-left: 8px solid #1f77b4; box-shadow: 3px 3px 10px rgba(0,0,0,0.1); }
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

# 🚀 [v12.5] 사장님이 주신 이미지 데이터 기반 12개월 4대 타겟(Budget) 완전 박제
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

# 2. 사이드바
with st.sidebar:
    st.header("🎯 경영 목표 및 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.divider()
    
    # 12개월 타겟 설정 (사장님이 주신 v11.9 expander 유지)
    targets = {}
    with st.expander("📅 12개월 경영 목표 셋팅 (펼치기)", expanded=False):
        st.info("각 월별 목표 매출(억원)과 RN을 입력하세요.")
        cols = st.columns(2)
        for i in range(1, 13):
            with cols[0 if i <= 6 else 1]:
                st.write(f"**[{i}월]**")
                rev = st.number_input(f"{i}월 매출(억)", value=BUDGET_DATA[i]['rev']/100000000, step=0.5, key=f"rev_{i}")
                rn = st.number_input(f"{i}월 RN", value=BUDGET_DATA[i]['rn'], step=100, key=f"rn_{i}")
                targets[i] = {"rev_won": rev * 100000000, "rn": rn}
    
    st.divider()
    target_occ = st.number_input("기준 점유율 (%)", value=85, help="AI가 이 점유율을 기준으로 부진 날짜를 판단합니다.")
    target_adr = st.number_input("기준 ADR (만원)", value=60) * 10000
    st.divider()
    st.info("💡 실적 파일 1개와 OTB 파일 여러 개를 동시에 선택해서 올리세요.")
    st.caption("v12.5: 버짓 데이터 완전 연동 및 4개월 OTB 관제탑")

st.title("🏛️ 엠버퓨어힐 전략분석 및 AI 경영 관제탑")

# 3. 파일 업로드 구역
col_up1, col_up2 = st.columns(2)
with col_up1:
    prod_file = st.file_uploader("1. 예약 생성 실적 파일 (Production)", type=['csv', 'xlsx'])
with col_up2:
    otb_files = st.file_uploader("2. 영업 현황 온더북 파일 (OTB) - 다중 선택 가능", type=['csv', 'xlsx'], accept_multiple_files=True)

# 데이터 로드
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

    # --- 메인 대시보드 함수 (v11.9 로직 단 한 줄도 수정 없이 보존) ---
    def render_booking_dashboard(target_df, compare_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        f_curr, f_prev = target_df[target_df['market_segment'] == 'FIT'], compare_df[compare_df['market_segment'] == 'FIT']
        g_curr, g_prev = target_df[target_df['market_segment'] == 'Group'], compare_df[compare_df['market_segment'] == 'Group']
        
        t_tot, t_room, t_rn, t_adr = calc_metrics(target_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(compare_df)

        st.subheader(f"✅ [{title_label} TOTAL 예약 성과]")
        
        # Monthly 탭 게이지 (v11.9 로직 보존)
        if title_label == "MONTHLY":
            curr_month_target = targets.get(analysis_month, {"rev_won": 1200000000, "rn": 1600})
            st.info(f"📊 {analysis_month}월 경영 목표 대비 실적 달성 현황")
            gauge_col1, gauge_col2 = st.columns(2)
            with gauge_col1:
                rev_pct = (t_tot / curr_month_target['rev_won']) * 100 if curr_month_target['rev_won'] > 0 else 0
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=rev_pct, title={'text':f"{analysis_month}월 매출 달성률(%)"}, gauge={'bar':{'color':"#1f77b4"}})).update_layout(height=250, margin=dict(t=50,b=0,l=30,r=30)), use_container_width=True)
            with gauge_col2:
                rn_pct = (t_rn / curr_month_target['rn']) * 100 if curr_month_target['rn'] > 0 else 0
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=rn_pct, title={'text':f"{analysis_month}월 RN 달성률(%)"}, gauge={'bar':{'color':"#2ca02c"}})).update_layout(height=250, margin=dict(t=50,b=0,l=30,r=30)), use_container_width=True)

        st.caption(f"기준: {current_label} (비교대상: {prev_label})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 예약금액", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("평균 ADR", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")
        st.write("---")

        # 세그먼트 상세 (FIT & Group)
        st.subheader(f"👤 [{title_label} 세그먼트 상세]")
        fc_tot, fc_room, fc_rn, fc_adr = calc_metrics(f_curr)
        gc_tot, gc_room, gc_rn, gc_adr = calc_metrics(g_curr)
        f1, f2, g1, g2 = st.columns(4)
        f1.metric("FIT 매출", f"{fc_room:,.0f}원", f"{fc_rn:,.0f} RN")
        f2.metric("FIT ADR", f"{fc_adr:,.0f}원")
        g1.metric("Group 매출", f"{gc_room:,.0f}원", f"{gc_rn:,.0f} RN")
        g2.metric("Group ADR", f"{gc_adr:,.0f}원")
        st.divider()

        # 조식 분석 (14개 지정 거래처)
        st.subheader("🍳 조식 포함 비중 및 지정 채널 선택률")
        target_accounts = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        target_df['acc_norm'] = target_df['account'].str.lower().str.replace(" ", "")
        normalized_targets = [a.lower().replace(" ","") for a in target_accounts]
        filtered_acc_df = target_df[target_df['acc_norm'].isin(normalized_targets)]
        if not filtered_acc_df.empty:
            acc_bf_stats = filtered_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in acc_bf_stats.columns:
                acc_bf_stats['total'] = acc_bf_stats.iloc[:, 1:].sum(axis=1)
                acc_bf_stats['ratio'] = (acc_bf_stats['조식포함'] / acc_bf_stats['total']) * 100
                acc_bf_plot = acc_bf_stats.sort_values('ratio', ascending=False)
                acc_bf_plot['label'] = acc_bf_plot.apply(lambda r: f"{r['ratio']:.1f}% ({int(r['total'])}건)", axis=1)
                st.plotly_chart(px.bar(acc_bf_plot, x='ratio', y='account', orientation='h', text='label', color='ratio', color_continuous_scale='YlOrRd'), use_container_width=True)
        st.divider()

        # 리드타임 ADR
        st.subheader("📅 예약 리드타임별 판매 단가(ADR) 분석")
        target_df['lead_group'] = pd.cut(target_df['lead_time'], bins=[-1, 7, 14, 30, 60, 999], labels=['1주이내', '1-2주', '2-4주', '1-2개월', '2개월이상'])
        lead_adr = target_df.groupby('lead_group', observed=False).agg({'객실매출액':'sum', 'room_nights':'sum'}).reset_index()
        lead_adr['ADR'] = lead_adr['객실매출액'] / lead_adr['room_nights']
        st.plotly_chart(px.line(lead_adr, x='lead_group', y='ADR', markers=True, title="예약 시점에 따른 평균 단가 추이"), use_container_width=True)
        st.write("---")

        # 생산성 5종 그래프 (전 기능 유지)
        pure_acc = f_curr[~f_curr['account'].str.contains('마이스|그룹', na=False, case=False)]
        acc_stats = pure_acc.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
        g1_col, g2_col = st.columns(2)
        with g1_col: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with g2_col: st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', title="거래처별 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='ADR'), use_container_width=True)
        
        # AI 리포트
        if st.button(f"🤖 AI 전문가 [{title_label}] 전략 리포트", key=f"ai_btn_{title_label}"):
            if api_key:
                with st.spinner("분석 중..."):
                    m_target = targets.get(analysis_month, {"rev_won": 1200000000, "rn": 1600})
                    prompt = f"[엠버퓨어힐 GM 브리핑 - {analysis_month}월]\n- 목표: 매출 {m_target['rev_won']:,.0f}원 / RN {m_target['rn']}RN\n- 현재실적: 매출 {t_tot:,.0f} / 판매 {t_rn} 분석해줘."
                    st.info(get_ai_insight(api_key, prompt))

    # --- 탭 구성 ---
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🚀 Future OTB (전략관제)"])

    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        pm_start = w_start - timedelta(days=7)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= pm_start) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        pm_start = (m_start - timedelta(days=1)).replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= pm_start) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")

    # --- 탭 4: 미래 OTB 고도화 및 4개월 버짓 달성 현황 (핵심 추가 구역) ---
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 미래 수익 관리 및 향후 4개월 버짓 달성 현황")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            
            # 🚀 [v12.5 핵심 추가] 당월 포함 향후 4개월 월별 버짓 달성도 분석
            current_month = latest_booking_date.month
            st.write("### 🎯 월별 OTB 확정 데이터 기반 목표 달성 현황")
            for i in range(4):
                target_month = (current_month - 1 + i) % 12 + 1
                month_data = otb_future[otb_future['일자_dt'].dt.month == target_month]
                
                if not month_data.empty:
                    # 박제된 버짓 데이터 매칭
                    m_budget = BUDGET_DATA.get(target_month)
                    f_rev, f_rn = month_data['합계_매출'].sum(), month_data['합계_객실'].sum()
                    f_adr, f_occ = month_data['합계_ADR'].mean(), month_data['점유율'].mean()
                    
                    with st.expander(f"📌 {target_month}월 OTB 달성 현황 (Budget 대비)", expanded=(i==0)):
                        g1, g2, g3, g4 = st.columns(4)
                        g1.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_rev/m_budget['rev'])*100, title={'text':"매출달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        g2.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_rn/m_budget['rn'])*100, title={'text':"RN달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        g3.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_adr/m_budget['adr'])*100, title={'text':"ADR달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        g4.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_occ/m_budget['occ'])*100, title={'text':"OCC달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            st.divider()

            # 미래 관제 지표
            f_o1, f_o2, f_o3, f_o4 = st.columns(4)
            f_o1.metric("향후 평균 점유율", f"{otb_future['점유율'].mean():.1f}%")
            f_o2.metric("향후 평균 ADR", f"{otb_future['합계_ADR'].mean():,.0f}원")
            f_o3.metric("최고 매출 예상일", f"{otb_future.loc[otb_future['합계_매출'].idxmax(), '일자']}")
            f_o4.metric("누적 대기 매출", f"{otb_future['합계_매출'].sum():,.0f}원")
            
            # Pace 분석 (v11.9 로직 유지)
            st.write("---")
            st.subheader("📈 미래 예약 가속도(Pace): 점유율 vs ADR")
            fig_pace = go.Figure()
            fig_pace.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_pace.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_pace.update_layout(yaxis2=dict(overlaying='y', side='right'), title="날짜별 점유율 및 ADR 추이", hovermode='x unified')
            st.plotly_chart(fig_pace, use_container_width=True)

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                st.write("**🛌 개인(FIT) vs 단체(Group) 예약 비중**")
                st.plotly_chart(px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실']), use_container_width=True)
            with col_sub2:
                st.write("**💸 수익 최적화 매트릭스**")
                st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자'), use_container_width=True)

            if st.button("🤖 AI 전문가 미래 수익 전략 리포트"):
                if api_key:
                    with st.spinner("분석 중..."):
                        high_occ = otb_future[otb_future['점유율'] > 80]['일자'].tolist()[:5]
                        st.info(get_ai_insight(api_key, f"평균점유율:{otb_future['점유율'].mean():.1f}%, 만실임박:{high_occ} 데이터를 기반으로 가격 전략을 제안해줘."))
        else: st.warning("온더북 파일을 업로드하세요.")
else: st.info("실적 파일을 업로드하여 경영 관제를 시작하세요.")
