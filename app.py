import streamlit as st
from processor import process_data
from ai_engine import get_ai_insight

st.set_page_config(page_title="퓨어힐 PMS AI 대시보드", layout="wide")
st.title("🏨 퓨어힐 PMS AI 분석 비서")

# 여기에 사장님의 API Key를 꼭! 따옴표 안에 넣어주세요
API_KEY = "AIzaSyA7JanbIy4xRr0ICGO8pDOqZvxq2mPPg20" 

uploaded_file = st.file_uploader("PMS 파일을 올려주세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        
        # 숫자 계산 (NaN 값 제외하고 평균 계산)
        avg_lead = data['lead_time'].mean() if 'lead_time' in data.columns else 0
        avg_los = data['los'].mean() if 'los' in data.columns else 0
        total_rev = data['판매금액'].sum() if '판매금액' in data.columns else 0
        
        c1.metric("총 예약", f"{len(data)}건")
        c2.metric("평균 리드타임", f"{avg_lead:.1f}일")
        c3.metric("평균 숙박일수", f"{avg_los:.1f}박")
        c4.metric("총 판매금액", f"{total_rev:,.0f}원")
        
        st.divider()
        
        if st.button("🤖 AI 전략 리포트 생성하기"):
            if API_KEY == "여기에_사장님_API_KEY_넣기":
                st.error("API Key를 먼저 입력해주세요!")
            else:
                with st.spinner("AI가 데이터를 분석 중입니다..."):
                    summary = f"""
                    - 총 예약 건수: {len(data)}
                    - 평균 리드타임: {avg_lead:.1f}일
                    - 평균 숙박일수: {avg_los:.1f}박
                    - 총 매출: {total_rev:,.0f}원
                    - 주요 예약 경로: {data['예약경로'].value_counts().head(3).to_dict() if '예약경로' in data.columns else '정보없음'}
                    """
                    report = get_ai_insight(API_KEY, summary)
                    st.info("AI의 분석 결과입니다.")
                    st.markdown(report)

        st.subheader("📋 전체 데이터 확인")
        st.dataframe(data)
