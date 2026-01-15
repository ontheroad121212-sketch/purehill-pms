import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 전략관제 v12.1", layout="wide")

# 대시보드 스타일
st.markdown("""
<style>
    .stMetric { background-color: #f1f3f9; padding: 20px; border-radius: 12px; border-left: 8px solid #1f77b4; box-shadow: 3px 3px 10px rgba(0,0,0,0.1); }
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

# 🚀 [v12.1] 이미지 데이터 기반 12개월 4대 타겟(Budget) 완전 박제
# RNS(판매수), ADR(단가), OCC(점유율), REV(매출)
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
    st.header("🎯 경영 목표 관리")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.divider()
    
    with st.expander("📅 내장된 12개월 버짓(Target) 확인", expanded=False):
        st.write("이미지 데이터 기준 (REV/RN/ADR/OCC)")
        budget_df = pd.DataFrame(BUDGET_DATA).T
        budget_df.columns = ['목표매출', '목표RN', '목표ADR', '목표OCC(%)']
        st.dataframe(budget_df.style.format("{:,.0f}"))
    
    st.divider()
    # AI 보조 판단 기준
    target_occ_ref = st.number_input("AI 판단 기준 점유율 (%)", value=85)
    target_adr_ref = st.number_input("AI 판단 기준 ADR (만원)", value=60) * 10000
    st.divider()
    st.info("💡 실적 파일 1개와 OTB 파일 여러 개를 동시에 선택해서 올리세요.")
    st.caption("v12.1: 4대 타겟(매출/RN/ADR/OCC) 완전 통합 무삭제판")

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

    # --- 메인 대시보드 함수 (무삭제 보장) ---
    def render_booking_dashboard(target_df, compare_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        f_curr, f_prev = target_df[target_df['market_segment'] == 'FIT'], compare_df[compare_df['market_segment'] == 'FIT']
        g_curr, g_prev = target_df[target_df['market_segment'] == 'Group'], compare_df[compare_df['market_segment'] == 'Group']
        
        t_tot, t_room, t_rn, t_adr = calc_metrics(target_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(compare_df)

        st.subheader(f"✅ [{title_label} TOTAL 예약 성과]")
        
        # 🚀 Monthly 탭: 4대 타겟 대비 달성률 시각화
        if title_label == "MONTHLY":
            m_target = BUDGET_DATA.get(analysis_month)
            st.info(f"📊 {analysis_month}월 고정 버짓(Target) 대비 실적 달성 현황")
            
            g_col1, g_col2, g_col3, g_col4 = st.columns(4)
            with g_col1:
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_tot/m_target['rev'])*100, 
                    title={'text':"매출 달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#1f77b4"}})).update_layout(height=200, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with g_col2:
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_rn/m_target['rn'])*100, 
                    title={'text':"RN 달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2ca02c"}})).update_layout(height=200, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with g_col3:
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(t_adr/m_target['adr'])*100, 
                    title={'text':"ADR 달성률(%)"}, gauge={'axis':{'range':[0,110]}, 'bar':{'color':"#ff7f0e"}})).update_layout(height=200, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
            with g_col4:
                # 실적 점유율 계산 (130객실 기준)
                actual_occ = (t_rn / (130 * 30)) * 100 # 대략적 계산
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(actual_occ/m_target['occ'])*100, 
                    title={'text':"OCC 달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#9467bd"}})).update_layout(height=200, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

        st.caption(f"기준: {current_label} (비교대상: {prev_label})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 예약금액", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("평균 ADR", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")
        st.write("---")

        # 세그먼트 상세
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
        bf1, bf2 = st.columns(2)
        t_all, t_bf = len(target_df), len(target_df[target_df['breakfast_status']=='조식포함'])
        bf1.metric("전체 조식 비중", f"{(t_bf/t_all*100 if t_all>0 else 0):.1f}%")
        
        target_accounts = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        target_df['acc_norm'] = target_df['account'].str.lower().str.replace(" ", "")
        filtered_acc_df = target_df[target_df['acc_norm'].isin([a.lower().replace(" ","") for a in target_accounts])]
        if not filtered_acc_df.empty:
            acc_bf_stats = filtered_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in acc_bf_stats.columns:
                acc_bf_stats['ratio'] = (acc_bf_stats['조식포함'] / acc_bf_stats.iloc[:,1:].sum(axis=1)) * 100
                st.plotly_chart(px.bar(acc_bf_stats.sort_values('ratio', ascending=False), x='ratio', y='account', orientation='h', title="거래처별 조식 선택률", text_auto='.1f', color='ratio', color_continuous_scale='YlOrRd'), use_container_width=True)
        st.divider()

        # 리드타임 ADR
        st.subheader("📅 예약 리드타임별 판매 단가(ADR) 분석")
        target_df['lead_group'] = pd.cut(target_df['lead_time'], bins=[-1, 7, 14, 30, 60, 999], labels=['1주이내', '1-2주', '2-4주', '1-2개월', '2개월이상'])
        lead_adr = target_df.groupby('lead_group', observed=False).agg({'객실매출액':'sum', 'room_nights':'sum'}).reset_index()
        lead_adr['ADR'] = lead_adr['객실매출액'] / lead_adr['room_nights']
        st.plotly_chart(px.line(lead_adr, x='lead_group', y='ADR', markers=True, title="예약 시점에 따른 평균 단가 추이"), use_container_width=True)
        st.write("---")

        # 생산성 5종 그래프
        acc_stats = f_curr.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
        g1_col, g2_col = st.columns(2)
        with g1_col: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇 생산성", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with g2_col: st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', title="거래처별 객실 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='ADR'), use_container_width=True)
        
        if st.button(f"🤖 AI 전문가 [{title_label}] 전략 리포트", key=f"ai_btn_{title_label}"):
            if api_key:
                m_target = BUDGET_DATA.get(analysis_month)
                prompt = f"""[엠버퓨어힐 GM 브리핑 - {analysis_month}월]
                - 경영목표: 매출 {m_target['rev']:,.0f} / RN {m_target['rn']} / ADR {m_target['adr']:,.0f} / OCC {m_target['occ']}%
                - 현재실적: 매출 {t_tot:,.0f} / RN {t_rn} / ADR {t_adr:,.0f}
                위 목표 대비 성과를 분석하고 뾰족한 전략을 제안해줘."""
                st.info(get_ai_insight(api_key, prompt))

    # 탭 구성
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🚀 Future OTB (전략)"])

    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= (m_start-timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")

    # --- 탭 4: 미래 OTB 고도화 및 4대 지표 달성 현황 ---
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 미래 수익 관리 (Revenue Management) 전략")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            
            # [v12.1 신규] OTB 확정 데이터 기반 4대 지표 달성 게이지
            curr_month_future = otb_future[otb_future['일자_dt'].dt.month == analysis_month]
            if not curr_month_future.empty:
                m_target = BUDGET_DATA.get(analysis_month)
                f_rev, f_rn, f_adr = curr_month_future['합계_매출'].sum(), curr_month_future['합계_객실'].sum(), curr_month_future['합계_ADR'].mean()
                f_occ = curr_month_future['점유율'].mean()
                
                st.write(f"### 🎯 {analysis_month}월 OTB(확정예약) 기반 목표 달성도")
                fg1, fg2, fg3, fg4 = st.columns(4)
                with fg1: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_rev/m_target['rev'])*100, title={'text':"OTB 매출달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                with fg2: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_rn/m_target['rn'])*100, title={'text':"OTB RN달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                with fg3: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_adr/m_target['adr'])*100, title={'text':"OTB ADR달성률(%)"}, gauge={'axis':{'range':[0,110]}, 'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                with fg4: st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(f_occ/m_target['occ'])*100, title={'text':"OTB OCC달성률(%)"}, gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                st.divider()

            f_o1, f_o2, f_o3, f_o4 = st.columns(4)
            f_o1.metric("향후 평균 점유율", f"{otb_future['점유율'].mean():.1f}%")
            f_o2.metric("향후 평균 ADR", f"{otb_future['합계_ADR'].mean():,.0f}원")
            f_o3.metric("최고 매출 예상일", f"{otb_future.loc[otb_future['합계_매출'].idxmax(), '일자']}")
            f_o4.metric("누적 대기 매출", f"{otb_future['합계_매출'].sum():,.0f}원")
            
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
                    with st.spinner("미래 데이터를 진단 중..."):
                        low_occ = otb_future[otb_future['점유율'] < target_occ_ref * 0.5]['일자'].tolist()[:5]
                        st.info(get_ai_insight(api_key, f"미래 평균점유율:{otb_future['점유율'].mean():.1f}%, 부진날짜:{low_occ} 전략 제안해줘."))
        else: st.warning("온더북 파일을 업로드하세요.")
else: st.info("실적 파일을 업로드하여 경영 관제를 시작하세요.")
