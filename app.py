import streamlit as st
from processor import process_data
from ai_engine import get_ai_insight

st.set_page_config(page_title="퓨어힐 PMS AI 비서", layout="wide")
st.title("🏨 퓨어힐 PMS AI 분석 비서")

API_KEY = "AIzaSyA7JanbIy4xRr0ICGO8pDOqZvxq2mPPg20" 

uploaded_file = st.file_uploader("PMS 파일을 올려주세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    if not data.empty:
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        
        # 실제 데이터 계산
        total_cnt = len(data)
        avg_lead = data['lead_time'].mean()
        avg_los = data['los'].mean()
        total_rev = data['판매금액'].sum()
        
        c1.metric("총 예약", f"{total_cnt}건")
        c2.metric("평균 리드타임", f"{avg_lead:.1f}일")
        c3.metric("평균 숙박일수", f"{avg_los:.1f}박")
        c4.metric("총 판매금액", f"{total_rev:,.0f}원")
        
        if st.button("🤖 AI 전략 리포트 생성하기"):
            with st.spinner("AI가 데이터를 분석 중입니다..."):
                summary = f"총예약:{total_cnt}, 리드타임:{avg_lead:.1f}일, 숙박:{avg_los:.1f}박, 매출:{total_rev:,.0f}"
                report = get_ai_insight(API_KEY, summary)
                st.markdown(report)
        
        st.dataframe(data)
