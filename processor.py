import pandas as pd
from datetime import datetime, timedelta

def process_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=2)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '총매출액', '객실료': '객실매출액', '박수': 'los', 
        '객실타입': 'room_type', '국적': 'country', '시장': 'market',
        '상태': 'status', '거래처': 'account', '객실수': 'rooms'
    }
    df = df.rename(columns=mapping)
    
    # [데이터 정제] 합계 제외 및 취소 데이터 제거
    if '고객명' in df.columns:
        df = df[df['고객명'].str.contains('합계|총합계') == False]
    df = df[df['status'].str.strip().isin(['RR', 'CI', 'RC'])]
    
    # [날짜 형식 변환]
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    
    # [수치 변환]
    df['총매출액'] = pd.to_numeric(df['총매출액'], errors='coerce').fillna(0)
    df['객실매출액'] = pd.to_numeric(df['객실매출액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)
    df['room_nights'] = df['rooms'] * df['los']
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)

    # [마켓 분류]
    def classify_market(m):
        m_str = str(m).upper()
        if any(key in m_str for key in ['GRP', 'GROUP', 'DOS', 'BGRP', 'MICE']):
            return 'Group'
        return 'FIT'
    df['market_segment'] = df['market'].apply(classify_market)
    
    # [글로벌 OTA 판별]
    def is_global(acc):
        acc_u = str(acc).upper()
        globals = ['AGODA', 'EXPEDIA', 'BOOKING', 'TRIP', '아고다', '부킹닷컴', '익스피디아', '트립닷컴']
        return any(g in acc_u for g in globals)
    df['is_global_ota'] = df['account'].apply(is_global)
    
    return df
