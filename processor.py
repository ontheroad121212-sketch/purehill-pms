import pandas as pd

def process_data(uploaded_file):
    # 1. 파일 읽기 (2번째 줄부터 제목으로 인식)
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
    except Exception as e:
        return pd.DataFrame()

    # 2. 항목 이름의 앞뒤 공백 제거 (매우 중요!)
    df.columns = df.columns.str.strip()
    
    # 3. 항목 이름 매핑 (사장님 엑셀에 맞춰서 정확히!)
    mapping = {
        '예약일자': '예약일',
        '입실일자': '도착일',
        '퇴실일자': '출발일',
        '총금액': '판매금액',
        '박수': 'los'
    }
    df = df.rename(columns=mapping)
    
    # 4. 날짜 데이터로 변환
    for col in ['예약일', '도착일', '출발일']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # 5. 리드타임 계산 (도착일 - 예약일)
    if '도착일' in df.columns and '예약일' in df.columns:
        df['lead_time'] = (df['도착일'] - df['예약일']).dt.days
    
    # 6. 판매금액 숫자 변환 (쉼표 등 제거)
    if '판매금액' in df.columns:
        df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
        
    return df
