// src/components/TermCard.js
import React from "react";

export default function TermCard({ term }) {
  return (
    <div className="term-card">
      <div className="term-card-header">
        <div className="term-badge">MOLEG</div>
        <div className="term-title">{term.term}</div>
      </div>
      <div className="term-body">
        <p className="term-korean">{term.korean}</p>
        {term.english && (
          <p className="term-english">
            <span className="term-label">EN</span> {term.english}
          </p>
        )}
      </div>
      <div className="term-footer">
        <span className="term-source">
          출처: {term.source || "MOLEG"}
        </span>
      </div>
    </div>
  );
}
