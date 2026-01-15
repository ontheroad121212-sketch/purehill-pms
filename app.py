import streamlit as st
from processor import process_data

st.set_page_config(page_title="퓨어힐 대시보드", layout="wide")

st.title("🏨 퓨어힐 PMS 데일리 분석")

uploaded_file = st.file_uploader("PMS 파일을 올려주세요", type=['csv', 'xlsx'])

if uploaded_file:
    data = process_data(uploaded_file)
    
    st.divider()
    # 요약 지표 보여주기
    c1, c2, c3 = st.columns(3)
    c1.metric("총 예약", f"{len(data)}건")
    c2.metric("평균 리드타임", f"{data['lead_time'].mean():.1f}일")
    c3.metric("평균 숙박일수", f"{data['los'].mean():.1f}박")
    
    st.subheader("상세 데이터")
    st.dataframe(data)
