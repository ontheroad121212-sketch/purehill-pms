import requests
import json

def get_ai_insight(api_key, data_summary):
    # API 키 앞뒤 공백 제거
    api_key = api_key.strip()
    
    # 구글 서버로 직접 연결하는 주소 (v1beta 통로를 피해서 v1으로 접속)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # 보낼 데이터 구성
    payload = {
        "contents": [{
            "parts": [{
                "text": f"당신은 호텔 분석가입니다. 아래 퓨어힐 호텔 데이터를 한국어로 분석하세요: {data_summary}"
            }]
        }]
    }

    try:
        # 구글 서버에 직접 요청
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        # 결과에서 텍스트만 추출
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI 응답 오류: {result.get('error', {}).get('message', '알 수 없는 오류')}"
            
    except Exception as e:
        return f"서버 연결 중 진짜 오류 발생: {str(e)}"
