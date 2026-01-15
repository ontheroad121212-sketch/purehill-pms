import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v11.2", layout="wide")

# 대시보드 스타일
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 5px solid #007bff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# 2. 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.divider()
    st.info("💡 실적 파일 1개와 OTB 파일 여러 개를 동시에 선택해서 올리세요.")
    st.caption("v11.2: 수수료 제외, RM 분석 강화 및 전 탭 AI 탑재")

st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 및 미래 수익 관리")

# 3. 파일 업로드 구역 (멀티 선택 가능)
col_up1, col_up2 = st.columns(2)
with col_up1:
    prod_file = st.file_uploader("1. 예약 생성 실적 파일 (Production)", type=['csv', 'xlsx'])
with col_up2:
    otb_files = st.file_uploader("2. 영업 현황 온더북 파일 (OTB) - 다중 선택 가능", type=['csv', 'xlsx'], accept_multiple_files=True)

# 데이터 로드
prod_data = process_data(prod_file, is_otb=False) if prod_file else pd.DataFrame()
otb_data = process_data(otb_files, is_otb=True) if otb_files else pd.DataFrame()

if not prod_data.empty:
    # 실적 분석의 기준일
    latest_booking_date = prod_data['예약일'].max()

    def calc_metrics(df):
        total_sales = df['총매출액'].sum()
        room_sales = df['객실매출액'].sum()
        rn = df['room_nights'].sum()
        adr = room_sales / rn if rn > 0 else 0
        return total_sales, room_sales, rn, adr

    # --- 메인 대시보드 함수 (실적 대조 + 조식 + RM 분석 통합) ---
    def render_booking_dashboard(target_df, compare_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        # 데이터 분리
        f_curr, f_prev = target_df[target_df['market_segment'] == 'FIT'], compare_df[compare_df['market_segment'] == 'FIT']
        g_curr, g_prev = target_df[target_df['market_segment'] == 'Group'], compare_df[compare_df['market_segment'] == 'Group']
        
        t_tot, t_room, t_rn, t_adr = calc_metrics(target_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(compare_df)

        # 1구역: TOTAL 성과 대조
        st.subheader(f"✅ [{title_label} TOTAL 예약 성과]")
        st.caption(f"기준: {current_label} (비교대상: {prev_label})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 예약금액", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric("순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric("판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric("평균 ADR", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")
        st.write("---")

        # 2~3구역: FIT & Group 상세
        st.subheader(f"👤 [{title_label} 세그먼트 상세]")
        fc_tot, fc_room, fc_rn, fc_adr = calc_metrics(f_curr)
        gc_tot, gc_room, gc_rn, gc_adr = calc_metrics(g_curr)
        f1, f2, g1, g2 = st.columns(4)
        f1.metric("FIT 매출", f"{fc_room:,.0f}원", f"{fc_rn:,.0f} RN")
        f2.metric("FIT ADR", f"{fc_adr:,.0f}원")
        g1.metric("Group 매출", f"{gc_room:,.0f}원", f"{gc_rn:,.0f} RN")
        g2.metric("Group ADR", f"{gc_adr:,.0f}원")
        st.divider()

        # 4~5구역: 조식 분석 (지정 거래처 필터링)
        st.subheader("🍳 조식 포함 비중 및 지정 채널 선택률")
        bf1, bf2 = st.columns(2)
        t_all, t_bf = len(target_df), len(target_df[target_df['breakfast_status']=='조식포함'])
        f_all, f_bf = len(f_curr), len(f_curr[f_curr['breakfast_status']=='조식포함'])
        bf1.metric("전체 조식 비중", f"{(t_bf/t_all*100 if t_all>0 else 0):.1f}%", f"{t_bf}건 / {t_all}건")
        bf2.metric("FIT 조식 비중", f"{(f_bf/f_all*100 if f_all>0 else 0):.1f}%", f"{f_bf}건 / {f_all}건")
        
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

        # 🚀 [v11.2 추가] 리드타임별 ADR 분석 (RM 핵심)
        st.subheader("📅 예약 리드타임별 판매 단가(ADR) 분석")
        target_df['lead_group'] = pd.cut(target_df['lead_time'], bins=[-1, 7, 14, 30, 60, 999], labels=['1주이내', '1-2주', '2-4주', '1-2개월', '2개월이상'])
        lead_adr = target_df.groupby('lead_group').agg({'객실매출액':'sum', 'room_nights':'sum'}).reset_index()
        lead_adr['ADR'] = lead_adr['객실매출액'] / lead_adr['room_nights']
        st.plotly_chart(px.line(lead_adr, x='lead_group', y='ADR', markers=True, title="예약 시점에 따른 평균 단가 추이 (얼리버드 할인 적정성 진단)"), use_container_width=True)
        st.write("---")

        # 6~7구역: 행동 분석 및 그래프 5종 (무삭제)
        st.subheader("📈 채널별 생산성 및 고객 행동 심층 분석")
        b1, b2, b3 = st.columns(3)
        b1.metric("📅 평균 리드타임 (FIT)", f"{f_curr['lead_time'].mean():.1f}일")
        b2.metric("🌙 평균 숙박일수 (FIT LOS)", f"{f_curr['los'].mean():.1f}박")
        b3.metric("🌍 FIT 주요 국적", " / ".join(f_curr['country'].value_counts().head(3).index))
        
        pure_acc = f_curr[~f_curr['account'].str.contains('마이스|그룹', na=False, case=False)]
        acc_stats = pure_acc.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
        
        g_col1, g_col2 = st.columns(2)
        with g_col1: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with g_col2: st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', title="거래처별 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='ADR'), use_container_width=True)
        
        g_col3, g_col4 = st.columns(2)
        with g_col3: st.plotly_chart(px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h', title="거래처별 평균 LOS", text_auto='.1f', color_continuous_scale='Purples', color='los'), use_container_width=True)
        with g_col4: st.plotly_chart(px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h', title="거래처별 평균 리드타임", text_auto='.1f', color_continuous_scale='Oranges', color='lead_time'), use_container_width=True)

        global_ota = f_curr[f_curr['is_global_ota'] == True]
        if not global_ota.empty:
            st.plotly_chart(px.bar(global_ota, x="account", color="country", title="글로벌 OTA 국적 비중", barmode="stack", text_auto=True), use_container_width=True)

        # 🚀 [v11.2 유지] 각 탭별 전용 AI 분석 버튼
        st.write("---")
        if st.button(f"🤖 AI 전문가 [{title_label}] 실적 전략 리포트", key=f"ai_btn_{title_label}"):
            if api_key:
                with st.spinner(f"AI가 {title_label} 성과를 분석 중입니다..."):
                    summary = f"총매출:{t_tot:,.0f}원, RN:{t_rn:,.0f}, ADR:{t_adr:,.0f}원, 조식비중:{t_bf/t_all*100:.1f}%"
                    st.info(get_ai_insight(api_key, f"{summary} 이 데이터를 바탕으로 성과 분석과 다음 기간 수익 증대 전략을 제안해줘."))
            else: st.warning("사이드바에 Gemini API Key를 입력하세요.")

    # --- 탭 구성 및 날짜 필터링 ---
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily 실적", "📊 Weekly 실적", "📈 Monthly 실적", "🚀 Future OTB (RM전략)"])

    with tab_d:
        render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        pm_start = w_start - timedelta(days=7)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= pm_start) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
        
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        pm_end = m_start - timedelta(days=1)
        pm_start = pm_end.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= pm_start) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")

    # --- 탭 4: 미래 OTB 고도화 및 수익 관리 ---
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 미래 수익 관리 (Revenue Management) 고도화")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            f_o1, f_o2, f_o3, f_o4 = st.columns(4)
            future_occ = otb_future['점유율'].mean()
            f_o1.metric("향후 평균 점유율", f"{future_occ:.1f}%")
            f_o2.metric("향후 평균 ADR", f"{otb_future['합계_ADR'].mean():,.0f}원")
            f_o3.metric("최고 매출 예상일", f"{otb_future.loc[otb_future['합계_매출'].idxmax(), '일자'] if not otb_future.empty else 'N/A'}")
            f_o4.metric("누적 대기 매출", f"{otb_future['합계_매출'].sum():,.0f}원")
            
            # [RM 시각화 1] 점유율 vs ADR 교차 분석 (Pace)
            st.write("---")
            st.subheader("📈 미래 날짜별 예약 페이스(Pace): 점유율 vs ADR")
            fig_pace = go.Figure()
            fig_pace.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_pace.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_pace.update_layout(yaxis2=dict(overlaying='y', side='right'), title="날짜별 점유율(Bar) 및 ADR(Line) 추이", hovermode='x unified')
            st.plotly_chart(fig_pace, use_container_width=True)

            # [RM 시각화 2] 세그먼트 믹스 & 요일별 패턴
            col_rm1, col_rm2 = st.columns(2)
            with col_rm1:
                st.write("**🛌 개인(FIT) vs 단체(Group) 예약 비중**")
                fig_mix = px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실'], title="미래 예약 구성 (Room Nights)")
                st.plotly_chart(fig_mix, use_container_width=True)
            with col_rm2:
                st.write("**🗓️ 요일별 미래 점유율 패턴**")
                dow_map = {'Mon':0, 'Tue':1, 'Wed':2, 'Thu':3, 'Fri':4, 'Sat':5, 'Sun':6}
                dow_stats = otb_future.copy()
                dow_stats['dow_num'] = dow_stats['요일'].map(dow_map)
                dow_summary = dow_stats.groupby(['dow_num', '요일']).agg({'점유율':'mean'}).reset_index().sort_values('dow_num')
                st.plotly_chart(px.bar(dow_summary, x='요일', y='점유율', color='점유율', color_continuous_scale='Purples'), use_container_width=True)

            # [RM 시각화 3] 수익 최적화 매트릭스
            st.write("---")
            st.subheader("💸 수익 최적화 매트릭스 (OCC vs ADR)")
            st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자', title="점유율 대비 가격 적정성 분석"), use_container_width=True)

            if st.button("🤖 AI 전문가 미래 수익 전략 리포트"):
                if api_key:
                    with st.spinner("미래 데이터를 분석 중..."):
                        high_occ = otb_future[otb_future['점유율'] > 80]['일자'].tolist()[:5]
                        st.info(get_ai_insight(api_key, f"평균점유율:{future_occ:.1f}%, 만실임박일:{high_occ} 를 기반으로 수익 극대화 전략을 제안해줘."))
        else: st.warning("온더북 파일을 업로드하세요.")
else:
    st.info("실적 파일을 업로드하여 분석을 시작하세요.")
