import pandas as pd
from datetime import timedelta

def process_data(uploaded_files, is_otb=False):
    if not uploaded_files:
        return pd.DataFrame()
    
    # 리스트 형식이 아니면 리스트로 변환 (단일 업로드와 다중 업로드 모두 대응)
    files = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
    combined_df = pd.DataFrame()

    for uploaded_file in files:
        try:
            # 실적 데이터는 2줄 스킵, 온더북(영업현황)은 데이터만 뽑기 위해 3줄 스킵이 적절함
            if is_otb:
                df = pd.read_csv(uploaded_file, skiprows=3) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, skiprows=3)
            else:
                df = pd.read_csv(uploaded_file, skiprows=2) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, skiprows=2)
        except:
            continue

        df.columns = df.columns.str.strip()

        # --- [유형 1] 예약 생성 데이터 (Production) ---
        if not is_otb:
            mapping = {
                '예약일자': '예약일', '입실일자': '도착일', '퇴실일자': '출발일',
                '총금액': '총매출액', '객실료': '객실매출액', '박수': 'los', 
                '객실타입': 'room_type', '국적': 'country', '시장': 'market',
                '상태': 'status', '거래처': 'account', '객실수': 'rooms',
                '서비스코드': 'service_code', '요금타입': 'rate_type', '패키지': 'package'
            }
            df = df.rename(columns=mapping)
            if '고객명' in df.columns:
                df = df[df['고객명'].str.contains('합계|총합계') == False]
            df = df[df['status'].str.strip().isin(['RR', 'CI', 'RC'])]
            df = df[df['status'] != '취소'] 

            df['총매출액'] = pd.to_numeric(df['총매출액'], errors='coerce').fillna(0)
            df['객실매출액'] = pd.to_numeric(df['객실매출액'], errors='coerce').fillna(0)
            df['los'] = pd.to_numeric(df['los'], errors='coerce').fillna(0)
            df['rooms'] = pd.to_numeric(df['rooms'], errors='coerce').fillna(1)
            df['room_nights'] = df['rooms'] * df['los']
            df['예약일'] = pd.to_datetime(df['예약일'], errors='coerce')
            df['도착일'] = pd.to_datetime(df['도착일'], errors='coerce')
            df['lead_time'] = (df['도착일'] - df['예약일']).dt.days.fillna(0)

            # 조식/마켓/글로벌 로직
            df['breakfast_status'] = df.apply(lambda r: '조식포함' if any(kw in f"{r.get('service_code','')} {r.get('rate_type','')} {r.get('package','')}".upper() for kw in ['BF', '조식', 'BFR', 'BB']) else '조식불포함', axis=1)
            df['market_segment'] = df['market'].apply(lambda x: 'Group' if any(k in str(x).upper() for k in ['GRP', 'GROUP', 'DOS', 'BGRP', 'MICE']) else 'FIT')
            df['is_global_ota'] = df['account'].apply(lambda x: any(g in str(x).upper() for g in ['AGODA', 'EXPEDIA', 'BOOKING', 'TRIP', '아고다', '부킹닷컴', '익스피디아', '트립닷컴']))
            combined_df = pd.concat([combined_df, df])

        # --- [유형 2] 영업 현황 데이터 (OTB) ---
        else:
            # 영업현황 파일의 컬럼 재설정 (사장님 파일의 19개 컬럼 구조)
            if len(df.columns) >= 19:
                df = df.iloc[:, :19]
                df.columns = ['일자', '요일', '개인_객실', '개인_비율', '개인_ADR', '개인_매출', '개인_매출비율', 
                              '단체_객실', '단체_비율', '단체_ADR', '단체_매출', '단체_매출비율', 
                              '내부이용', '무료', '합계_객실', '점유율', '합계_ADR', 'RevPAR', '합계_매출']
                
                # '일자'가 날짜 형식이 아닌 행(Sub-total, Total 등) 제거
                df['일자_dt'] = pd.to_datetime(df['일자'], errors='coerce')
                df = df.dropna(subset=['일자_dt'])
                
                for col in ['점유율', '합계_매출', '합계_ADR', '합계_객실', 'RevPAR']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                combined_df = pd.concat([combined_df, df])

    if not combined_df.empty and is_otb:
        # 여러 달의 파일을 합친 후 날짜순 정렬 및 중복(겹치는 날짜) 제거
        combined_df = combined_df.sort_values('일자_dt').drop_duplicates('일자_dt')
        
    return combined_df
