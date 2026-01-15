import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight

# 1. 화면 설정 (가로로 넓게 사용)
st.set_page_config(page_title="엠버퓨어힐 경영 분석 프리미엄", layout="wide")

# 대시보드 가독성을 위한 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }
    </style>
    """, unsafe_allow_html=True)

# 2. 사이드바: 설정 및 보안
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.info("입력하신 키는 세션 종료 시 자동으로 파기됩니다.")
    st.divider()
    st.caption("v7.0: 글로벌 OTA 분석 및 일반 거래처 행태 분석 모듈")

# 3. 메인 타이틀
st.title("🏛️ 엠버퓨어힐 호텔 경영 실적 분석 대시보드")
st.caption("전체/FIT/Group 세그먼트별 순수 객실 실적 및 채널별 고객 행태 정밀 분석")

# 4. 파일 업로드
uploaded_file = st.file_uploader("PMS 엑셀 파일을 업로드하세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # 지표 계산용 헬퍼 함수 (총매출, 객실매출, RN, 객실 ADR 산출)
        def calc_metrics(df):
            total_sales = df['총매출액'].sum()
            room_sales = df['객실매출액'].sum()
            rn = df['room_nights'].sum()
            adr = room_sales / rn if rn > 0 else 0
            return total_sales, room_sales, rn, adr

        # 데이터 세그먼트 분리
        fit_data = data[data['market_segment'] == 'FIT']
        grp_data = data[data['market_segment'] == 'Group']

        # --- 1구역: 전체 실적 (Total) ---
        st.subheader("✅ [TOTAL] 전체 경영 실적 (총매출 vs 객실매출)")
        t_total, t_room, t_rn, t_adr = calc_metrics(data)
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("전체 총매출", f"{t_total:,.0f}원")
        tc2.metric("순수 객실매출", f"{t_room:,.0f}원")
        tc3.metric("총 룸나잇 (RN)", f"{t_rn:,.0f} RN")
        tc4.metric("전체 객실 ADR", f"{t_adr:,.0f}원")
        st.write("---")

        # --- 2구역: FIT 실적 (개별) ---
        st.subheader("👤 [FIT] 개별 고객 실적")
        f_total, f_room, f_rn, f_adr = calc_metrics(fit_data)
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("FIT 총매출", f"{f_total:,.0f}원")
        fc2.metric("FIT 객실매출", f"{f_room:,.0f}원")
        fc3.metric("FIT 룸나잇", f"{f_rn:,.0f} RN")
        fc4.metric("FIT 객실 ADR", f"{f_adr:,.0f}원")
        st.write("---")

        # --- 3구역: Group 실적 (단체/마이스) ---
        st.subheader("👥 [GROUP] 단체 고객 실적")
        g_total, g_room, g_rn, g_adr = calc_metrics(grp_data)
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("그룹 총매출", f"{g_total:,.0f}원")
        gc2.metric("그룹 객실매출", f"{g_room:,.0f}원")
        gc3.metric("그룹 룸나잇", f"{g_rn:,.0f} RN")
        gc4.metric("그룹 객실 ADR", f"{g_adr:,.0f}원")

        st.divider()

        # --- 4구역: 통합 행동 지표 ---
        st.subheader("📊 고객 행동 및 국적 지표")
        b1, b2, b3 = st.columns(3)
        avg_lead = data['lead_time'].mean()
        avg_los = data['los'].mean()
        nation_counts = data['country'].value_counts(normalize=True).head(3) * 100
        nation_info = " / ".join([f"{k}: {v:.1f}%" for k, v in nation_counts.to_dict().items()])
        b1.metric("📅 평균 리드타임", f"{avg_lead:.1f}일")
        b2.metric("🌙 평균 숙박일수 (LOS)", f"{avg_los:.1f}박")
        b3.metric("🌍 주요 국적비 (TOP 3)", nation_info)

        st.divider()

        # --- 5구역: 시각화 분석 (총 5개 그래프) ---
        st.subheader("📈 채널 및 거래처 심층 분석")
        
        # [데이터 필터링] 마이스 및 그룹을 제외한 일반 거래처(FIT 마켓)
        pure_acc_stats = fit_data[~fit_data['account'].str.contains('마이스|그룹|MICE|GROUP', na=False)]
        acc_stats = pure_acc_stats.groupby('account').agg({
            'room_nights': 'sum',
            '객실매출액': 'sum',
            'los': 'mean',
            'lead_time': 'mean'
        }).reset_index()
        acc_stats['ADR'] = acc_stats['객실매출액'] / acc_stats['room_nights']

        # 열 레이아웃 1: 생산성 및 ADR
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 거래처별 룸나잇 생산성 (TOP 10)")
            fig_rn = px.bar(acc_stats.sort_values('room_nights').tail(10), x='room_nights', y='account', orientation='h',
                            color='room_nights', text_auto=True, color_continuous_scale='Blues')
            st.plotly_chart(fig_rn, use_container_width=True)
        with col2:
            st.subheader("💰 거래처별 객실 ADR 현황 (TOP 10)")
            fig_adr = px.bar(acc_stats.sort_values('ADR').tail(10), x='ADR', y='account', orientation='h',
                             color='ADR', text_auto=',.0f', color_continuous_scale='Greens')
            st.plotly_chart(fig_adr, use_container_width=True)

        # 열 레이아웃 2: LOS 및 리드타임 (신규)
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🌙 거래처별 평균 숙박일수 (LOS)")
            fig_los = px.bar(acc_stats.sort_values('los').tail(10), x='los', y='account', orientation='h',
                             color='los', text_auto='.1f', color_continuous_scale='Purples')
            st.plotly_chart(fig_los, use_container_width=True)
        with col4:
            st.subheader("📅 거래처별 평균 리드타임")
            fig_lead = px.bar(acc_stats.sort_values('lead_time').tail(10), x='lead_time', y='account', orientation='h',
                              color='lead_time', text_auto='.1f', color_continuous_scale='Oranges')
            st.plotly_chart(fig_lead, use_container_width=True)

        # 열 레이아웃 3: 글로벌 OTA 국적비 (신규)
        st.subheader("🌍 글로벌 채널 국적 비중 분석 (아고다/익스피디아/부킹/트립)")
        global_ota = data[data['is_global_ota'] == True]
        if not global_ota.empty:
            fig_global = px.bar(global_ota, x="account", color="country", 
                                title="주요 글로벌 OTA별 국적 구성 (건수 기준)",
                                barmode="stack", text_auto=True)
            st.plotly_chart(fig_global, use_container_width=True)
        else:
            st.info("글로벌 OTA 채널 데이터가 부족합니다.")

        # --- 6구역: AI 전략 제언 ---
        st.divider()
        if st.button("🤖 AI 전문가 수익 분석 리포트 받기"):
            if not api_key:
                st.warning("사이드바에 API Key를 먼저 입력해주세요!")
            else:
                with st.spinner("전문가 AI가 데이터를 정밀 분석 중입니다..."):
                    summary = f"""
                    [엠버퓨어힐 실적 데이터 요약]
                    - 전체 ADR(객실): {t_adr:,.0f}원 / FIT ADR: {f_adr:,.0f}원
                    - FIT 비중: {f_room/t_total*100:.1f}% / Group 비중: {g_room/t_total*100:.1f}%
                    - 글로벌 OTA 국적: {global_ota['country'].value_counts().head(3).to_dict() if not global_ota.empty else 'N/A'}
                    - 평균 LOS: {avg_los:.1f}박 / 평균 리드타임: {avg_lead:.1f}일
                    """
                    report = get_ai_insight(api_key, summary + " 거래처별 LOS와 리드타임 특성을 고려하여, 채널별 수익 최적화 및 타겟 마케팅 방안을 제안해줘.")
                    st.success("📝 AI 전문 분석 리포트")
                    st.markdown(report)
        
        # 7. 상세 데이터 표
        with st.expander("📝 상세 데이터 시트 보기"):
            st.dataframe(data)

    else:
        st.error("데이터를 분석할 수 없습니다. 엑셀 파일의 형식을 다시 확인해주세요.")
