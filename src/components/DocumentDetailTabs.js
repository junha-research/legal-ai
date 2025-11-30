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
    raw: { ko: "Raw JSON", en: "Raw JSON", vi: "Raw JSON" },
  };

  const t = (k) => labels[k]?.[language] || labels[k]?.ko || k;

  const tabs = [
    { id: "summary", label: t("summary") },
    { id: "risk", label: t("risk") },
    { id: "clauses", label: t("clauses"), badge: counts.clauses },
    { id: "terms", label: t("terms"), badge: counts.terms },
    { id: "raw", label: t("raw") },
  ];

  return (
    <div className="doc-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`doc-tab-item ${
            activeTab === tab.id ? "active" : ""
          }`}
          onClick={() => onChange(tab.id)}
        >
          <span>{tab.label}</span>
          {typeof tab.badge === "number" && (
            <span className="doc-tab-badge">{tab.badge}</span>
          )}
        </button>
      ))}
    </div>
  );
}
