import pandas as pd

def process_data(uploaded_file):
    try:
        # 엑셀/CSV 구분해서 읽기 (제목 위 2줄 제외)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=2)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    # 항목 이름의 앞뒤 공백 제거
    df.columns = df.columns.str.strip()
    
    # [업데이트] 사장님 요청에 따라 '객실료'와 '총금액'을 명확히 분리 매핑
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '총매출액',   # 전체 금액 (식음료 등 포함)
        '객실료': '객실매출액', # 순수 객실 판매 금액
        '박수': 'los', 
        '객실타입': 'room_type', 
        '국적': 'country', 
        '시장': 'market',
        '상태': 'status', 
        '거래처': 'account', 
        '객실수': 'rooms'
    }
    df = df.rename(columns=mapping)
    
    # [가장 중요] 엑셀 맨 밑의 '총합계' 줄 제거 (필터링 강화)
    # 고객명에 '합계'가 포함된 모든 행을 제거하여 RN 뻥튀기 방지
    if '고객명' in df.columns:
        df = df[df['고객명'].str.contains('합계|총합계') == False]
    
    # 상태값 정제 및 취소 데이터 제외
    df = df[df['status'].str.strip().isin(['RR', 'CI', 'RC'])]
    df = df[df['status'] != '취소'] 

    # 데이터 타입 변환 (숫자형)
    df['총매출액'] = pd.to_numeric(df['총매출액'], errors='coerce').fillna(0)
    df['객실매출액'] = pd.to_numeric(df['객실매출액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)
    
    # [업데이트] 룸나잇(RN) 계산: 실제 객실수 * 박수
    df['room_nights'] = df['rooms'] * df['los']
    
    # 날짜 데이터 변환 및 리드타임 계산
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)

    # FIT / Group 분류
    def classify_market(m):
        m_str = str(m).upper()
        if any(key in m_str for key in ['GRP', 'GROUP', 'DOS', 'BGRP']):
            return 'Group'
        return 'FIT'
    
    df['market_segment'] = df['market'].apply(classify_market)
    df['account'] = df['account'].fillna('개인/현장')
    
    return df
