# Legal-AI — 법률 문서 분석 · 법령/판례 Dynamic RAG 챗봇

> **3줄 요약**
> 1. 계약서 분석 + 법률 질의응답을 제공하는 한림대 캡스톤 팀 프로젝트입니다 (FastAPI + React + Streamlit RAG 데모).
> 2. 방대한 법령 전체를 미리 인덱싱하는 대신, 질문마다 필요한 법령만 국가법령정보 API로 가져와 **실시간(in-memory) 벡터화하는 dynamic RAG**를 구현했습니다.
> 3. 판례는 사전 구축한 FAISS DB에서 검색해 법령과 함께 답변 근거로 제시하고, DeepEval(Faithfulness/Relevancy)로 환각 여부를 평가합니다.

## Problem (문제)

대한민국의 현행 법령은 5,000건이 넘고 판례는 수십만 건입니다. 이를 전부 임베딩해 벡터 DB로 유지하는 것은 저장 비용도 크지만, **법령이 수시로 개정되므로 인덱스가 금방 낡는다**는 문제가 있습니다. 반대로 LLM에게 그냥 물어보면 조문을 지어내는 환각이 발생합니다. "항상 최신 법령을 근거로, 환각 없이" 답하는 구조가 필요했습니다.

## Approach (해결 방안)

- **Dynamic RAG (법령)**: 한 번에 모든 법률을 불러올 수 없으므로, ① LLM(gemini-2.5-flash-lite)이 질문에서 대상 법령명을 추출하고("알바" → 근로기준법), ② 국가법령정보센터 API로 해당 법령 XML 전문을 **질의 시점에** 가져와 조문 단위로 파싱한 뒤, ③ ko-sbert-nli 임베딩으로 **in-memory FAISS 인덱스를 즉석 생성**해 질문과 의미적으로 가장 유사한 조항을 찾습니다. 항상 최신 조문이 근거가 되고, 거대한 사전 인덱스를 유지할 필요가 없습니다.
- **Static RAG (판례)**: 판례는 개정되지 않으므로 공개 판례 데이터셋(korean_law_open_data_precedents)을 사건명·판시사항·판결요지 구조로 정리해 FAISS DB를 사전 구축했습니다 (`build_precedent_db.py`).
- **하이브리드 답변 생성**: 검색된 법령 조항 + 유사 판례를 함께 프롬프트에 넣고, "① 법령 원칙 → ② 판례의 실제 적용·예외 → ③ 보충 설명" 순서로 답하도록 답변 구조를 강제했습니다.
- **환각 평가**: DeepEval의 Faithfulness(답변이 검색 문서에 근거하는가)·Answer Relevancy 지표를 Gemini 기반 evaluator로 측정하는 파이프라인을 붙였습니다.
- **서비스 레이어**: FastAPI 백엔드(계약서 업로드→OCR/텍스트 추출→조항별 위험도 분석→PostgreSQL 저장) + React 프론트(다국어 ko/en/vi) + Streamlit 데모(4개 탭: 쉬운 법률 해석 / 법령 상담 / 판례 상담 / 하이브리드 상담)로 구성했습니다.

## Results (결과)

| 항목 | 값 |
|---|---|
| 법령 검색 | 질의 시점 API 조회 + 조문 단위 실시간 FAISS (인덱스 상시 최신) |
| 판례 DB | 공개 판례 데이터셋 기반 FAISS 사전 구축 |
| 임베딩 | jhgan/ko-sbert-nli (한국어 특화) |
| 답변 평가 | DeepEval Faithfulness / Answer Relevancy 파이프라인 구축 |
| 정량 평가 점수 (테스트셋 기준) | 측정 예정 |

## What I learned / Limitations

- **배운 것**: RAG의 품질은 모델보다 "무엇을 근거로 넣느냐"가 좌우한다는 것. 도메인(법률)의 특성 — 법령은 개정되고 판례는 불변 — 에 따라 dynamic/static 검색 전략을 나누는 설계를 팀원들과 논의하며 배웠습니다.
- **한계 1**: 법령명 추출이 틀리면(예: 복수 법령에 걸친 질문) 검색 전체가 어긋납니다. 다중 법령 검색과 재질의(fallback) 로직이 필요합니다.
- **한계 2**: 실시간 벡터화는 조문이 많은 법령(상위 100개 조문으로 제한)에서 질의당 수 초의 지연이 있습니다. 자주 묻는 법령의 인덱스 캐싱이 다음 개선입니다.
- **한계 3**: DeepEval 평가를 파이프라인으로 붙였지만 고정 테스트셋 기반 정량 리포트까지는 만들지 못했습니다.

## Quick start

```bash
# RAG 데모 (Streamlit)
pip install -r requirements.txt
python build_precedent_db.py     # 판례 FAISS DB 구축 (최초 1회)
streamlit run app.py             # .env에 GEMINI_API_KEY, MOLEG_API_KEY 필요

# 서비스 (FastAPI + React)
cd backend && uvicorn app.main:app --reload
cd frontend && npm install && npm start
```

## 파일 구조

```
app.py                  # Streamlit 데모 (4개 탭)
integrated_rag.py       # 법령+판례 하이브리드 RAG + DeepEval 평가
legal_search.py         # dynamic RAG: 법령 API 조회 → 조문 파싱 → 실시간 FAISS 검색
precedent_rag.py        # static RAG: 사전 구축 판례 FAISS 검색
build_precedent_db.py   # 판례 벡터 DB 구축 스크립트
legal_dict.py           # 법제처 API 기반 법률 용어 사전
llm_service.py          # Gemini 호출: 법령명 추출, 답변 생성, 쉬운 해석
backend/                # FastAPI: 계약서 분석·저장 API (PostgreSQL)
frontend/               # React: 문서함·상세 분석·다국어 UI
```

## License

MIT
