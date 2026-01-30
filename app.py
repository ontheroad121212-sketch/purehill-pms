import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime
import pandas as pd
import calendar
import firebase_admin
from firebase_admin import credentials, storage
import json
import io

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v17.3", layout="wide")

# 대시보드 스타일
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

# 🚀 [파이어베이스 초기화]
if not firebase_admin._apps:
    try:
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': st.secrets["firebase"]["storage_bucket"]
        })
    except Exception as e:
        st.error(f"🔥 파이어베이스 연결 실패: {e}")

# 2. 사이드바
with st.sidebar:
    st.header("🎯 경영 타겟 및 조회")
    
    # 데이터 기준일 조회
    ref_date = st.date_input("📅 데이터 기준일 (Snapshot Date)", datetime.now())
    
    st.divider()
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
    st.caption("v17.3: 비교 기간 수동 선택 기능 탑재")

st.title("🏛️ 엠버퓨어힐 전략분석 및 AI 경영 관제탑")

# 3. 데이터 로드 (파이어베이스)
prod_data = pd.DataFrame()
otb_data = pd.DataFrame()
stly_data = pd.DataFrame()

bucket = storage.bucket()
date_str = ref_date.strftime("%Y-%m-%d")

blob_prod = bucket.blob(f"production/prod_{date_str}.csv")
blob_otb = bucket.blob(f"otb/otb_{date_str}.csv")
blob_stly = bucket.blob(f"stly/stly_{date_str}.csv")

if blob_prod.exists() and blob_otb.exists():
    st.success(f"☁️ 클라우드에서 {date_str} 기준 데이터를 성공적으로 불러왔습니다!")
    prod_content = blob_prod.download_as_string()
    otb_content = blob_otb.download_as_string()
    prod_data = pd.read_csv(io.BytesIO(prod_content))
    otb_data = pd.read_csv(io.BytesIO(otb_content))
    
    # 날짜 컬럼 복원
    if '예약일' in prod_data.columns: prod_data['예약일'] = pd.to_datetime(prod_data['예약일'])
    if '일자' in prod_data.columns: prod_data['일자'] = pd.to_datetime(prod_data['일자'])
    if '일자_dt' in otb_data.columns: otb_data['일자_dt'] = pd.to_datetime(otb_data['일자_dt'])
    
    if blob_stly.exists():
        stly_content = blob_stly.download_as_string()
        stly_data = pd.read_csv(io.BytesIO(stly_content))
        if '일자_dt' in stly_data.columns: stly_data['일자_dt'] = pd.to_datetime(stly_data['일자_dt'])

