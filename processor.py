import pandas as pd

def process_data(uploaded_file):
    try:
        # 2번째 줄(인덱스 1)이 실제 제목줄임
        df = pd.read_csv(uploaded_file, skiprows=2) 
    except:
        df = pd.read_excel(uploaded_file, skiprows=2)
    
    # 항목명 정리
    df.columns = df.columns.str.strip()
    
    # 사장님 엑셀 실제 이름 -> 코드용 이름
    mapping = {
        '예약일자': '예약일',
        '입실일자': '도착일',
        '퇴실일자': '출발일',
        '총금액': '판매금액',
        '박수': 'los'
    }
    df = df.rename(columns=mapping)
    
    # 날짜로 강제 변환
    df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
    df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
    
    # 리드타임 계산 (도착일 - 예약일)
    df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)
    
    # 금액 숫자 변환
    df['판매금액'] = pd.to_numeric(df['판매금액'], errors='coerce').fillna(0)
    df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
    
    return df
