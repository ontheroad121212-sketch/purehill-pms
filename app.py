import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from processor import process_data
from ai_engine import get_ai_insight
from datetime import timedelta, datetime, date
import pandas as pd
import calendar
import firebase_admin
from firebase_admin import credentials, storage
import json
import io

# 1. 화면 설정
st.set_page_config(page_title="엠버퓨어힐 통합 관제 v17.7", layout="wide")

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
    
    # 🔥 [수정] datetime.now() -> datetime.now().date() 로 시간 제거
    ref_date = st.date_input("📅 데이터 기준일 (Snapshot Date)", datetime.now().date())
    
    st.divider()
    st.subheader("🔍 기간별 맞춤 조회")
    # 분석 기간 선택 (여기도 날짜 객체 보장)
    custom_date_range = st.date_input(
        "1️⃣ 분석할 기간 (Current Period)",
        (ref_date - timedelta(days=7), ref_date),
        max_value=ref_date
    )
    
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
    st.caption("v17.7: 날짜 충돌 에러(RangeError) 해결")

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

# 1) 실적 데이터 로드
if blob_prod.exists():
    prod_content = blob_prod.download_as_string()
    prod_data = pd.read_csv(io.BytesIO(prod_content))
    if '예약일' in prod_data.columns: prod_data['예약일'] = pd.to_datetime(prod_data['예약일'])
    if '일자' in prod_data.columns: prod_data['일자'] = pd.to_datetime(prod_data['일자'])

# 2) OTB 데이터 로드
if blob_otb.exists():
    otb_content = blob_otb.download_as_string()
    otb_data = pd.read_csv(io.BytesIO(otb_content))
    if '일자_dt' in otb_data.columns: otb_data['일자_dt'] = pd.to_datetime(otb_data['일자_dt'])

# 3) STLY 데이터 로드
if blob_stly.exists():
    stly_content = blob_stly.download_as_string()
    stly_data = pd.read_csv(io.BytesIO(stly_content))
    if '일자_dt' in stly_data.columns: stly_data['일자_dt'] = pd.to_datetime(stly_data['일자_dt'])

# 데이터 상태 체크
is_prod_ready = not prod_data.empty
is_otb_ready = not otb_data.empty

if is_prod_ready and is_otb_ready:
    st.success(f"☁️ {date_str} 기준 통합 데이터 로드 완료! 대시보드를 출력합니다.")
