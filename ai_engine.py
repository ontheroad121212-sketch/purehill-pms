import requests
import json

def get_ai_insight(api_key, data_summary):
    api_key = api_key.strip()
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    headers = {'Content-Type': 'application/json'}
    
    # 1. 먼저 사용 가능한 모델 목록을 가져옵니다.
    list_models_url = f"{base_url}/models?key={api_key}"
    
    try:
        model_res = requests.get(list_models_url)
        models_data = model_res.json()
        
        # 목록 중에서 gemini-1.5-flash나 gemini-pro를 찾습니다.
        available_models = [m['name'] for m in models_data.get('models', []) 
                           if 'generateContent' in m.get('supportedGenerationMethods', [])]
        
        if not available_models:
            return "사용 가능한 AI 모델을 찾을 수 없습니다. API 키 권한을 확인해주세요."

        # 가장 좋은 모델(1.5 flash)을 우선 선택하고, 없으면 목록의 첫 번째를 씁니다.
        target_model = ""
        for m in available_models:
            if 'gemini-1.5-flash' in m:
                target_model = m
                break
        if not target_model:
            target_model = available_models[0]

        # 2. 선택된 모델로 분석 요청을 보냅니다.
        gen_url = f"{base_url}/{target_model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 호텔 전문 분석가입니다. 퓨어힐 호텔의 다음 데이터를 보고 한국어로 친절하고 전문적인 분석 보고서를 작성하세요: {data_summary}"
                }]
            }]
        }

        response = requests.post(gen_url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI 분석 실패: {result.get('error', {}).get('message', '응답 형식 오류')}"
            
    except Exception as e:
        return f"통신 오류: {str(e)}"
