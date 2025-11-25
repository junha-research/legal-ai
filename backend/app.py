import streamlit as st
import requests

st.set_page_config(
    page_title="📄 Legal AI 문서 분석기",
    page_icon="⚖️",
    layout="wide"
)

st.title("📄 Legal AI 문서 분석기")
st.write("이미지 · PDF · Word · HWP 파일을 업로드하면 AI가 분석합니다.")
st.markdown("---")


# ======================================================================================
# Helper — 문서 분석 렌더링
# ======================================================================================

def render_document_result(doc):
    st.success("분석 완료! 아래 결과를 확인하세요.")
    st.markdown("---")

    summary = doc["summary"]
    risk = doc["risk_profile"]

    st.subheader("📌 문서 요약")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("문서 제목", summary.get("title") or "제목 없음")
    with col2:
        st.metric("한 줄 요약", summary.get("one_line_summary", ""))
    with col3:
        st.metric("위험 수준", risk.get("overall_risk_level", "정보 없음"))

    st.write("### 📝 전체 요약")
    st.write(summary.get("overall_summary", ""))

    st.markdown("---")

    colA, colB = st.columns(2)
    with colA:
        st.write("### 📌 핵심 포인트")
        for p in summary.get("key_points", []):
            st.markdown(f"- {p}")

        st.write("### ⚠️ 주요 위험 요소")
        for r in summary.get("main_risks", []):
            st.error(f"- {r}")

    with colB:
        st.write("### 🛡 주요 보호 장치")
        for p in summary.get("main_protections", []):
            st.success(f"- {p}")

        st.write("### 📌 권장 액션")
        for a in summary.get("recommended_actions", []):
            st.warning(f"- {a}")

    st.markdown("---")

    st.subheader("📊 리스크 프로파일")
    score = risk.get("overall_risk_score", 0)
    st.write(f"전체 위험 점수: {score} / 100")
    st.progress(score / 100)

    for key, val in risk.get("risk_dimensions", {}).items():
        st.write(f"{key}: {val}점")
        st.progress(int(val) / 100)

    st.markdown("---")

    st.subheader("📄 조항별 분석")

    for clause in doc.get("clauses", []):
        sid = clause.get("clause_id", "unknown")
        preview = clause.get("summary") or clause.get("raw_text", "")[:40]

        with st.expander(f"📌 {sid} — {preview}"):
            st.write("### 요약")
            st.write(clause.get("summary", ""))

            st.write("### 위험도")
            st.write(f"- 수준: {clause.get('risk_level')}")
            st.write(f"- 점수: {clause.get('risk_score')}")
            st.progress(int(clause.get("risk_score", 0)) / 100)

            st.write("### 원문")
            st.code(clause.get("raw_text", ""))

    st.markdown("---")

    st.subheader("📚 용어 정의")
    terms = doc.get("terms", [])
    if terms:
        st.table([
            {
                "용어": t.get("term"),
                "설명": t.get("korean"),
                "영문": t.get("english"),
                "출처": t.get("source"),
            }
            for t in terms
        ])
    else:
        st.info("용어 없음")

    st.markdown("---")
    st.success("🎉 분석 완료!")


# ======================================================================================
# OCR PREVIEW
# ======================================================================================

uploaded_file = st.file_uploader(
    "분석할 문서를 업로드하세요",
    type=["pdf", "png", "jpg", "jpeg", "docx", "hwp"]
)

if uploaded_file:
    if st.button("📝 OCR / 텍스트 미리보기"):
        res = requests.post(
            "http://127.0.0.1:8000/api/files/extract-text",
            files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        )
        if res.ok:
            st.text_area("OCR 텍스트", res.json().get("preview", ""), height=300)
        else:
            st.error(res.text)

    if st.button("🔍 전체 문서 심층 분석 시작"):
        res = requests.post(
            "http://127.0.0.1:8000/api/files/interpret",
            files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
            data={"language": "ko"},
        )
        if res.ok:
            data = res.json()
            render_document_result(data.get("document", {}))
        else:
            st.error(res.text)