else:
    st.info(f"🧐 {date_str} 기준 데이터를 찾고 있습니다... (실적: {'✅' if is_prod_ready else '❌'} / OTB: {'✅' if is_otb_ready else '❌'})")
    
    col_u1, col_u2 = st.columns(2)
    
    # [왼쪽] 실적 저장
    with col_u1:
        st.subheader("1️⃣ 실적 (Production)")
        if is_prod_ready: st.success("데이터 있음")
        else: st.warning("데이터 없음")
            
        prod_file = st.file_uploader("실적 파일", type=['csv', 'xlsx'], key="u_prod")
        if prod_file and st.button("💾 실적 저장", key="btn_save_prod"):
            with st.spinner("처리 중..."):
                prod_df_temp = process_data(prod_file, is_otb=False)
                if not prod_df_temp.empty:
                    ex_date = prod_df_temp['예약일'].max().strftime("%Y-%m-%d")
                    # 저장
                    bucket.blob(f"production/prod_{ex_date}.csv").upload_from_string(prod_df_temp.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                    
                    if ex_date == date_str:
                        st.success(f"✅ {ex_date} 실적 저장 완료! 새로고침합니다.")
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장 완료! 하지만 파일 날짜({ex_date})가 선택 날짜({date_str})와 다릅니다. 사이드바 날짜를 변경해주세요.")

    # [오른쪽] OTB 저장
    with col_u2:
        st.subheader("2️⃣ 온더북 (OTB)")
        if is_otb_ready: st.success("데이터 있음")
        else: st.warning("데이터 없음")
            
        otb_files = st.file_uploader("OTB 파일 (다중)", type=['csv', 'xlsx'], accept_multiple_files=True, key="u_otb")
        with st.expander("➕ 추가 데이터 (STLY 등)"):
            c1, c2, c3 = st.columns(3)
            with c1: stly_file_up = st.file_uploader("STLY", key="u_stly")
            with c2: snap_file = st.file_uploader("Snap", key="u_snap")
            with c3: raw_file = st.file_uploader("Raw", key="u_raw")
            
        if otb_files and st.button("💾 OTB 저장", key="btn_save_otb"):
            with st.spinner("처리 중..."):
                otb_df_temp = process_data(otb_files, is_otb=True)
                stly_df_temp = pd.DataFrame()
                if stly_file_up: stly_df_temp = process_data(stly_file_up, is_otb=True)

                if not otb_df_temp.empty:
                    # OTB는 사이드바 선택 날짜(ref_date)로 강제 저장
                    bucket.blob(f"otb/otb_{date_str}.csv").upload_from_string(otb_df_temp.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                    if not stly_df_temp.empty:
                        bucket.blob(f"stly/stly_{date_str}.csv").upload_from_string(stly_df_temp.to_csv(index=False).encode('utf-8-sig'), content_type='text/csv')
                        
                    st.success(f"✅ {date_str} 기준 OTB 저장 완료! 새로고침합니다.")
                    st.rerun()

# 4. 공통 변수 및 전처리
latest_booking_date = pd.to_datetime(ref_date)
analysis_month = latest_booking_date.month

if not otb_data.empty and '일자_dt' in otb_data.columns:
    otb_data = otb_data[otb_data['일자_dt'].notna()].copy()

def calc_metrics(df):
    if df.empty: return 0, 0, 0, 0
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
    c1.metric("총 매출액", f"{t_tot:,.0f}원", delta=f"{get_delta_pct(t_tot, p_tot)}")
    c2.metric("객실매출", f"{t_room:,.0f}원", delta=f"{get_delta_pct(t_room, p_room)}")
    c3.metric("판매 RN", f"{t_rn:,.0f} RN", delta=f"{int(t_rn - p_rn):+d} RN")
    c4.metric("ADR (Net)", f"{t_adr:,.0f}원", delta=f"{get_delta_pct(t_adr, p_adr)}")

    # 조식 및 세그먼트 분석
    st.write("---")
    st.subheader("🍳 조식 및 세그먼트 믹스")
    bc1, bc2, bc3 = st.columns(3)
    def get_bf_ratio(df):
        if df.empty: return 0
        return (len(df[df['breakfast_status'] == '조식포함']) / len(df) * 100) if len(df) > 0 else 0
    
    bc1.metric("전체 조식 비중", f"{get_bf_ratio(curr_df):.1f}%")
    
    f_curr = curr_df[curr_df['market_segment'] == 'FIT']
    ft_tot, ft_room, ft_rn, ft_adr = calc_metrics(f_curr)
    
    g_curr = curr_df[curr_df['market_segment'] == 'Group']
    gt_tot, gt_room, gt_rn, gt_adr = calc_metrics(g_curr)
    
    bc2.metric("FIT 매출비중", f"{(ft_tot/t_tot*100 if t_tot>0 else 0):.1f}%")
    bc3.metric("Group 매출비중", f"{(gt_tot/t_tot*100 if t_tot>0 else 0):.1f}%")

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

    st.write("---")
    # FIT 심층 분석
    st.subheader("👤 FIT 세그먼트 성과 대조")
    f_prev = prev_df[prev_df['market_segment'] == 'FIT']
    fp_tot, fp_room, fp_rn, fp_adr = calc_metrics(f_prev)
    
    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("FIT 총매출", f"{ft_tot:,.0f}원", delta=f"{get_delta_pct(ft_tot, fp_tot)}")
    fc2.metric("FIT 객실매출", f"{ft_room:,.0f}원", delta=f"{get_delta_pct(ft_room, fp_room)}")
    fc3.metric("FIT RN", f"{ft_rn:,.0f} RN", delta=f"{int(ft_rn - fp_rn):+d} RN")
    fc4.metric("FIT ADR", f"{ft_adr:,.0f}원", delta=f"{get_delta_pct(ft_adr, fp_adr)}")

    if not f_curr.empty:
        st.write("**[FIT 전체 행동 패턴 분석]**")
        fa1, fa2, fa3 = st.columns(3)
        fa1.metric("FIT 평균 리드타임", f"{f_curr['lead_time'].mean():.1f}일")
        fa2.metric("FIT 평균 LOS", f"{f_curr['los'].mean():.1f}박")
        fa3.metric("FIT 최다 투숙 국적", f_curr['country'].value_counts().index[0])
        st.plotly_chart(px.pie(f_curr, names='country', title="FIT 전체 국적 비중", hole=0.4), use_container_width=True)

    st.write("---")
    # Group 심층 분석
    st.subheader("👥 Group 세그먼트 성과 대조")
    g_prev = prev_df[prev_df['market_segment'] == 'Group']
    gp_tot, gp_room, gp_rn, gp_adr = calc_metrics(g_prev)
    
    gc1, gc2, gc3, gc4 = st.columns(4)
    gc1.metric("그룹 총매출", f"{gt_tot:,.0f}원", delta=f"{get_delta_pct(gt_tot, gp_tot)}")
    gc2.metric("그룹 객실매출", f"{gt_room:,.0f}원", delta=f"{get_delta_pct(gt_room, gp_room)}")
    gc3.metric("그룹 RN", f"{gt_rn:,.0f} RN", delta=f"{int(gt_rn - gp_rn):+d} RN")
    gc4.metric("그룹 ADR", f"{gt_adr:,.0f}원", delta=f"{get_delta_pct(gt_adr, gp_adr)}")

    st.write("---")
    # 차트 여백 및 짤림 방지 적용
    if not curr_df.empty:
        st.subheader("📊 주요 거래처 분석")
        acc_s = curr_df.groupby('account').agg({'room_nights':'sum','객실매출액':'sum'}).reset_index().sort_values('room_nights', ascending=False).head(10)
        fig_acc = px.bar(acc_s, x='room_nights', y='account', orientation='h', text_auto=True, title="Top 10 생산성")
        fig_acc.update_layout(margin=dict(l=10, r=20, t=30, b=10), yaxis={'categoryorder':'total ascending'})
        fig_acc.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(fig_acc, use_container_width=True)
        
        # 글로벌 OTA
        st.write("---")
        gl_ch = ['아고다', 'AGODA', '익스피디아', '부킹', '트립']
        gl_df = curr_df[curr_df['account'].str.upper().str.contains('|'.join(gl_ch), na=False)]
        if not gl_df.empty:
            fig_gl = px.bar(gl_df, x="account", color="country", title="글로벌 OTA 채널별 국적 비중", barmode="stack", text_auto=True)
            fig_gl.update_layout(margin=dict(l=10, r=20, t=30, b=10))
            fig_gl.update_traces(cliponaxis=False)
            st.plotly_chart(fig_gl, use_container_width=True)

        # 조식 선택률
        targets_acc = ['아고다', '부킹닷컴', '익스피디아 e.c', '익스피디아 h.c', '트립닷컴', '네이버', '홈페이지', '야놀자', '호텔타임', '트립비토즈', '마이리얼트립', '올마이투어', '타이드스퀘어', 'personal']
        f_acc_df = curr_df[curr_df['account'].str.lower().str.replace(" ", "").isin([a.lower().replace(" ","") for a in targets_acc])]
        if not f_acc_df.empty:
            st.write("---")
            st.subheader("🍳 지정 거래처 조식 선택률 분석")
            bf_s = f_acc_df.groupby(['account', 'breakfast_status']).size().unstack(fill_value=0).reset_index()
            if '조식포함' in bf_s.columns:
                bf_s['ratio'] = (bf_s['조식포함'] / bf_s.iloc[:, 1:].sum(axis=1)) * 100
                fig_bf = px.bar(bf_s.sort_values('ratio', ascending=False), x='ratio', y='account', orientation='h', title="거래처별 조식 선택률 (%)", color_continuous_scale='YlOrRd', color='ratio')
                fig_bf.update_layout(margin=dict(l=10, r=20, t=30, b=10))
                fig_bf.update_traces(cliponaxis=False)
                st.plotly_chart(fig_bf, use_container_width=True)

        # 날짜별 수요 매트릭스
        st.write("---")
        st.subheader("🎯 체크인 수요 매트릭스")
        all_date_cols = curr_df.select_dtypes(include=['datetime64']).columns.tolist()
        stay_date_candidates = [c for c in all_date_cols if '예약' not in c]
        
        if stay_date_candidates:
            target_date_col = stay_date_candidates[0]
            demand_matrix = curr_df.groupby(target_date_col).agg({'room_nights': 'sum', '객실매출액': 'sum'}).reset_index()
            demand_matrix['Net_ADR'] = demand_matrix['객실매출액'] / demand_matrix['room_nights']
            
            fig_mat = px.scatter(
                demand_matrix, x=target_date_col, y='Net_ADR', size='room_nights', color='room_nights',
                color_continuous_scale='Viridis', title=f"{current_label} 투숙일별 수요 분포"
            )
            fig_mat.update_layout(hovermode='closest', margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_mat, use_container_width=True)

        # 공통 AI 리포트 (Custom 탭 아닐 때)
        if title_label != "CUSTOM":
            if st.button(f"🤖 AI 전문가 [{title_label}] 전략 리포트", key=f"ai_{title_label}"):
                if api_key:
                    with st.spinner("전문가가 성과를 정밀 진단 중..."):
                        m_bud = targets.get(analysis_month)
                        top_5_acc_list = "없음"
                        if not acc_s.empty:
                            top_5_acc_list = acc_s.head(5)[['account', 'room_nights']].to_dict('records')
                        
                        prompt = f"""
                        너는 글로벌 럭셔리 호텔 20년 경력의 Revenue Management 전문가다. 사장님(CEO)께 보고하듯 '현상-원인-액션아이템' 구조로 매우 뾰족하게 제언하라.
                        
                        [현재 데이터 요약]
                        - 분석 월: {analysis_month}월 / 분석 주기: {title_label} ({current_label})
                        - 실적: 객실매출 {t_room:,.0f}원, RN {t_rn}, ADR {t_adr:,.0f}원
                        - 전기 대비 추이: 객실매출 {get_delta_pct(t_room, p_room)}, ADR {get_delta_pct(t_adr, p_adr)}
                        - 주요 거래처 성과: {top_5_acc_list}
                        
                        [전략 지시사항]
                        1. 전기 대비 매출 변동 원인을 글로벌 채널(아고다/익스피디아)의 국적 믹스 및 가격 경쟁력 측면에서 분석하라.
                        2. 현재 시점 버짓 달성을 위해 남은 기간 매일 최소 몇 실을 얼마에 팔아야 하는지(Shortfall 대응) 구체적인 수치 가이드를 제시하라.
                        3. 조식 비중을 높여 부대수익을 극대화할 수 있는 구체적인 채널별 가격 전략(Add-on 패키징)을 제안하라.
                        4. 수요 매트릭스상 체크인 수요가 몰리는 날짜의 가격 인상 폭과, 부진한 날짜를 채우기 위한 'Flash Sale' 권장 판매가를 숫자로 찍어라.
                        
                        형식: 서술형 제외, 임팩트 있는 불렛포인트로 보고할 것.
                        """
                        st.info(get_ai_insight(api_key, prompt))

# 탭 구성
tab_d, tab_w, tab_m, tab_c, tab_f = st.tabs(["📅 Daily", "📊 Weekly", "📈 Monthly", "🔍 기간별 맞춤 조회", "🚀 Future OTB"])

if not prod_data.empty:
    with tab_d: render_booking_dashboard(prod_data[prod_data['예약일'] == latest_booking_date], prod_data[prod_data['예약일'] == latest_booking_date - timedelta(days=1)], "DAILY", "오늘", "어제")
    with tab_w:
        w_start = latest_booking_date - timedelta(days=latest_booking_date.weekday())
        render_booking_dashboard(prod_data[prod_data['예약일'] >= w_start], prod_data[(prod_data['예약일'] >= w_start - timedelta(days=7)) & (prod_data['예약일'] < w_start)], "WEEKLY", "이번주", "지난주")
    with tab_m:
        m_start = latest_booking_date.replace(day=1)
        render_booking_dashboard(prod_data[prod_data['예약일'] >= m_start], prod_data[(prod_data['예약일'] >= (m_start - timedelta(days=1)).replace(day=1)) & (prod_data['예약일'] < m_start)], "MONTHLY", "이번달", "지난달")
    
    # 기간별 맞춤 조회 (비교 기간 선택 기능 포함)
    with tab_c:
        st.subheader("🔍 기간별 맞춤 분석")
        cc1, cc2 = st.columns(2)
        with cc1:
            # 🔥 날짜 객체 보장 (v17.7 fix)
            custom_date_range = st.date_input("1️⃣ 분석 기간", (ref_date - timedelta(days=7), ref_date), max_value=ref_date, key="c_curr")
        with cc2:
            if len(custom_date_range)==2:
                s, e = custom_date_range
                dur = (e-s).days + 1
                def_range = (s - timedelta(days=1), s - timedelta(days=dur))
            else: def_range = (ref_date, ref_date)
            # 🔥 날짜 객체 보장
            compare_date_range = st.date_input("2️⃣ 비교 기간", def_range, max_value=ref_date, key="c_comp")
            
        if len(custom_date_range)==2 and len(compare_date_range)==2:
            s, e = map(pd.to_datetime, custom_date_range)
            cs, ce = map(pd.to_datetime, compare_date_range)
            curr = prod_data[(prod_data['예약일']>=s)&(prod_data['예약일']<=e)]
            prev = prod_data[(prod_data['예약일']>=cs)&(prod_data['예약일']<=ce)]
            if not curr.empty: 
                render_booking_dashboard(curr, prev, "CUSTOM", "선택", "비교")
                
                # Custom 탭 전용 AI 리포트
                if st.button("🤖 AI 전문가 [맞춤 기간] 리포트", key="ai_custom"):
                    if api_key:
                        with st.spinner("분석 중..."):
                            t_tot, t_room, t_rn, t_adr = calc_metrics(curr)
                            p_tot, p_room, p_rn, p_adr = calc_metrics(prev)
                            prompt = f"""
                            호텔 RM 전문가로서 분석하라.
                            [기간 1] 매출: {t_tot:,.0f}, RN: {t_rn}, ADR: {t_adr:,.0f}
                            [기간 2] 대비 매출 변화율: {((t_tot-p_tot)/p_tot*100) if p_tot else 0:.1f}%
                            핵심 원인 및 제언을 불렛포인트로 요약하라.
                            """
                            st.info(get_ai_insight(api_key, prompt))
            else: st.warning("데이터 없음")

# 5. 미래 OTB 및 시뮬레이션
with tab_f:
    if not otb_data.empty:
        st.subheader("🚀 향후 4개월 전략 관제")
        
        # OTB 분석용 데이터
        otb_future = otb_data[otb_data['일자_dt'] >= latest_booking_date]
        
        st.write("### 📅 월별 버짓 달성 현황")
        
        # 당월 버짓 달성 시뮬레이션 (Over-Budget 로직 적용)
        if analysis_month in targets:
            m_bud = targets[analysis_month]
            this_month_data = otb_data[otb_data['일자_dt'].dt.month == analysis_month]
            
            c_rev = this_month_data['합계_매출'].sum()
            c_rn = this_month_data['합계_객실'].sum()
            
            rev_rate = (c_rev / m_bud['rev_won']) * 100
            rn_rate = (c_rn / m_bud['rn']) * 100
            
            last_day = calendar.monthrange(latest_booking_date.year, analysis_month)[1]
            days_left = last_day - latest_booking_date.day
            
            st.info(f"📊 **{analysis_month}월 현황:** 매출 {c_rev:,.0f}원 ({rev_rate:.1f}%) / RN {c_rn:,.0f} ({rn_rate:.1f}%)")
            
            if days_left > 0:
                diff_rev = c_rev - m_bud['rev_won']
                diff_rn = c_rn - m_bud['rn']
                
                # 🔥 [Over-Budget] 초과 달성 시
                if diff_rev > 0:
                    st.success(f"🎉 **축하합니다! {analysis_month}월 목표를 이미 초과 달성했습니다!** (달성률 {rev_rate:.1f}%)")
                    b1, b2, b3 = st.columns(3)
                    b1.metric("남은 기간", f"{days_left}일")
                    b2.metric("💰 매출 초과액", f"+{diff_rev:,.0f}원", delta="초과 달성")
                    b3.metric("🛏️ RN 초과 판매", f"+{diff_rn:,.0f} RN", delta="초과 달성")
                
                # [Shortfall] 미달 시
                else:
                    short_rev = abs(diff_rev)
                    req_rn_day = (m_bud['rn'] - c_rn) / days_left
                    req_adr = short_rev / (m_bud['rn'] - c_rn) if (m_bud['rn'] - c_rn) > 0 else 0
                    
                    st.warning(f"🚨 100% 달성까지 {short_rev:,.0f}원 남았습니다.")
                    b1, b2, b3 = st.columns(3)
                    b1.metric("남은 기간", f"{days_left}일")
                    b2.metric("일일 필요 판매량", f"{req_rn_day:.1f} RN/일")
                    b3.metric("필요 평균 단가", f"{req_adr:,.0f}원")

        st.write("---")
        # 4개월 게이지
        for i in range(4):
            t_m = (analysis_month - 1 + i) % 12 + 1
            m_b = targets.get(t_m, {'rev_won':1, 'rn':1, 'adr':1, 'occ':1})
            m_data = otb_data[otb_data['일자_dt'].dt.month == t_m]
            
            if not m_data.empty:
                cur_rev = m_data['합계_매출'].sum()
                cur_rn = m_data['합계_객실'].sum()
                
                with st.expander(f"📌 {t_m}월 달성 현황 상세", expanded=(i==0)):
                    cols = st.columns(4)
                    fig_rev = go.Figure(go.Indicator(mode="gauge+number", value=(cur_rev/m_b['rev_won'])*100, title={'text':"매출(%)"}, gauge={'bar':{'color':"#FF4B4B"}}))
                    fig_rev.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=10))
                    cols[0].plotly_chart(fig_rev, use_container_width=True)
                    
                    fig_rn = go.Figure(go.Indicator(mode="gauge+number", value=(cur_rn/m_b['rn'])*100, title={'text':"RN(%)"}, gauge={'bar':{'color':"#FF4B4B"}}))
                    fig_rn.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=10))
                    cols[1].plotly_chart(fig_rn, use_container_width=True)
                    
                    cur_adr = cur_rev / cur_rn if cur_rn > 0 else 0
                    fig_adr = go.Figure(go.Indicator(mode="gauge+number", value=(cur_adr/m_b['adr'])*100, title={'text':"ADR(%)"}, gauge={'bar':{'color':"#FF4B4B"}}))
                    fig_adr.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=10))
                    cols[2].plotly_chart(fig_adr, use_container_width=True)
                    
                    days_in_m = calendar.monthrange(latest_booking_date.year, t_m)[1]
                    cur_occ = (cur_rn / (130 * days_in_m)) * 100
                    fig_occ = go.Figure(go.Indicator(mode="gauge+number", value=(cur_occ/m_b['occ'])*100, title={'text':"OCC(%)"}, gauge={'bar':{'color':"#FF4B4B"}}))
                    fig_occ.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=10))
                    cols[3].plotly_chart(fig_occ, use_container_width=True)

        st.divider()
        st.subheader("📈 미래 예약 Pace 흐름")
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=otb_future['일자_dt'], y=otb_future['점유율'], name='OCC(%)', marker_color='#a2d2ff', text=otb_future['점유율'], textposition='auto'))
        fig_p.add_trace(go.Scatter(x=otb_future['일자_dt'], y=otb_future['합계_ADR'], name='ADR', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
        
        fig_p.update_layout(
            yaxis2=dict(overlaying='y', side='right'),
            title="날짜별 점유율 vs ADR",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=50, t=50, b=50),
            uniformtext_minsize=8, uniformtext_mode='hide'
        )
        st.plotly_chart(fig_p, use_container_width=True)
        
        if st.button("🤖 AI 미래 전략 리포트"):
            if api_key:
                with st.spinner("AI 분석 시작..."):
                    stly_info = "제공됨" if not stly_data.empty else "부재"
                    prompt = f"""
                    RM 전문가로서 미래 전략을 수립하라.
                    [데이터 현황: {stly_info}]
                    [당월 달성률: {rev_rate:.1f}%]
                    
                    1. [종합 판단] 버짓 달성/미달 원인 및 전망.
                    2. [Yield 전략] 날짜별 고수요/저수요 대응 가격 전략.
                    3. [Action Plan] 부서별 실행 지침.
                    """
                    st.info(get_ai_insight(api_key, prompt))
    else:
        st.info("📉 OTB 데이터가 없습니다. 파일을 업로드해주세요.")
