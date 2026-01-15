import pandas as pd

def process_data(uploaded_file):
    try:
        # 엑셀/CSV 구분해서 읽기 (맨 위 2줄은 필터정보라 제외)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=2)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    # 항목 이름의 앞뒤 공백 제거
    df.columns = df.columns.str.strip()
    
    # 퓨어힐 엑셀 항목명 -> 시스템용 이름 매핑
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '판매금액', '박수': 'los', '예약경로': 'channel',
        '객실타입': 'room_type', '국적': 'country', '시장': 'market',
        '상태': 'status', '거래처': 'account', '고객수': 'guests'
    }
    df = df.rename(columns=mapping)
    
    # 날짜 데이터 변환
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    
    # 숫자 데이터 변환 (금액, 박수 등)
    df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    
    # 리드타임 계산
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)
    
    # 거래처가 비어있으면 '개인/직접'으로 표시
    df['account'] = df['account'].fillna('개인/현장')
    
    # 분석의 정확도를 위해 '취소'된 예약은 제외하고 분석
    df = df[df['status'] != '취소']
    
    return df
