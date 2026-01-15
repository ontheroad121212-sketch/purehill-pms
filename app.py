import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta
import pandas as pd

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 경영분석 v10.1", layout="wide")

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
    st.info("💡 온더북(OTB) 파일은 여러 개(최대 12개월)를 드래그해서 한 번에 올리세요.")
    st.caption("v10.1: 멀티 OTB 병합 및 실적 대조 통합 버전")

st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 및 미래 예측")

# 3. 파일 업로드 구역 (멀티 업로드 지원)
col_up1, col_up2 = st.columns(2)
with col_up1:
    prod_file = st.file_uploader("1. 예약 생성 실적 파일 (Production)", type=['csv', 'xlsx'])
with col_up2:
    otb_files = st.file_uploader("2. 영업 현황 온더북 파일 (OTB) - 여러 파일 동시 선택 가능", 
                                 type=['csv', 'xlsx'], accept_multiple_files=True)

# 데이터 로드
prod_data = process_data(prod_file, is_otb=False) if prod_file else pd.DataFrame()
otb_data = process_data(otb_files, is_otb=True) if otb_files else pd.DataFrame()

if not prod_data.empty:
    latest_booking_date = prod_data['예약일'].max()

    def calc_metrics(df):
        total_sales = df['총매출액'].sum()
        room_sales = df['객실매출액'].sum()
        rn = df['room_nights'].sum()
        adr = room_sales / rn if rn > 0 else 0
        return total_sales, room_sales, rn, adr

    def render_booking_dashboard(target_df, compare_df, title_label, current_label, prev_label):
        def get_delta_pct(curr, prev):
            if prev == 0: return "N/A"
            return f"{((curr - prev) / prev * 100):.1f}%"

        f_curr = target_df[target_df['market_segment'] == 'FIT']
        f_prev = compare_df[compare_df['market_segment'] == 'FIT']
        g_curr = target_df[target_df['market_segment'] == 'Group']
        g_prev = compare_df[compare_df['market_segment'] == 'Group']

        t_tot, t_room, t_rn, t_adr = calc_metrics(target_df)
        p_tot, p_room, p_rn, p_adr = calc_metrics(compare_df)

        # --- 1구역: TOTAL 실적 대조 ---
        st.subheader(f"✅ [{title_label} TOTAL 예약실적]")
        st.caption(f"기준: {current_label} (비교대상: {prev_label})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"총 예약금액", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)} (전기: {p_tot:,.0f})")
        c2.metric(f"순수 객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)} (전기: {p_room:,.0f})")
        c3.metric(f"판매 룸나잇", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN (전기: {p_rn:,.0f})")
        c4.metric(f"평균 판매단가", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)} (전기: {p_adr:,.0f})")
        st.write("---")

        # --- 2구역: FIT 실적 대조 ---
        st.subheader(f"👤 [{title_label} FIT 예약]")
        fc_tot, fc_room, fc_rn, fc_adr = calc_metrics(f_curr)
        fp_tot, fp_room, fp_rn, fp_adr = calc_metrics(f_prev)
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("FIT 예약금액", f"{fc_tot:,.0f}원", delta=f"{get_delta_pct(fc_tot, fp_tot)} (전기: {fp_tot:,.0f})")
        f2.metric("FIT 객실매출", f"{fc_room:,.0f}원", delta=f"{get_delta_pct(fc_room, fp_room)} (전기: {fp_room:,.0f})")
        f3.metric("FIT 룸나잇", f"{fc_rn:,.0f} RN", delta=f"{int(fc_rn - fp_rn):+d} RN (전기: {fp_rn:,.0f})")
        f4.metric("FIT ADR", f"{fc_adr:,.0f}원", delta=f"{get_delta_pct(fc_adr, fp_adr)} (전기: {fp_adr:,.0f})")
        st.write("---")

        # --- 3구역: GROUP 실적 대조 ---
        st.subheader(f"👥 [{title_label} GROUP 예약]")
        gc_tot, gc_room, gc_rn, gc_adr = calc_metrics(g_curr)
        gp_tot, gp_room, gp_rn, gp_adr = calc_metrics(g_prev)
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("그룹 예약금액", f"{gc_tot:,.0f}원", delta=f"{get_delta_pct(gc_tot, gp_tot)} (전기: {gp_tot:,.0f})")
        g2.metric("그룹 객실매출", f"{gc_room:,.0f}원", delta=f"{get_delta_pct(gc_room, gp_room)} (전기: {gp_room:,.0f})")
        g3.metric("그룹 룸나잇", f"{gc_rn:,.0f} RN", delta=f"{int(gc_rn - gp_rn):+d} RN (전기: {gp_rn:,.0f})")
        g4.metric("그룹 ADR", f"{gc_adr:,.0f}원", delta=f"{get_delta_pct(gc_adr, gp_adr)} (전기: {gp_adr:,.0f})")

        st.divider()

        # --- 4구역: 조식 핵심 지표 ---
        st.subheader(f"🍳 [{title_label}] 조식 포함 비중")
        bf1, bf2, bf3 = st.columns(3)
        t_c, bf_t_c = len(target_df), len(target_df[target_df['breakfast_status'] == '조식포함'])
        f_c, bf_f_c = len(f_curr), len(f_curr[f_curr['breakfast_status'] == '조식포함'])
        bf1.metric("전체 조식 비중", f"{(bf_t_c/t_c*100 if t_c>0 else 0):.1f}%", f"{bf_t_c}건 / {t_c}건")
        bf2.metric("FIT 조식 비중", f"{(bf_f_c/f_c*100 if f_c>0 else 0):.1f}%", f"{bf_f_c}건 / {f_c}건")
        st.divider()

        # --- 5구역: 조식 거래처 상세 (사장님 지정 리스트 필터링) ---
        st.subheader("📈 지정 거래처별 조식 포함 비중")
        target_accounts = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        def normalize_acc(x): return str(x).lower().replace(" ", "")
        target_df['acc_norm'] = target_df['account'].apply(normalize_acc)
        normalized_targets = [normalize_acc(a) for a in target_accounts]
        filtered_acc_df = target_df[target_df['acc_norm'].isin(normalized_targets)]
        if not filtered_acc_df.empty:
            acc_bf_stats = filtered_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0)
            if '조식포함' in acc_bf_stats.columns:
                row_totals = acc_bf_stats.sum(axis=1)
                acc_bf_stats['조식선택률'] = (acc_bf_stats['조식포함'] / row_totals) * 100
                acc_bf_plot = acc_bf_stats.reset_index().sort_values('조식선택률', ascending=False)
                st.plotly_chart(px.bar(acc_bf_plot, x='조식선택률', y='account', orientation='h', text=acc_bf_plot.apply(lambda r: f"{r['조식선택률']:.1f}% ({int(row_totals.loc[r.name])}건)", axis=1), color='조식선택률', color_continuous_scale='YlOrRd'), use_container_width=True)
        st.divider()

        # --- 6구역: 고객 행동 분석 (FIT 중심) ---
        st.subheader("📊 고객 행동 분석 (FIT 고객 중심)")
        b1, b2, b3 = st.columns(3)
        b1.metric("📅 평균 리드타임 (FIT)", f"{f_curr['lead_time'].mean():.1f}일")
        b2.metric("🌙 평균 숙박일수 (FIT LOS)", f"{f_curr['los'].mean():.1f}박")
        nc = f_curr['country'].value_counts(normalize=True).head(3) * 100
        b3.metric("🌍 FIT 주요 국적비", " / ".join([f"{k}: {v:.1f}%" for k, v in nc.to_dict().items()]))
        st.divider()

        # --- 7구역: 그래프 5종 (거래처 분석) ---
        st.subheader("📈 채널 및 거래처 심층 시각화")
        pure_acc = f_curr[~f_curr['account'].str.contains('마이스|그룹', na=False, case=False)]
        acc_stats = pure_acc.groupby('account').agg({'room_nights':'sum','객실매출액':'sum','los':'mean','lead_time':'mean'}).reset_index()
        acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']
        g_col1, g_col2 = st.columns(2)
        with g_col1: st.plotly_chart(px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h', title="거래처별 룸나잇", text_auto=True, color_continuous_scale='Blues', color='room_nights'), use_container_width=True)
        with g_col2: st.plotly_chart(px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h', title="거래처별 ADR", text_auto=',.0f', color_continuous_scale='Greens', color='ADR'), use_container_width=True)
        
        st.write("**글로벌 OTA 국적 비중 분석**")
        global_ota = f_curr[f_curr['is_global_ota'] == True]
        if not global_ota.empty:
            st.plotly_chart(px.bar(global_ota, x="account", color="country", barmode="stack", text_auto=True), use_container_width=True)

    # --- 탭 구성 ---
    tab_d, tab_w, tab_m, tab_f = st.tabs(["📅 Daily 실적", "📊 Weekly 실적", "📈 Monthly 실적", "🚀 Future OTB (장기)"])

    with tab_d:
        render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_s = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_s], prod_data[(prod_data['예약일'] >= w_s - timedelta(days=7)) & (prod_data['예약일'] < w_s)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_s = latest_booking_date.replace(day=1)
        pm_s = (m_s - timedelta(days=1)).replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_s], prod_data[(prod_data['예약일'] >= pm_s) & (prod_data['예약일'] < m_s)], "MONTHLY", "이번달", "지난달")
    
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 장기 미래 예약 현황 (On-the-Book Timeline)")
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            
            f_o1, f_o2, f_o3, f_o4 = st.columns(4)
            f_o1.metric("미래 평균 점유율", f"{otb_future['점유율'].mean():.1f}%")
            f_o2.metric("미래 평균 ADR", f"{otb_future['합계_ADR'].mean():,.0f}원")
            f_o3.metric("최고 점유율 일자", f"{otb_future.loc[otb_future['점유율'].idxmax(), '일자'] if not otb_future.empty else 'N/A'}")
            f_o4.metric("누적 대기 매출", f"{otb_future['합계_매출'].sum():,.0f}원")
            
            st.plotly_chart(px.line(otb_future, x='일자_dt', y='점유율', title='장기 점유율(OCC) 예측 곡선', markers=True), use_container_width=True)
            st.plotly_chart(px.area(otb_future, x='일자_dt', y='합계_매출', title='일자별 누적 예약 매출', color_discrete_sequence=['#1f77b4']), use_container_width=True)
        else:
            st.warning("온더북(OTB) 파일을 업로드하세요.")

    # AI 전략 (교차 분석)
    st.divider()
    if st.button("🤖 AI 전문가 통합 경영 리포트"):
        if api_key:
            with st.spinner("데이터 분석 중..."):
                summary = f"오늘예약매출:{prod_data[prod_data['예약일']==latest_booking_date]['객실매출액'].sum():,.0f}원"
                if not otb_data.empty: summary += f", 미래평균점유율:{otb_future['점유율'].mean():.1f}%"
                st.info(get_ai_insight(api_key, summary + " 예약 페이스와 장기 OTB를 비교하여 전략을 제안해줘."))
else:
    st.info("실적 파일을 업로드하여 분석을 시작하세요.")
