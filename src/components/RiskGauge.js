// src/components/RiskGauge.js
import React from "react";

const LEVEL_ORDER = ["낮음", "중간", "높음", "치명적"];

function getLevelIndex(level) {
  const idx = LEVEL_ORDER.indexOf(level);
  return idx === -1 ? 1 : idx;
}

export default function RiskGauge({ riskProfile, big = false }) {
  if (!riskProfile) return null;

  const score = riskProfile.overall_risk_score ?? 0;
  const level = riskProfile.overall_risk_level || "중간";

  const idx = getLevelIndex(level);
  const percent = ((idx + 1) / LEVEL_ORDER.length) * 100;

  return (
    <div className={`risk-gauge ${big ? "risk-gauge-big" : ""}`}>
      <div className="risk-gauge-label-row">
        <span className="risk-gauge-level">{level}</span>
        <span className="risk-gauge-score">{score}/100</span>
      </div>
      <div className="risk-gauge-bar">
        <div
          className={`risk-gauge-fill level-${idx}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="risk-gauge-legend">
        {LEVEL_ORDER.map((lv) => (
          <span
            key={lv}
            className={`risk-gauge-legend-item ${
              lv === level ? "active" : ""
            }`}
          >
            {lv}
          </span>
        ))}
      </div>
      {riskProfile.risk_dimensions &&
        Object.keys(riskProfile.risk_dimensions).length > 0 && (
          <div className="risk-gauge-dimensions">
            {Object.entries(riskProfile.risk_dimensions).map(
              ([k, v]) => (
                <div key={k} className="risk-dimension-item">
                  <span className="risk-dimension-name">{k}</span>
                  <span className="risk-dimension-score">{v}</span>
                </div>
              )
            )}
          </div>
        )}
    </div>
  );
}
