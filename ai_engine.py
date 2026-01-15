import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    genai.configure(api_key=api_key.strip())
    
    # 모델 이름을 'gemini-1.5-flash'로만 써보세요. (v1beta 에러 방지)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    당신은 호텔 전문 분석가입니다. 아래 퓨어힐 호텔의 예약 데이터를 보고 분석 보고서를 작성하세요.
    1. 오늘 예약의 핵심 요약
    2. 데이터 특징 (리드타임, 숙박일수 등)
    3. 매출 증대를 위한 제언
    
    데이터:
    {data_summary}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"
