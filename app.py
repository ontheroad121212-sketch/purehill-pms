import streamlit as st
from processor import process_data
from ai_engine import get_ai_insight

st.set_page_config(page_title="퓨어힐 PMS AI 대시보드", layout="wide")

st.title("🏨 퓨어힐 PMS AI 분석 비서")

# 사장님의 API Key를 여기에 넣으세요 (나중에는 보안 설정을 따로 할 수 있어요)
API_KEY = "여기에_복사한_API_KEY를_넣으세요" 

uploaded_file = st.file_uploader("PMS 파일을 올려주세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    # 숫자 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("총 예약", f"{len(data)}건")
    c2.metric("평균 리드타임", f"{data['lead_time'].mean():.1f}일")
    c3.metric("평균 숙박일수", f"{data['los'].mean():.1f}박")
    
    st.divider()
    
    # AI 분석 버튼
    if st.button("AI 전략 리포트 생성하기"):
        with st.spinner("AI가 데이터를 분석 중입니다... 잠시만 기다려주세요."):
            # 데이터 요약해서 AI에게 전달
            summary = {
                "total_bookings": len(data),
                "avg_lead_time": data['lead_time'].mean(),
                "avg_los": data['los'].mean(),
                "segments": data['판매금액'].sum() if '판매금액' in data.columns else "데이터 없음"
            }
            
            report = get_ai_insight(API_KEY, str(summary))
            
            st.subheader("🤖 AI 분석 결과")
            st.write(report)

    st.subheader("📋 전체 데이터 확인")
    st.dataframe(data)
