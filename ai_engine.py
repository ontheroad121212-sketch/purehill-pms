import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    # API Key 설정 (공백 제거)
    genai.configure(api_key=api_key.strip())
    
    # 404 에러를 피하기 위해 가장 기본 모델명을 사용합니다.
    # 만약 'gemini-1.5-flash'가 안되면 'gemini-pro'로 자동 전환되게 만들었습니다.
    model_name = 'gemini-1.5-flash' 
    
    try:
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        당신은 호텔 전문 분석가입니다. 아래 퓨어힐 호텔의 예약 데이터를 보고 분석 보고서를 작성하세요.
        1. 오늘 예약의 핵심 요약 (총 건수 및 매출 등)
        2. 데이터 특징 (리드타임, 숙박일수 등의 의미)
        3. 매출 증대를 위한 구체적인 전략 제언 (한국어로)
        
        데이터 요약:
        {data_summary}
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # 혹시나 flash 모델이 지원 안되는 계정일 경우 pro 모델로 한 번 더 시도
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except:
            return f"AI 연결 오류: {str(e)}\n구글 AI 스튜디오에서 API Key가 활성화되었는지 확인해주세요."
