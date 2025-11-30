// src/components/ClauseAccordion.js
import React, { useState } from "react";

function riskColor(level) {
  switch (level) {
    case "낮음":
      return "#15803d";
    case "중간":
      return "#d97706";
    case "높음":
      return "#b91c1c";
    case "치명적":
      return "#7f1d1d";
    default:
      return "#6b7280";
  }
}

export default function ClauseAccordion({ clauses }) {
  const [openId, setOpenId] = useState(
    clauses && clauses[0] ? clauses[0].clause_id : null
  );

  if (!clauses || clauses.length === 0) {
    return <div className="doc-empty">조항 정보가 없습니다.</div>;
  }

  return (
    <div className="doc-accordion">
      {clauses.map((c) => {
        const isOpen = openId === c.clause_id;
        return (
          <div key={c.clause_id} className="doc-accordion-item">
            <button
              className="doc-accordion-header"
              onClick={() =>
                setOpenId(isOpen ? null : c.clause_id)
              }
            >
              <div className="doc-accordion-title-wrap">
                <span className="doc-accordion-id">{c.clause_id}</span>
                <span className="doc-accordion-title">
                  {c.title || "제목 없음"}
                </span>
              </div>
              <div className="doc-accordion-meta">
                <span
                  className="doc-accordion-risk"
                  style={{ borderColor: riskColor(c.risk_level) }}
                >
                  <span
                    className="doc-accordion-risk-dot"
                    style={{ backgroundColor: riskColor(c.risk_level) }}
                  />
                  {c.risk_level} / {c.risk_score}
                </span>
                <span className="doc-accordion-chevron">
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>
            </button>
            {isOpen && (
              <div className="doc-accordion-body">
                <p className="doc-accordion-summary">
                  {c.summary || "요약 없음"}
                </p>

                {c.key_points && c.key_points.length > 0 && (
                  <div className="doc-accordion-sub">
                    <div className="doc-accordion-sub-title">
                      Key points
                    </div>
                    <ul>
                      {c.key_points.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {c.action_guides && c.action_guides.length > 0 && (
                  <div className="doc-accordion-sub">
                    <div className="doc-accordion-sub-title">
                      Action guides
                    </div>
                    <ul>
                      {c.action_guides.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
