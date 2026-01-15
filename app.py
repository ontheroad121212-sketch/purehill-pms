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
    st.caption("v3.0: RN/ADR 및 FIT/Group 세그먼트 분석 모듈 탑재")

# 3. 메인 타이틀
st.title("🏛️ 퓨어힐 호텔 경영 실적 분석 대시보드")
st.caption("PMS 데이터를 기반으로 AI가 실시간 수익 관리(Revenue Management) 전략을 제안합니다.")

# 4. 파일 업로드
uploaded_file = st.file_uploader("PMS 엑셀 파일을 업로드하세요 (CSV, XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    # processor.py를 통해 데이터 가공 (룸나잇, 세그먼트 포함)
    data = process_data(uploaded_file)
    
    if not data.empty:
        # --- 1구역: 핵심 수익 지표 (KPI Metrics) ---
        st.subheader("📌 핵심 경영 실적 요약")
        c1, c2, c3, c4 = st.columns(4)
        
        total_rev = data['판매금액'].sum()
        total_rn = data['room_nights'].sum()
        # ADR 계산: 총 매출액 / 총 룸나잇(RN)
        adr = total_rev / total_rn if total_rn > 0 else 0
        best_acc = data.groupby('account')['판매금액'].sum().idxmax()
        
        c1.metric("누적 매출액", f"{total_rev:,.0f}원")
        c2.metric("총 룸나잇 (RN)", f"{total_rn:,.0f} RN")
        c3.metric("평균 객단가 (ADR)", f"{adr:,.0f}원")
        c4.metric("최고 매출 거래처", best_acc)

        st.divider()

        # --- 2구역: 시장 세그먼트 및 거래처 분석 ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 FIT vs Group 매출 비중")
            # 시장 분류(FIT/Group)에 따른 파이 차트
            fig_seg = px.pie(data, values='판매금액', names='market_segment', hole=0.5,
                             color_discrete_map={'FIT':'#00CC96', 'Group':'#EF553B'},
                             title="시장 세그먼트별 기여도")
            st.plotly_chart(fig_seg, use_container_width=True)

        with col2:
            st.subheader("🏢 거래처별 매출 TOP 10 (OTA 및 여행사)")
            # 거래처별 매출 합계 정렬
            acc_revenue = data.groupby('account')['판매금액'].sum().sort_values(ascending=True).tail(10).reset_index()
            fig_acc = px.bar(acc_revenue, x='판매금액', y='account', orientation='h',
                             color='판매금액', text_auto=',.0f', 
                             color_continuous_scale='Blues', title="어카운트 실적 순위")
            st.plotly_chart(fig_acc, use_container_width=True)

        # --- 3구역: 객실 수익성 및 생산성 트렌드 ---
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🛌 객실 타입별 ADR 현황")
            # 객실타입별 ADR(매출/RN) 계산
            room_stats = data.groupby('room_type').agg({'판매금액':'sum', 'room_nights':'sum'}).reset_index()
            room_stats['ADR'] = room_stats['판매금액'] / room_stats['room_nights']
            room_stats = room_stats.sort_values('ADR', ascending=False)
            
            fig_adr = px.bar(room_stats, x='room_type', y='ADR', color='ADR', 
                             text_auto=',.0f', color_continuous_scale='Viridis',
                             title="객실 타입별 수익성 비교")
            st.plotly_chart(fig_adr, use_container_width=True)

        with col4:
            st.subheader("📅 예약 경로별 룸나잇(RN) 생산성")
            # 채널별 생산성 분석
            chan_rn = data.groupby('channel')['room_nights'].sum().reset_index()
            fig_chan = px.bar(chan_rn, x='channel', y='room_nights', text_auto=True,
                              color_discrete_sequence=['#636EFA'], title="예약 경로별 총 판매 박수")
            st.plotly_chart(fig_chan, use_container_width=True)

        # --- 4구역: AI 전략 제언 ---
        st.divider()
        if st.button("🤖 AI 수익 관리 전문가 전략 리포트 받기"):
            if not api_key:
                st.warning("왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
            else:
                with st.spinner("전문가 AI가 수익 데이터를 정밀 분석 중입니다..."):
                    # 풍부한 수익 데이터를 AI에게 요약 전달
                    summary = f"""
                    [퓨어힐 실적 데이터 요약]
                    - 총 매출: {total_rev:,.0f}원
                    - 총 룸나잇: {total_rn:,.0f} RN
                    - 평균 ADR: {adr:,.0f}원
                    - 세그먼트 비중: {data['market_segment'].value_counts(normalize=True).to_dict()}
                    - 최다 매출 거래처: {best_acc}
                    - 인기 객실: {data['room_type'].value_counts().idxmax()}
                    - 평균 리드타임: {data['lead_time'].mean():.1f}일
                    """
                    # 구체적인 전략을 묻는 프롬프트
                    report = get_ai_insight(api_key, summary + " 이 실적을 바탕으로 ADR 상승 전략과 FIT/Group 맞춤형 마케팅 방안을 제안해줘.")
                    st.success("📝 AI 전문 분석 리포트")
                    st.markdown(report)
        
        # 5. 상세 데이터 표 (거래처별 분석 표 추가)
        st.divider()
        st.subheader("📋 상세 실적 데이터 시트")
        
        tab1, tab2 = st.tabs(["거래처별 상세 실적", "전체 원본 데이터"])
        
        with tab1:
            acc_table = data.groupby('account').agg({
                '판매금액': 'sum',
                'room_nights': 'sum',
                '예약일': 'count'
            }).rename(columns={'room_nights': '총 RN', '예약일': '예약건수'}).sort_values('판매금액', ascending=False)
            
            # ADR 컬럼 추가 계산
            acc_table['ADR'] = acc_table['판매금액'] / acc_table['총 RN']
            
            st.dataframe(acc_table.style.format({
                '판매금액': '{:,.0f}원', 
                '총 RN': '{:,.0f} RN',
                'ADR': '{:,.0f}원'
            }))

        with tab2:
            st.dataframe(data)

    else:
        st.error("데이터를 분석할 수 없습니다. 엑셀 파일의 형식을 다시 확인해주세요.")
