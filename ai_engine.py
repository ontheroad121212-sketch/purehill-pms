import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    # API Key 앞뒤 공백 제거
    genai.configure(api_key=api_key.strip())
    
    # 모델 설정 (가장 안정적인 모델명 사용)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    당신은 호텔 전문 분석가입니다. 아래의 퓨어힐 호텔 예약 데이터를 분석해 주세요.
    1. 오늘의 핵심 요약 (총 예약, 매출 등)
    2. 데이터 특징 분석 (리드타임, 숙박일수 등)
    3. 향후 매출 증대를 위한 마케팅 제언
    
    데이터 요약:
    {data_summary}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"
