import pandas as pd

def process_data(uploaded_file):
    # 파일 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # 날짜 데이터 변환 (사장님 엑셀 컬럼명 기준)
    date_cols = ['예약일', '도착일', '출발일']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # 리드타임 & 숙박일수 계산
    if '도착일' in df.columns and '예약일' in df.columns:
        df['lead_time'] = (df['도착일'] - df['예약일']).dt.days
    if '출발일' in df.columns and '도착일' in df.columns:
        df['los'] = (df['출발일'] - df['도착일']).dt.days
        
    return df
