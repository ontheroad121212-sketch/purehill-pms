import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    당신은 호텔 전문 분석가입니다. 아래의 예약 현황 데이터를 보고 
    1. 오늘의 핵심 요약
    2. 주목해야 할 특징 (리드타임, 숙박일수 등)
    3. 매출 증대를 위한 구체적인 전략 제언
    을 한국어로 친절하게 작성해 주세요.
    
    데이터 요약:
    {data_summary}
    """
    
    response = model.generate_content(prompt)
    return response.text
