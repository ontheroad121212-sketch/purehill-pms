import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    # 1. API 키 설정 (공백 확실히 제거)
    clean_key = api_key.strip()
    genai.configure(api_key=clean_key)
    
    # 2. 시도해볼 모델 이름들 목록
    # 시스템에 따라 인식하는 이름이 달라서 여러번 찔러봅니다.
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    
    prompt = f"""
    당신은 호텔 전문 분석가입니다. 아래 퓨어힐 호텔의 예약 데이터를 보고 분석 보고서를 작성하세요.
    1. 오늘 예약의 핵심 요약 (총 건수 및 매출 등)
    2. 데이터 특징 (리드타임, 숙박일수 등의 의미)
    3. 매출 증대를 위한 구체적인 전략 제언 (한국어로)
    
    데이터 요약:
    {data_summary}
    """

    last_error = ""
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            return response.text # 성공하면 바로 결과 반환!
        except Exception as e:
            last_error = str(e)
            continue # 실패하면 다음 이름으로 시도
            
    return f"AI 연결 실패. 마지막 에러: {last_error}\n구글 AI 스튜디오에서 'Gemini API'가 활성화 상태인지 확인이 필요합니다."
