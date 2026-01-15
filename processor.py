import pandas as pd
from datetime import timedelta

def process_data(uploaded_file):
    try:
        # 파일 읽기 (상단 제목부 제외를 위해 기본 2줄 스킵)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=2)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
    except:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    # --- [유형 1] 예약 생성 데이터 (Production) 판단 ---
    if '고객명' in df.columns or '예약일자' in df.columns:
        mapping = {
            '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
            '총금액': '총매출액', '객실료': '객실매출액', '박수': 'los', 
            '객실타입': 'room_type', '국적': 'country', '시장': 'market',
            '상태': 'status', '거래처': 'account', '객실수': 'rooms',
            '서비스코드': 'service_code', '요금타입': 'rate_type', '패키지': 'package'
        }
        df = df.rename(columns=mapping)
        
        # 합계 제외 및 상태 필터링
        if '고객명' in df.columns:
            df = df[df['고객명'].str.contains('합계|총합계') == False]
        df = df[df['status'].str.strip().isin(['RR', 'CI', 'RC'])]
        df = df[df['status'] != '취소'] 

        # 수치 변환
        df['총매출액'] = pd.to_numeric(df['총매출액'], errors='coerce').fillna(0)
        df['객실매출액'] = pd.to_numeric(df['객실매출액'], errors='coerce').fillna(0)
        df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
        df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)
        df['room_nights'] = df['rooms'] * df['los']
        df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
        df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
        df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)

        # 조식 판별
        def check_breakfast(row):
            check_str = f"{row.get('service_code', '')} {row.get('rate_type', '')} {row.get('package', '')}".upper()
            if any(kw in check_str for kw in ['BF', '조식', 'BFR', 'BB', 'B.F']):
                return '조식포함'
            return '조식불포함'
        df['breakfast_status'] = df.apply(check_breakfast, axis=1)

        # 마켓 분류 (FIT / Group)
        def classify_market(m):
            m_str = str(m).upper()
            if any(key in m_str for key in ['GRP', 'GROUP', 'DOS', 'BGRP', 'MICE']):
                return 'Group'
            return 'FIT'
        df['market_segment'] = df['market'].apply(classify_market)
        
        # 글로벌 OTA 판별
        def is_global(acc):
            acc_u = str(acc).upper()
            globals = ['AGODA', 'EXPEDIA', 'BOOKING', 'TRIP', '아고다', '부킹닷컴', '익스피디아', '트립닷컴']
            return any(g in acc_u for g in globals)
        df['is_global_ota'] = df['account'].apply(is_global)
        
        df['data_type'] = 'PROD'
        return df

    # --- [유형 2] 영업 현황 데이터 (OTB) 판단 ---
    elif '합계' in df.columns or 'RevPAR' in df.columns or '점유율(%)' in df.columns:
        # OTB 파일은 컬럼이 매우 많으므로 위치 기반으로 필요한 것만 매핑
        # (사장님이 주신 파일 구조: 일자, 요일, 개인(객실/비율/ADR/매출/비율), 단체(...), 내부, 무료, 합계(객실/OCC/ADR/RevPAR/매출))
        df.columns = ['일자', '요일', '개인_객실', '개인_비율', '개인_ADR', '개인_매출', '개인_매출비율', 
                      '단체_객실', '단체_비율', '단체_ADR', '단체_매출', '단체_매출비율', 
                      '내부이용', '무료', '합계_객실', '점유율', '합계_ADR', 'RevPAR', '합계_매출']
        
        # 날짜가 아닌 행(Sub-total 등) 제거 로직
        df['일자_dt'] = pd.to_datetime(df['일자'], errors='coerce')
        df = df.dropna(subset=['일자_dt'])
        
        # 수치 변환
        cols_to_fix = ['점유율', '합계_매출', '합계_ADR', '합계_객실', 'RevPAR']
        for col in cols_to_fix:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['data_type'] = 'OTB'
        return df

    return pd.DataFrame()
