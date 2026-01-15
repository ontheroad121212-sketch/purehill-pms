import pandas as pd

def process_data(uploaded_file):
    try:
        # 사장님 엑셀 특성에 맞춰 2줄 건너뛰고 읽기
        df = pd.read_csv(uploaded_file, skiprows=2) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    
    # AI와 그래프가 사용할 핵심 항목들 매핑
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '판매금액', '박수': 'los', '예약경로': 'channel',
        '객실타입': 'room_type', '국적': 'country', '시장': 'market',
        '상태': 'status'
    }
    df = df.rename(columns=mapping)
    
    # 데이터 정제 (날짜/숫자/공백제거)
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)
    
    # 취소된 예약 제외 (분석 정확도 향상)
    df = df[df['status'] != '취소'] 
    
    return df
