import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "../api/client";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [items, setItems] = useState([]);

  const handleAsk = async () => {
    if (!question.trim()) return;

    try {
      const res = await api.post("/api/ask", {
        text: question,
        language: "ko",
      });
      setItems((prev) => [res.data, ...prev]);
      setQuestion("");
    } catch (e) {
      alert("질문 실패: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div style={{ paddingBottom: 80 }}>
      <h1 style={{ fontSize: 22, fontWeight: "bold", marginBottom: 12 }}>
        법률 질의응답
      </h1>

      <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 12 }}>
        법률 질문을 입력하면 AI가 요약·리스크·법령까지 정리해드립니다.
      </p>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="예: 프리랜서 계약서에서 지식재산권은 어떻게 확인해야 하나요?"
        style={{
          width: "100%",
          height: 80,
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          padding: 8,
          fontSize: 13,
        }}
      />

      <button
        onClick={handleAsk}
        style={{
          marginTop: 8,
          padding: "8px 14px",
          borderRadius: 999,
          border: "none",
          background: "#2563eb",
          color: "#fff",
          fontSize: 14,
          cursor: "pointer",
        }}
      >
        질문 보내기
      </button>

      <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 20 }}>
        {items.map((c) => (
          <div
            key={c.id}
            style={{
              background: "#fff",
              borderRadius: 14,
              padding: 20,
              border: "1px solid #e5e7eb",
              boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 10 }}>
              Q. {c.question}
            </div>

            <div style={{ fontSize: 14, lineHeight: "1.55", color: "#374151" }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {c.answer}
              </ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
