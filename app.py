from dotenv import load_dotenv
import streamlit as st
from legal_dict import extract_and_define_terms
from llm_service import create_easy_legal_interpretation

# .env 파일의 변수를 로드합니다
load_dotenv()

st.set_page_config(page_title="⚖️ 쉬운 법률 해석 생성기", page_icon="⚖️", layout="wide")

st.title("쉬운 법률 해석 생성기")
st.write("어려운 법률 텍스트(계약서, 판례 등)를 입력하면 AI가 알기 쉽게 풀어서 설명해 드립니다.")
st.markdown("---")


# 예시 텍스트
sample_text = "제7조 (계약의 해제)\n① 매도인 또는 매수인이 본 계약상의 채무불이행을 하였을 경우, 그 상대방은 서면으로 이행을 최고하고 계약을 해제할 수 있다.\n② 천재지변 기타 불가항력의 사유로 계약 이행이 불가능하게 된 때에는 본 계약은 자동 해제된 것으로 본다."

# 사용자 입력
original_text = st.text_area("여기에 법률 텍스트를 입력하세요:", value=sample_text, height=200)

if st.button("해석 생성하기", type="primary"):
    if not original_text:
        st.warning("해석할 법률 텍스트를 입력해주세요.")
    else:
        with st.spinner("1단계: 법률 용어 분석... (법제처 API 호출 중)"):
            # 1. 법률 용어 추출 및 원본 정의
            term_definitions = extract_and_define_terms(original_text)

        with st.spinner("2단계: AI가 용어 정의를 쉽게 풀고, 본문을 해석 중입니다... (Gemini 호출 중)"):
            # 2. LLM을 통한 2단계 해석 생성
            llm_result = create_easy_legal_interpretation(original_text, term_definitions)
            
            # 반환된 딕셔너리에서 값 분리
            easy_interpretation = llm_result.get("main_interpretation", "해석을 생성하지 못했습니다.")
            simplified_terms = llm_result.get("simplified_terms", {})

            st.markdown("---")
            st.subheader("🔍 AI 법률 해석 결과")

            # 3. 본문 해석 결과 출력
            st.success("해석이 완료되었습니다!")
            
            # ⭐️ [수정됨] st.markdown -> st.text_area로 변경
            # 깔끔한 텍스트 상자에 결과를 보여주며, 내용이 길면 스크롤됩니다.
            st.text_area("상세 해석 내용", value=easy_interpretation, height=400)

            # 4. 참고한 법률 용어 (Expander)
            if term_definitions:
                st.subheader(" ") # 공백 추가
                with st.expander("AI가 참고한 법률 용어 자세히 보기"):
                    
                    for term, data in term_definitions.items():
                        
                        st.markdown(f"#### {term}")
                        
                        # 4-1. LLM이 생성한 '쉬운 정의'
                        easy_def = simplified_terms.get(term, "쉬운 해석을 찾을 수 없습니다.")
                        st.info(f"**쉬운 정의:** {easy_def}")
                        
                        # 4-3. '영어 정의'
                        if data['english'] != "N/A":
                            st.text(f"영어 정의: {data['english']}")
                        
                        st.divider() # 각 용어 사이에 구분선