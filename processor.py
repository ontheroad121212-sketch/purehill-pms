import pandas as pd

def process_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, skiprows=2) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    
    mapping = {
        '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
        '총금액': '판매금액', '박수': 'los', '예약경로': 'channel',
        '객실타입': 'room_type', '국적': 'country', '시장': 'market',
        '상태': 'status', '거래처': 'account'  # <-- 거래처 추가!
    }
    df = df.rename(columns=mapping)
    
    # 데이터 정제
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)
    
    # 공백 데이터 처리 (아고다, 부킹닷컴 등이 텍스트로 잘 들어오게)
    df['account'] = df['account'].fillna('개인/직접')
    df['channel'] = df['channel'].fillna('기타')
    
    return df[df['status'] != '취소']
