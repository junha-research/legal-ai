import streamlit as st
import aiohttp
import asyncio
import re
import os
import json
from konlpy.tag import Okt
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor # ⭐️ 스레드 실행을 위해 추가
print("DEBUG: legal_dict.py 모듈 로딩 시작...") # ⭐️ 모듈 로드 확인용 로그
load_dotenv()
# --- 1. 전역 변수 설정 ---
# ⭐️ .env 파일을 사용하지 않는 대신, Streamlit의 secrets.toml이나
#    환경 변수를 통해 API 키를 설정하는 것을 권장합니다.
#    st.secrets["MOLEG_API_KEY"] 또는 os.environ.get("MOLEG_API_KEY")
#    여기서는 하드코딩된 예시를 사용합니다. (보안상 좋지 않음)
API_KEY = os.getenv("MOLEG_API_KEY") # 👈 본인의 API 키로 변경 (또는 st.secrets["MOLEG_API_KEY"] 사용)
# --- 2. Okt 캐싱 (Streamlit 무관하게 동작하도록 수정) ---
_okt_instance = None

def get_okt_tagger():
    global _okt_instance
    if _okt_instance is None:
        try:
            _okt_instance = Okt()
        except Exception as e:
            print(f"❌ Okt 로딩 실패: {e}")
            return None
    return _okt_instance

# Streamlit 캐싱 래퍼 (앱 실행 시 사용)
if hasattr(st, "cache_resource"):
    get_okt_tagger_cached = st.cache_resource(get_okt_tagger)
else:
    get_okt_tagger_cached = get_okt_tagger


# --- 3. 비동기 API 호출 함수 (핵심 로직) ---
async def fetch_term_definition(session, term):
    """단일 용어에 대해 API를 비동기로 호출하고 파싱합니다."""
    API_URL = f"http://www.law.go.kr/DRF/lawService.do?OC={API_KEY}&target=lstrm&query={term}&type=JSON"

    
    try:
        async with session.get(API_URL, timeout=5) as response:
            if response.status != 200:
                print(f"⚠️ [{term}] API 상태 코드 오류: {response.status}")
                return term, None

            try:
                # content_type=None 허용 (API가 text/html로 줄 때가 있음)
                data = await response.json(content_type=None)
            except Exception as e:
                print(f"⚠️ [{term}] JSON 변환 실패: {e}")
                # 텍스트로 뭐가 왔는지 확인
                text_response = await response.text()
                print(f"   응답 내용(일부): {text_response[:100]}")
                return term, None
            
            # --- 데이터 파싱 로직 ---
            service = data.get("LsTrmService")
            if not service:
                # 검색 결과 없음 (정상적인 경우)
                return term, None

            # 데이터 가져오기 (없으면 빈 리스트/문자열)
            defs = service.get("법령용어정의")
            codes = service.get("법령용어코드명")
            examples = service.get("용례")

            if not codes:
                return term, None

            # ⭐️ [중요] 타입 정규화 (리스트로 통일)
            # API가 결과가 1개면 문자열(str), 2개 이상이면 리스트(list)로 줌
            defs = [defs] if isinstance(defs, str) else (defs or [])
            codes = [codes] if isinstance(codes, str) else (codes or [])
            examples = [examples] if isinstance(examples, str) else (examples or [])

            # ⭐️ 개수 맞추기 (zip을 위해)
            # 가끔 '정의'가 없거나 개수가 안 맞을 수 있음. 가장 긴 길이에 맞춤
            max_len = len(codes)
            
            # (부족한 부분 채우기)
            while len(defs) < max_len: defs.append("")
            while len(examples) < max_len: examples.append("")

            korean_def, english_def = None, None

            for i in range(max_len):
                code = codes[i]
                definition = defs[i]
                example = examples[i]
                
                if code == "법령한영사전":
                    english_def = definition.strip()
                elif not korean_def:
                    # 한국어 정의 찾기 (정의 우선, 없으면 용례)
                    candidate = definition.strip() or example.strip()
                    if candidate:
                        korean_def = candidate

            if korean_def:
                # 전처리 (HTML, 영어 등 제거)
                korean_def = re.sub(r'<[^>]+>|&[a-zA-Z0-9#]+;|[a-zA-Z]|\([一-龥\s]+\)', '', korean_def)
                korean_def = ' '.join(korean_def.split())
                
                return term, {"korean_original": korean_def, "english": english_def or "N/A"}

    except Exception as e:
        print(f"❌ [{term}] 처리 중 예기치 못한 오류: {e}")

    return term, None

# --- 4. 비동기 배치 처리기 ---
async def fetch_all_terms(terms):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_term_definition(session, term) for term in terms]
        return await asyncio.gather(*tasks)
# ⭐️ 헬퍼 함수: 비동기 함수를 별도 스레드에서 안전하게 실행
def run_async_in_thread(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()
# --- 5. 메인 함수 (동기 래퍼) ---
def extract_and_define_terms(text):
    okt = get_okt_tagger_cached()
    if not okt: return {}

    nouns = okt.nouns(text)
    
    stopwords = {
        "제", "조", "항", "호", "것", "수", "때", "년", "월", "일", "시", "분", "초", "개", "원", "명",
        "부분", "문제", "상황", "방식", "이유", "방법", "관련", "사실", "정의", "절차", 
        "이상", "이하", "다음", "해당", "대해", "위해", "대한", "그", "이", "및", "등",
        "우리", "저희", "당신", "하나", "둘", "셋", "첫째", "둘째", "기타"
    }
    
    target_terms = sorted(list(set(n for n in nouns if len(n) > 1 and n not in stopwords)))
    
    if not target_terms:
        return {}

    # Streamlit 환경 체크 (이벤트 루프 충돌 방지)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 이미 실행 중인 루프가 있다면 그 안에서 실행, 아니면 run_until_complete
    if loop.is_running():
        # Streamlit 등 이미 루프가 도는 환경
        future = asyncio.ensure_future(fetch_all_terms(target_terms))
        # 동기 함수에서 비동기 결과를 기다리는 것은 복잡하므로,
        # 여기서는 간단히 새 루프를 만드는 방식 대신 기존 루프 활용 시도
        # (Streamlit은 보통 별도 스레드라 run_until_complete가 안전)
        pass 
    
    # 안전한 새 루프 생성 및 실행
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    results = new_loop.run_until_complete(fetch_all_terms(target_terms))
    new_loop.close()

    return {term: data for term, data in results if data}

# ==========================================
# 🧪 테스트 코드 (이 파일을 직접 실행할 때만 작동)
# ==========================================
if __name__ == "__main__":
    print("\n🔍 [자가 진단 모드] legal_dict.py 테스트 시작...\n")
    
    # 1. API 키 확인
    print(f"1. API Key 확인: {API_KEY}***")
    
    # 2. 테스트용 텍스트
    test_text = "근로자가 임금을 체불당했을 때 고용노동부에 신고할 수 있다."
    print(f"2. 분석 텍스트: {test_text}")
    
    # 3. 실행
    print("3. 함수 실행 중...")
    result = extract_and_define_terms(test_text)
    
    print("\n4. 결과 확인:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if not result:
        print("\n⚠️ 결과가 비어있습니다! 다음을 확인하세요:")
        print("   - API 키가 올바른지")
        print("   - 인터넷 연결 상태")
        print("   - '임금', '근로자', '체불' 등의 검색 결과가 실제 API에서 나오는지")