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
    clauses?.[0]?.clause_id || null
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
              onClick={() => setOpenId(isOpen ? null : c.clause_id)}
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
                {/* 원문 */}
                <div className="doc-accordion-sub">
                  <div className="doc-accordion-sub-title">원문</div>
                  <pre className="doc-raw-text">{c.raw_text}</pre>
                </div>

                {/* 요약 */}
                <div className="doc-accordion-sub">
                  <div className="doc-accordion-sub-title">요약</div>
                  <p>{c.summary || "요약 정보 없음"}</p>
                </div>

                {/* 핵심 포인트 */}
                {c.key_points?.length > 0 && (
                  <div className="doc-accordion-sub">
                    <div className="doc-accordion-sub-title">✨ Key Points</div>
                    <ul>
                      {c.key_points.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 위험 요소 */}
                {c.risk_factors?.length > 0 && (
                  <div className="doc-accordion-sub">
                    <div className="doc-accordion-sub-title">⚠️ 위험 요소</div>
                    <ul>
                      {c.risk_factors.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 레드 플래그 */}
                {c.red_flags?.length > 0 && (
                  <div className="doc-accordion-sub red">
                    <div className="doc-accordion-sub-title">🚨 레드 플래그</div>
                    <ul>
                      {c.red_flags.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 보호 요소 */}
                {c.protections?.length > 0 && (
                  <div className="doc-accordion-sub green">
                    <div className="doc-accordion-sub-title">🛡 보호 요소</div>
                    <ul>
                      {c.protections.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 액션 가이드 */}
                {c.action_guides?.length > 0 && (
                  <div className="doc-accordion-sub blue">
                    <div className="doc-accordion-sub-title">🚀 권장 행동</div>
                    <ul>
                      {c.action_guides.map((p, idx) => (
                        <li key={idx}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 태그 */}
                {c.tags && (c.tags.domain?.length || c.tags.risk?.length) > 0 && (
                  <div className="doc-accordion-sub">
                    <div className="doc-accordion-sub-title">🏷 태그</div>
                    <div className="tag-row">
                      {c.tags.domain?.map((t, i) => (
                        <span key={i} className="tag blue">{t}</span>
                      ))}
                      {c.tags.risk?.map((t, i) => (
                        <span key={i} className="tag red">{t}</span>
                      ))}
                      {c.tags.parties?.map((t, i) => (
                        <span key={i} className="tag green">{t}</span>
                      ))}
                    </div>
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
