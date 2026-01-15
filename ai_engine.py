import requests
import json

def get_ai_insight(api_key, data_summary):
    api_key = api_key.strip()
    
    # 404 에러를 피하기 위해 가장 범용적인 gemini-pro 주소를 사용합니다.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"당신은 호텔 전문 분석가입니다. 다음 퓨어힐 호텔의 데이터를 한국어로 분석하고 전략을 제언하세요: {data_summary}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        # 성공 시 응답 구조가 달라질 수 있어 안전하게 추출합니다.
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            # 실패 시 에러 원인을 더 자세히 출력합니다.
            error_details = result.get('error', {}).get('message', '알 수 없는 서버 오류')
            return f"AI 분석 실패: {error_details}"
            
    except Exception as e:
        return f"통신 오류 발생: {str(e)}"
