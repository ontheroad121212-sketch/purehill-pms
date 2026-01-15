import google.generativeai as genai

def get_ai_insight(api_key, data_summary):
    # 1. API 키 설정
    genai.configure(api_key=api_key.strip())
    
    # 2. 에러가 났던 v1beta 통로 대신 표준 통로를 강제 지정합니다.
    # 모델 이름을 단순화하여 전달합니다.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') # 'models/'를 빼고 시도
        
        prompt = f"""
        당신은 호텔 전문 분석가입니다. 아래 퓨어힐 호텔의 데이터를 보고 한국어로 분석 보고서를 작성하세요.
        - 요약: {data_summary}
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # 그래도 안되면 모델명을 'models/gemini-1.5-flash-latest'로 시도
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e2:
            return f"구글 서버 연결 오류. API 키가 'Gemini API'용인지 확인해주세요. 에러내용: {str(e2)}"
