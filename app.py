import streamlit as st
import plotly.express as px
from processor import process_data
from ai_engine import get_ai_insight

# 1. 화면 설정
st.set_page_config(page_title="퓨어힐 PMS 프리미엄 리포트", layout="wide")

# 2. 사이드바: 설정 및 보안
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    st.info("입력하신 키는 세션이 종료되면 자동으로 파기됩니다.")
    st.divider()
    st.caption("v5.0: 사장님 요청 모든 지표 및 그래프 통합 완료")

# 3. 메인 타이틀
st.title("🏛️ 퓨어힐 호텔 경영 실적 분석 대시보드")
st.caption("전체/FIT/Group 수익 지표 및 상세 시각화 분석 리포트")

# 4. 파일 업로드
uploaded_file = st.file_uploader("PMS 엑셀 파일을 업로드하세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        # 지표 계산용 헬퍼 함수
        def calc_metrics(df):
            rev = df['판매금액'].sum()
            rn = df['room_nights'].sum()
            adr = rev / rn if rn > 0 else 0
            return rev, rn, adr

        # 데이터 분리
        fit_data = data[data['market_segment'] == 'FIT']
        grp_data = data[data['market_segment'] == 'Group']

        # --- 지표 1단: 전체 (Total) ---
        st.subheader("✅ [TOTAL] 전체 경영 실적")
        t_rev, t_rn, t_adr = calc_metrics(data)
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("전체 매출액", f"{t_rev:,.0f}원")
        tc2.metric("전체 룸나잇 (RN)", f"{t_rn:,.0f} RN")
        tc3.metric("전체 객단가 (ADR)", f"{t_adr:,.0f}원")
        st.write("---")

        # --- 지표 2단: FIT (개별) ---
        st.subheader("👤 [FIT] 개별 고객 실적")
        f_rev, f_rn, f_adr = calc_metrics(fit_data)
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("FIT 매출액", f"{f_rev:,.0f}원")
        fc2.metric("FIT 룸나잇", f"{f_rn:,.0f} RN")
        fc3.metric("FIT 객단가 (ADR)", f"{f_adr:,.0f}원")
        st.write("---")

        # --- 지표 3단: Group (단체) ---
        st.subheader("👥 [GROUP] 단체 고객 실적")
        g_rev, g_rn, g_adr = calc_metrics(grp_data)
        gc1, gc2, gc3 = st.columns(3)
        gc1.metric("그룹 매출액", f"{g_rev:,.0f}원")
        gc2.metric("그룹 룸나잇", f"{g_rn:,.0f} RN")
        gc3.metric("그룹 객단가 (ADR)", f"{g_adr:,.0f}원")
        st.divider()

        # --- 지표 4단: 행동 및 인구통계 ---
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

        # --- 5단: 시각화 분석 (사장님이 요청하신 그래프 4종) ---
        st.subheader("📈 상세 데이터 시각화")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 거래처별 매출 TOP 10")
            acc_rev = data.groupby('account')['판매금액'].sum().sort_values(ascending=True).tail(10).reset_index()
            fig_acc = px.bar(acc_rev, x='판매금액', y='account', orientation='h', color='판매금액', text_auto=',.0f')
            st.plotly_chart(fig_acc, use_container_width=True)
        with col2:
            st.subheader("🌐 예약 경로(Channel) 매출 비중")
            fig_pie = px.pie(data, values='판매금액', names='channel', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🛌 객실 타입별 객단가(ADR) 현황")
            room_stats = data.groupby('room_type').agg({'판매금액':'sum', 'room_nights':'sum'}).reset_index()
            room_stats['ADR'] = room_stats['판매금액'] / room_stats['room_nights']
            room_stats = room_stats.sort_values('ADR', ascending=False)
            fig_adr = px.bar(room_stats, x='room_type', y='ADR', color='ADR', text_auto=',.0f')
            st.plotly_chart(fig_adr, use_container_width=True)
        with col4:
            st.subheader("📅 예약 경로별 룸나잇(RN) 생산성")
            chan_rn = data.groupby('channel')['room_nights'].sum().reset_index()
            fig_rn = px.bar(chan_rn, x='channel', y='room_nights', text_auto=True, color_discrete_sequence=['#636EFA'])
            st.plotly_chart(fig_rn, use_container_width=True)

        # 6. AI 전략 제언
        st.divider()
        if st.button("🤖 AI 전문가 전략 리포트 받기"):
            if not api_key:
                st.warning("사이드바에 API Key를 넣어주세요!")
            else:
                with st.spinner("AI가 수익 데이터를 분석 중입니다..."):
                    summary = f"전체ADR:{t_adr:,.0f}, FIT_ADR:{f_adr:,.0f}, Group_ADR:{g_adr:,.0f}, 리드타임:{avg_lead:.1f}일, 국적:{nation_info}"
                    report = get_ai_insight(api_key, summary + " 시장별 수익 격차를 분석하고 수익 최적화 방안을 제안해줘.")
                    st.success("📝 AI 전문 분석 리포트")
                    st.markdown(report)

        # 7. 상세 데이터 표
        with st.expander("📝 원본 데이터 상세 보기"):
            st.dataframe(data)
