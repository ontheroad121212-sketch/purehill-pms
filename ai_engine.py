import requests
import json

def get_ai_insight(api_key, data_summary):
    api_key = api_key.strip()
    
    # 주소에 모델 이름을 정확하게 'models/gemini-1.5-flash'로 넣었습니다.
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"당신은 호텔 전문 분석가입니다. 다음 퓨어힐 호텔 데이터를 한국어로 분석하고 전략을 제언하세요: {data_summary}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        # 성공적으로 텍스트가 왔을 때
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        # 에러가 났을 때 상세 메시지 출력
        else:
            error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
            return f"AI 응답 오류: {error_msg}"
            
    except Exception as e:
        return f"서버 연결 중 오류 발생: {str(e)}"