else:
    st.warning(f"⚠️ {date_str} 기준 데이터가 서버에 없습니다. 파일을 업로드하면 자동으로 저장됩니다.")
    col_up1, col_up2 = st.columns(2)
    with col_up1: prod_file = st.file_uploader("1. 실적 (Production)", type=['csv', 'xlsx'])
    with col_up2: otb_files = st.file_uploader("2. 온더북 (OTB)", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    with st.expander("➕ 정밀 분석용 추가 데이터 업로드 (Pace/Pick-up/리드타임)", expanded=False):
        c_add1, c_add2, c_add3 = st.columns(3)
        with c_add1: stly_file_up = st.file_uploader("전년 동기 OTB (STLY)", type=['csv', 'xlsx'])
        with c_add2: snap_file = st.file_uploader("1주일 전 OTB 스냅샷", type=['csv', 'xlsx'])
        with c_add3: raw_file = st.file_uploader("상세 예약 리스트 (Raw Data)", type=['csv', 'xlsx'])

    if prod_file and otb_files:
        with st.spinner("데이터 처리 및 클라우드 저장 중..."):
            prod_data = process_data(prod_file, is_otb=False)
            otb_data = process_data(otb_files, is_otb=True)
            if stly_file_up: stly_data = process_data(stly_file_up, is_otb=True)
            
            if not prod_data.empty:
                extracted_date = prod_data['예약일'].max().strftime("%Y-%m-%d")
                if extracted_date != date_str:
                    st.toast(f"💡 파일 내부 기준일({extracted_date})이 선택일과 달라 해당 날짜로 저장합니다.")
                
                bucket.blob(f"production/prod_{extracted_date}.csv").upload_from_string(prod_data.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                bucket.blob(f"otb/otb_{extracted_date}.csv").upload_from_string(otb_data.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                if not stly_data.empty:
                    bucket.blob(f"stly/stly_{extracted_date}.csv").upload_from_string(stly_data.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                
                st.success(f"✅ 데이터가 {extracted_date} 기준으로 안전하게 저장되었습니다! (새로고침 시 자동 로드)")

# OTB 데이터 전처리
if not otb_data.empty and '일자_dt' in otb_data.columns:
    otb_data = otb_data[otb_data['일자_dt'].notna()].copy()

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

        # 수요 집중도 매트릭스
        if not curr_df.empty:
            st.write("---")
            st.subheader(f"🎯 [{title_label}] 생성 예약분 기반 체크인 수요 매트릭스")
            all_date_cols = curr_df.select_dtypes(include=['datetime64']).columns.tolist()
            stay_date_candidates = [c for c in all_date_cols if '예약' not in c]
            
            if not stay_date_candidates:
                stay_date_candidates = [c for c in curr_df.columns if any(x in c for x in ['일자', '체크인', 'Stay', 'Date'])]
            
            if stay_date_candidates:
                target_date_col = stay_date_candidates[0]
                demand_matrix = curr_df.groupby(target_date_col).agg({'room_nights': 'sum', '객실매출액': 'sum'}).reset_index()
                demand_matrix['Net_ADR'] = demand_matrix['객실매출액'] / demand_matrix['room_nights']
                
                fig_matrix = px.scatter(
                    demand_matrix, x=target_date_col, y='Net_ADR', size='room_nights', color='room_nights',
                    color_continuous_scale='Viridis', title=f"현재 선택된 예약들({current_label})의 실제 투숙일(체크인) 분포",
                    labels={target_date_col: '체크인 예정일 (Stay Date)', 'Net_ADR': 'ADR(Net)', 'room_nights': '예약량(RN)'}
                )
                fig_matrix.update_layout(hovermode='closest')
                st.plotly_chart(fig_matrix, use_container_width=True)
            else:
                st.warning("⚠️ 투숙일(체크인 날짜) 데이터를 찾을 수 없어 매트릭스를 표시할 수 없습니다.")

        # AI 리포트 호출 (Custom 탭이 아닐 때만 공통 버튼 사용)
        if title_label != "CUSTOM":
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
                        1. 전기 대비 매출 변동 원인을 글로벌 채널(아고다/익스피디아)의 국적 믹스 및 가격 경쟁력 측면에서 분석하라.
                        2. 현재 시점 버짓 달성을 위해 남은 기간 매일 최소 몇 실을 얼마에 팔아야 하는지(Shortfall 대응) 구체적인 수치 가이드를 제시하라.
                        3. 조식 비중을 높여 부대수익을 극대화할 수 있는 구체적인 채널별 가격 전략(Add-on 패키징)을 제안하라.
                        4. 수요 매트릭스상 체크인 수요가 몰리는 날짜의 가격 인상 폭과, 부진한 날짜를 채우기 위한 'Flash Sale' 권장 판매가를 숫자로 찍어라.
                        
                        형식: 서술형 제외, 임팩트 있는 불렛포인트로 보고할 것.
                        """
                        st.info(get_ai_insight(api_key, prompt))

    # 4. 탭 구성 (Tab 추가됨)
    tab_d, tab_w, tab_m, tab_c, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🔍 기간별 맞춤 조회", "🚀 Future OTB (전략관제)"])
    
    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= (m_start - timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")
    
    # 🆕 [추가된 탭] 맞춤 조회 로직 (비교 기간 수동 선택 기능 추가)
    with tab_c:
        st.subheader("🔍 기간별 맞춤 분석 & 비교")
        
        # 1. 컬럼 분할: 왼쪽(분석기간) / 오른쪽(비교기간)
        cc1, cc2 = st.columns(2)
        
        with cc1:
            custom_date_range = st.date_input(
                "1️⃣ 분석할 기간 (Current Period)",
                (ref_date - timedelta(days=7), ref_date),
                max_value=ref_date,
                key="curr_range"
            )
            
        with cc2:
            # 비교 기간 기본값 (직전 동기간) 미리 계산
            if len(custom_date_range) == 2:
                c_s, c_e = custom_date_range
                duration = (c_e - c_s).days + 1
                def_e = c_s - timedelta(days=1)
                def_s = def_e - timedelta(days=duration - 1)
                def_range = (def_s, def_e)
            else:
                def_range = (ref_date - timedelta(days=14), ref_date - timedelta(days=8))

            compare_date_range = st.date_input(
                "2️⃣ 비교할 과거 기간 (Comparison Period)",
                def_range,
                max_value=ref_date,
                key="comp_range"
            )

        # 2. 데이터 처리 및 렌더링
        if len(custom_date_range) == 2 and len(compare_date_range) == 2:
            s_date, e_date = custom_date_range
            cs_date, ce_date = compare_date_range
            
            s_date, e_date = pd.to_datetime(s_date), pd.to_datetime(e_date)
            cs_date, ce_date = pd.to_datetime(cs_date), pd.to_datetime(ce_date)
            
            # 데이터 필터링
            mask_curr = (prod_data['예약일'] >= s_date) & (prod_data['예약일'] <= e_date)
            mask_prev = (prod_data['예약일'] >= cs_date) & (prod_data['예약일'] <= ce_date)
            
            curr_df = prod_data[mask_curr]
            prev_df = prod_data[mask_prev]
            
            st.info(f"📊 **분석 구간:** {s_date.strftime('%Y-%m-%d')} ~ {e_date.strftime('%Y-%m-%d')}  VS  **비교 구간:** {cs_date.strftime('%Y-%m-%d')} ~ {ce_date.strftime('%Y-%m-%d')}")
            
            if not curr_df.empty:
                # Custom 탭 전용 렌더링 호출
                render_booking_dashboard(curr_df, prev_df, "CUSTOM", "선택 기간", "비교 기간")
                
                # Custom 탭 전용 AI 리포트 버튼 (여기에만 별도 배치)
                if st.button("🤖 AI 전문가 [맞춤 기간] 전략 리포트", key="ai_custom"):
                    if api_key:
                        with st.spinner("선택하신 기간의 데이터를 정밀 분석 중입니다..."):
                            t_tot, t_room, t_rn, t_adr = calc_metrics(curr_df)
                            p_tot, p_room, p_rn, p_adr = calc_metrics(prev_df)
                            
                            def get_delta_pct(curr, prev):
                                if prev == 0: return "N/A"
                                return f"{((curr - prev) / prev * 100):.1f}%"

                            prompt = f"""
                            당신은 호텔 RM 전문가입니다. 사용자가 지정한 두 기간의 실적을 비교 분석하세요.
                            
                            [기간 1: {s_date.strftime('%Y-%m-%d')} ~ {e_date.strftime('%Y-%m-%d')}]
                            - 매출: {t_tot:,.0f}, RN: {t_rn}, ADR: {t_adr:,.0f}
                            
                            [기간 2 (비교군): {cs_date.strftime('%Y-%m-%d')} ~ {ce_date.strftime('%Y-%m-%d')}]
                            - 매출 변화: {get_delta_pct(t_tot, p_tot)}
                            - RN 변화: {int(t_rn - p_rn):+d}
                            
                            주요 변화의 원인과 향후 전략을 불렛포인트로 요약하세요.
                            """
                            st.info(get_ai_insight(api_key, prompt))
            else:
                st.warning("선택하신 '분석 기간'에 해당하는 데이터가 없습니다.")
        else:
            st.info("두 기간(분석 기간, 비교 기간)의 시작일과 종료일을 모두 선택해주세요.")

    # 5. 미래 OTB 및 시뮬레이션
    with tab_f:
        if not otb_data.empty:
            st.subheader("🚀 향후 4개월 월별 버짓 달성 현황 및 긴급 시뮬레이션")
            
            this_month_prod = prod_data[prod_data['예약일'].dt.month == analysis_month]
            p_rev_sum = this_month_prod['객실매출액'].sum()
            p_rn_sum = this_month_prod['room_nights'].sum()
            
            this_month_otb_all = otb_data[otb_data['일자_dt'].dt.month == analysis_month]
            c_rev = this_month_otb_all['합계_매출'].sum()
            c_rn = this_month_otb_all['합계_객실'].sum()
            
            if c_rev == 0 and not this_month_otb_all.empty:
                 c_rev = p_rev_sum
                 c_rn = p_rn_sum

            m_bud = targets.get(analysis_month)
            rev_ach_rate = (c_rev / m_bud['rev_won'] * 100)
            rn_ach_rate = (c_rn / m_bud['rn'] * 100)
            
            otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
            
            if m_bud:
                st.error(f"🚨 {analysis_month}월 버짓 달성 긴급 시뮬레이션")
                last_day_of_month = calendar.monthrange(latest_booking_date.year, analysis_month)[1]
                days_left = last_day_of_month - latest_booking_date.day
                s_rev = max(0, m_bud['rev_won'] - c_rev)
                s_rn = max(0, m_bud['rn'] - c_rn)
                
                if days_left > 0:
                    req_rn_per_day = s_rn / days_left
                    req_adr = s_rev / s_rn if s_rn > 0 else 0
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("남은 기간", f"{days_left}일")
                    sc2.metric("일일 필요 판매량", f"{req_rn_per_day:.1f} RN/일")
                    sc3.metric("필요 평균 단가", f"{req_adr:,.0f}원")
                    if rev_ach_rate >= 90: st.success(f"💡 현재 {rev_ach_rate:.1f}% 달성! 남은 {days_left}일간 {req_rn_per_day:.1f}실을 {req_adr:,.0f}원에 팔면 100% 돌파.")
                    else: st.warning(f"💡 목표 달성을 위해 남은 {days_left}일간 매일 {req_rn_per_day:.1f}실을 {req_adr:,.0f}원에 팔아야 합니다.")

            for i in range(4):
                t_m = (analysis_month - 1 + i) % 12 + 1
                m_data = otb_data[otb_data['일자_dt'].dt.month == t_m]
                if not m_data.empty:
                    m_b = targets.get(t_m)
                    cur_rev = c_rev if i == 0 else m_data['합계_매출'].sum()
                    cur_rn = c_rn if i == 0 else m_data['합계_객실'].sum()
                    
                    with st.expander(f"📌 {t_m}월 OTB 상세 달성 현황", expanded=(i==0)):
                        fg = st.columns(4)
                        fg[0].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(cur_rev/m_b['rev_won'])*100, title={'text':"매출달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        fg[1].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(cur_rn/m_b['rn'])*100, title={'text':"RN달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        cur_adr = cur_rev/cur_rn if cur_rn > 0 else 0
                        fg[2].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(cur_adr/m_b['adr'])*100, title={'text':"ADR달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)
                        days_in_m = calendar.monthrange(latest_booking_date.year, t_m)[1]
                        cur_occ = (cur_rn / (130 * days_in_m)) * 100
                        fg[3].plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=(cur_occ/m_b['occ'])*100, title={'text':"OCC달성(%)"}, gauge={'bar':{'color':"#FF4B4B"}})).update_layout(height=180, margin=dict(t=30,b=0,l=10,r=10)), use_container_width=True)

            st.divider()
            st.subheader("📈 미래 예약 Pace 분석")
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='점유율(%)', marker_color='#a2d2ff'))
            fig_p.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR(원)', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
            fig_p.update_layout(yaxis2=dict(overlaying='y', side='right'), title="날짜별 점유율 vs ADR 추이")
            st.plotly_chart(fig_p, use_container_width=True)
            
            cs1, cs2 = st.columns(2)
            with cs1: st.plotly_chart(px.area(otb_future, x='일자_dt', y=['개인_객실', '단체_객실'], title="세그먼트 믹스"), use_container_width=True)
            with cs2: st.plotly_chart(px.scatter(otb_future, x='점유율', y='합계_ADR', size='합계_매출', color='요일', hover_name='일자', title="수익 최적화 매트릭스"), use_container_width=True)

            # 🤖 [수정된 AI 리포트 기능]
            if st.button("🤖 AI 미래 전략 리포트"):
                if api_key:
                    with st.spinner("AI 전문가가 수익 전략을 분석 중입니다..."):
                        stly_info = "제공됨" if not stly_data.empty else "부재(비교불가)"
                        
                        prompt = f"""
                        "너는 20년 경력의 RM 전문가다. 하지만 반드시 내가 제공한 데이터(Jan 2026) 내에서만 수치를 인용하라. 전년 데이터나 과거 리드타임 데이터가 없다면 임의로 숫자를 지어내지 말고, **'데이터 부재로 비교 불가'**라고 명시한 뒤 현재의 OTB Pace와 버짓 달성률만 가지고 전략을 짜라. 소설 쓰지 말고 팩트 위주로 보고하라."
                        
                        [데이터 상태: {stly_info}]
                        [당월(1월) 매출 달성률: {rev_ach_rate:.1f}%]
                        [남은 일수: {days_left}일 / 필요 일일판매량: {req_rn_per_day:.1f}실 / 필요 단가: {req_adr:,.0f}원]

                        1. [종합 경영 판단 및 버짓 예측]
                        - 버짓 달성 예측: 현재 예약 Pace를 고려할 때 당월 매출 목표 달성 가능성을 %로 예측하라. 숏폴(Shortfall) 발생 시 정확한 부족 금액을 산출하라.
                        - 세그먼트 믹스: FIT(개인)와 Group(단체) 비중을 분석하여 ADR을 훼손하는 세그먼트를 찾아내고, 수익성 개선을 위한 믹스 조정안을 제안하라.
                        - 페이스 특이사항: 전주 또는 전월 대비 예약 속도가 급변한 날짜를 특정하고 그 원인을 진단하라.

                        2. [Yield Management: 수익 최적화 전략]
                        - 고수요 구간(High-Demand): OCC(점유율) 80% 초과 날짜를 식별하고, 해당 날짜의 ADR을 극대화하기 위한 'Close-to-Arrival' 또는 '강한 가격 인상' 필요성을 판정하라.
                        - 저수요 구간(Low-Demand): 점유율 부진 날짜를 찍어내어 즉각적인 Flash Sale, 패키지 결합, 또는 타겟 프로모션 단가를 숫자로 제시하라.
                        - RevPAR 극대화: 현재 데이터 흐름상 OCC를 채우는 전략과 ADR을 높이는 전략 중 무엇이 전체 수익에 유리한지 결론을 내려라.

                        3. [향후 3개월 Pacing 관제: 당월/익월/익익월]
                        - 당월(M): 남은 기간 버짓 달성을 위해 필요한 일일 목표 RN과 최소 판매 단가(Required ADR)를 제시하라.
                        - 익월(M+1): 현재 유입 속도로 볼 때 익월 버짓 달성이 낙관적인지 비관적인지 판단하고, 선확보(Base-load)가 필요한 세그먼트를 지시하라.
                        - 익익월(M+2): 얼리버드 수요를 분석하여 현재의 Lead Time이 적절한지 평가하고, 초기 가격 책정(Starting Rate) 변경 여부를 제언하라.

                        4. [회의용 Action Plan]
                        - 예약실: 특정일 마감 전략 및 오버부킹 허용 범위 지시.
                        - 영업팀: 숏폴 날짜를 메우기 위한 기업/단체 타겟 마케팅 일자 지정.
                        - 마케팅팀: OTA 채널별 가격 노출 순위 조정 및 특정 날짜 프로모션 강화 지시.

                        보고 형식: 서술형은 지양하고, 임팩트 있는 불렛포인트 위주로 요약할 것.
                        """
                        st.info(get_ai_insight(api_key, prompt))
else:
    st.info("실적 파일을 업로드하여 경영 관제를 시작하세요.")
