import pandas as pd

def process_data(uploaded_file):
    # 사장님 엑셀은 1번째 줄(0번)이 제목이 아니므로 2번째 줄(index 1)부터 읽습니다.
    try:
        df = pd.read_csv(uploaded_file, skiprows=1)
    except:
        df = pd.read_excel(uploaded_file, skiprows=1)
    
    # 실제 엑셀 항목명과 우리가 쓸 항목명을 연결해줍니다.
    # 엑셀항목명 : 우리코드항목명
    mapping = {
        '예약일자': '예약일',
        '입실일자': '도착일',
        '퇴실일자': '출발일',
        '총금액': '판매금액',
        '박수': 'los'
    }
    df = df.rename(columns=mapping)
    
    # 날짜 데이터로 변환 (컴퓨터가 계산할 수 있게)
    for col in ['예약일', '도착일', '출발일']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # 리드타임 계산 (도착일 - 예약일)
    if '도착일' in df.columns and '예약일' in df.columns:
        df['lead_time'] = (df['도착일'] - df['예약일']).dt.days
    
    # 혹시 리드타임 계산이 안됐을 경우를 대비해 0으로 채워줌
    if 'lead_time' not in df.columns:
        df['lead_time'] = 0
        
    return df
