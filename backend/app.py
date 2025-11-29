import streamlit as st
import requests

BASE = "http://127.0.0.1:8000"

st.title("📌 Legal AI Backend Test Dashboard")
st.write("백엔드 모든 기능을 하나의 화면에서 테스트할 수 있습니다.")

st.markdown("---")

# ============================
# 1) 계약서 분석
# ============================
st.header("📘 1. 계약서 분석 테스트 (/contracts/analyze)")

text_input = st.text_area("계약서 전문 입력", height=200)
filename = st.text_input("파일 제목", "uploaded.txt")

if st.button("📄 계약서 분석 실행"):
    res = requests.post(
        f"{BASE}/contracts/analyze",
        json={"text": text_input, "filename": filename, "language": "ko"}
    )
    st.write(res.json())

st.markdown("---")

# ============================
# 2) 문서 리스트 조회
# ============================
st.header("📚 2. 문서 리스트 (/contracts/list)")

if st.button("📂 문서 리스트 가져오기"):
    res = requests.get(f"{BASE}/contracts/list")
    docs = res.json()
    st.json(docs)

    if docs:
        doc_ids = [d["id"] for d in docs]
        st.session_state["doc_ids"] = doc_ids


st.markdown("---")

# ============================
# 3) 문서 상세 조회
# ============================
st.header("📄 3. 문서 상세조회 (/contracts/{id})")

doc_id = st.number_input("문서 ID", min_value=1)

if st.button("🔍 문서 상세 보기"):
    res = requests.get(f"{BASE}/contracts/{doc_id}")
    st.json(res.json())

st.markdown("---")

# ============================
# 4) 조항 조회
# ============================
st.header("📑 4. 조항 조회 (/contracts/{id}/clauses)")

if st.button("📌 조항 보기"):
    res = requests.get(f"{BASE}/contracts/{doc_id}/clauses")
    st.json(res.json())

st.markdown("---")

# ============================
# 5) 용어 조회
# ============================
st.header("📘 5. 용어 조회 (/contracts/{id}/terms)")

if st.button("📌 용어 보기"):
    res = requests.get(f"{BASE}/contracts/{doc_id}/terms")
    st.json(res.json())

st.markdown("---")

# ============================
# 6) Chat: 질의응답
# ============================
st.header("💬 6. 법률 질의응답 (/legal/ask)")

ask_text = st.text_input("질문 입력")

if st.button("🤖 질문하기"):
    res = requests.post(f"{BASE}/legal/ask", json={"text": ask_text, "language": "ko"})
    st.json(res.json())

st.markdown("---")

# ============================
# 7) 대화 히스토리
# ============================
st.header("📝 7. 최근 대화 히스토리 (/legal/history)")

if st.button("📜 히스토리 조회"):
    res = requests.get(f"{BASE}/legal/history")
    st.json(res.json())

st.markdown("---")

# ============================
# 8) 북마크 기능
# ============================
st.header("⭐ 8. 북마크 기능 (toggle / list)")

bookmark_conv_id = st.number_input("대화 ID", min_value=1, key="bm_id")

if st.button("⭐ 북마크 토글"):
    res = requests.post(f"{BASE}/legal/toggle-bookmark", json={"conversation_id": bookmark_conv_id})
    st.json(res.json())

if st.button("📌 북마크 리스트"):
    res = requests.get(f"{BASE}/legal/bookmarks")
    st.json(res.json())

st.markdown("---")

# ============================
# 9) 공유 링크
# ============================
st.header("🔗 9. 공유 링크 생성 (/legal/create-share-link)")

share_conv_id = st.number_input("공유할 대화 ID", min_value=1, key="sl_id")

if st.button("🔗 링크 생성"):
    res = requests.post(f"{BASE}/legal/create-share-link", json={"conversation_id": share_conv_id})
    st.json(res.json())

st.write("---")
