// src/components/DocumentDetailTabs.js
import React from "react";
import { useLanguage } from "../context/LanguageContext";

export default function DocumentDetailTabs({ activeTab, onChange, counts }) {
  const { language } = useLanguage();

  const labels = {
    summary: { ko: "요약", en: "Summary", vi: "Tóm tắt" },
    risk: { ko: "위험도", en: "Risk", vi: "Rủi ro" },
    clauses: { ko: "조항", en: "Clauses", vi: "Điều khoản" },
    terms: { ko: "용어", en: "Terms", vi: "Thuật ngữ" },
    raw: { ko: "전체 데이터", en: "Raw JSON", vi: "Raw JSON" },
  };

  const t = (key) => labels[key]?.[language] || labels[key]?.ko || key;

  const tabs = [
    { id: "summary", label: t("summary") },
    { id: "risk", label: t("risk") },
    { id: "clauses", label: t("clauses"), badge: counts.clauses },
    { id: "terms", label: t("terms"), badge: counts.terms },
    { id: "raw", label: t("raw") },
  ];

  return (
    <div className="doc-tabs">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            className={`doc-tab-item ${isActive ? "active" : ""}`}
            onClick={() => onChange(tab.id)}
          >
            <span className="doc-tab-label">{tab.label}</span>

            {typeof tab.badge === "number" && (
              <span
                className={`doc-tab-badge ${
                  isActive ? "badge-active" : ""
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
