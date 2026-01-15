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

    # 항목 이름의 공백 제거
    df.columns = df.columns.str.strip()
    
    # 퓨어힐 엑셀 항목명 -> 시스템용 이름 매핑
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '판매금액', '박수': 'los', '예약경로': 'channel',
        '객실타입': 'room_type', '국적': 'country', '시장': 'market',
        '상태': 'status', '거래처': 'account', '객실수': 'rooms'
    }
    df = df.rename(columns=mapping)
    
    # 데이터 타입 및 숫자 변환
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)
    
    # [핵심] 룸나잇(RN) 계산: 판매한 객실 수 * 박수
    df['room_nights'] = df['rooms'] * df['los']
    
    # [핵심] 리드타임 계산
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)
    
    # [핵심] FIT / Group 구분 로직
    def classify_market(m):
        m_str = str(m).upper()
        # 시장 코드에 GRP, GROUP, DOS, BGRP 등이 포함되면 Group으로 간주
        if any(key in m_str for key in ['GRP', 'GROUP', 'DOS', 'BGRP']):
            return 'Group'
        return 'FIT'
    
    df['market_segment'] = df['market'].apply(classify_market)
    df['account'] = df['account'].fillna('개인/현장')
    
    # '취소' 상태 데이터 제외 (실제 실적 중심)
    df = df[df['status'] != '취소']
    
    return df
