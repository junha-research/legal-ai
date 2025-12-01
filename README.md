# ⚖️ Legal-AI — Contract & Legal Document Analyzer  
AI 기반 계약서 분석 · 문서 저장 · 법률 질의응답 서비스

---

## ✨ Overview
Legal-AI는 **계약서·법률 문서를 업로드하면 AI가 자동으로 핵심 요약 · 위험도 분석 · 당사자 · 법령 정보 · 주요 조항**을 정리해주는 서비스입니다.  
또한 **분석 결과를 문서함에 저장**해 다시 들어가 확인할 수 있고,  
**법률 질문을 입력하면 AI가 법령·리스크·핵심 포인트를 알려주는 질의응답 기능**도 포함합니다.

---

## Features

### 1. 계약서 자동 분석 (Analyze)
- PDF / DOCX / TXT / 이미지 업로드
- 텍스트 자동 추출
- AI 기반 분석:
  - 핵심 요약
  - 위험도 점수 / 레벨
  - 주요 조항 분석
  - 핵심 키포인트
  - 추천 행동 조치
  - 관련 법령
- 분석 결과를 즉시 확인 가능
- "상세 분석 보기" 버튼을 통해 전체 분석 화면 이동

---

### 📁 2. 저장된 문서함 (Documents)
- AI 분석 결과가 자동으로 저장
- 즐겨찾기 기능(★)
- 제목·요약·위험도·날짜 표시
- 클릭 시 상세 분석 페이지로 이동
- 검색 / 필터 (추가 예정)

---

### 3. 문서 상세 페이지 (Document Detail)
각 문서의 모든 분석 내용을 구조적으로 확인 가능:

- 문서 메타 정보  
  - 언어  
  - 도메인  
  - 당사자  
  - 생성 날짜  
- 전체 요약 / 한줄 요약  
- 위험도 분석 Gauge  
- 조항별 분석 Accordion  
- 용어 정의  
- RAW JSON 보기 (디버깅용)  
- 즐겨찾기 / PDF 내보내기 / 이름 변경

---

### 4. 법률 질의응답 (Legal Q&A)
- 사용자가 질문 입력 → AI가 응답  
- 법령 요약, 위험 요소, 핵심 포인트 자동 생성  
- ReactMarkdown 으로 마크다운 렌더링  
- 한국어 / 영어 / 베트남어 다국어 지원  
- "분석 중…" 애니메이션 표시

---

## Multi-language Support
- Korean (ko)  
- English (en)  
- Vietnamese (vi)

React Context + i18n 구조로 전체 UI 번역 가능.

---

## Tech Stack

### Frontend
- React (CRA)
- React Router
- ReactMarkdown + remark-gfm
- Firebase Auth 준비 중
- i18n 다국어 지원
- CSS 커스텀 UI

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- LLM 기반 계약서 분석 엔진
- LangChain 기반 처리
- 파일 업로드(OCR 포함) API
- 문서 저장 / 조항 / 용어 정의 API

---

## 🚀 How to Run (로컬 실행)

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```
### Backend
```
cd legal-ai-frontend
npm install
npm start
```

## Folder Structure

```bash
frontend/
 ├── src/
 │    ├── api/
 │    ├── auth/
 │    ├── components/
 │    ├── context/
 │    ├── i18n/
 │    ├── pages/
 │    └── utils/
 └── public/
```