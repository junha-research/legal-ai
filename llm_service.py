import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

print("V2")
# --- 1. 환경 변수 및 클라이언트 설정 ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_genai_client():
    """Google GenAI 클라이언트를 생성합니다."""
    if not GEMINI_API_KEY:
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

# --- 2. 통합 해석 함수 (Single Call Strategy) ---

def create_easy_legal_interpretation(original_text: str, term_definitions: dict) -> dict:
    """
    Gemini를 단 한 번 호출하여 모든 작업을 수행합니다.
    1. 여러 개의 복잡한 용어 정의를 한 번에 쉽게 요약
    2. 원본 텍스트를 쉽게 해석
    3. 결과를 구조화된 JSON으로 반환
    """
    client = get_genai_client()
    if not client:
        return {
            "main_interpretation": "API 키가 설정되지 않았습니다.",
            "simplified_terms": {}
        }

    print("Gemini API (Single Call) 서비스 호출 시작...")
    
    # 1. 프롬프트에 넣을 용어 정의 목록 생성
    #    (사전 데이터를 하나의 텍스트 덩어리로 변환)
    terms_context = ""
    if term_definitions:
        for term, data in term_definitions.items():
            terms_context += f"- {term}: {data['korean_original']}\n"
    else:
        terms_context = "(참고할 용어 정의 없음)"

    # 2. 통합 프롬프트 작성 (JSON 출력을 강제함)
    prompt = f"""
    당신은 법률 문서를 초등학생도 이해할 수 있게 설명해주는 친절한 변호사입니다.
    아래 제공된 [원본 텍스트]와 [법률 용어 목록]을 바탕으로 다음 두 가지 작업을 수행해주세요.

    [작업 1] '쉬운 용어 사전' 만들기:
    제공된 [법률 용어 목록]에 있는 각 용어의 뜻을 초등학생도 알 수 있게 '한 문장'으로 아주 쉽게 요약하세요.

    [작업 2] '본문 해석' 하기:
    [원본 텍스트]의 내용을 문단별로 나누어, 위에서 만든 쉬운 용어들을 활용해 아주 쉽고 명확하게 풀어서 설명해주세요.
    핵심 내용을 먼저 말하고 부가 설명을 덧붙이세요.

    --------------------------------------------------------
    [법률 용어 목록 (원본 정의)]:
    {terms_context}

    [원본 텍스트]:
    {original_text}
    --------------------------------------------------------

    [응답 형식 (반드시 이 JSON 형식을 지켜주세요)]:
    {{
        "simplified_terms": {{
            "용어1": "쉬운 요약 1",
            "용어2": "쉬운 요약 2"
        }},
        "main_interpretation": "여기에 본문의 쉬운 해석을 적어주세요. 줄바꿈은 \\n을 사용하세요."
    }}
    """

    try:
        # 3. Gemini API 호출 (JSON 모드 사용)
        response = client.models.generate_content(
            model="gemini-2.0-flash", # 또는 gemini-1.5-pro
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json" # ⭐️ JSON 응답 강제 (가장 중요)
            )
        )
        
        if response.text:
            # 4. JSON 파싱 및 반환
            result_data = json.loads(response.text)
            print("Gemini 응답 및 파싱 완료.")
            
            # 혹시 모를 키 에러 방지를 위한 안전장치
            return {
                "main_interpretation": result_data.get("main_interpretation", "해석 생성 실패"),
                "simplified_terms": result_data.get("simplified_terms", {})
            }
        else:
            return {
                "main_interpretation": "AI가 빈 응답을 반환했습니다.",
                "simplified_terms": {}
            }
            
    except Exception as e:
        print(f"Gemini API 호출 오류: {e}")
        return {
            "main_interpretation": f"오류가 발생했습니다: {str(e)}",
            "simplified_terms": {}
        }