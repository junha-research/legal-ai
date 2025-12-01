// src/pages/DocumentDetailPage.js
import React, { useEffect, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useLanguage } from "../context/LanguageContext";

import DocumentDetailTabs from "../components/DocumentDetailTabs";
import ClauseAccordion from "../components/ClauseAccordion";
import RiskGauge from "../components/RiskGauge";
import TermCard from "../components/TermCard";
import RawJsonViewer from "../components/RawJsonViewer";

import "./DocumentDetailPage.css";

export default function DocumentDetailPage() {
  const { id } = useParams();
  const location = useLocation();
  const { t, formatDate } = useLanguage();

  const [documentResult, setDocumentResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("summary");
  const [isFavorite, setIsFavorite] = useState(false);

  // ==============================
  // 🔥 백엔드 → pseudoDoc 변환 (핵심 수정)
  // ==============================
  useEffect(() => {
    if (documentResult || !id) return;

    let cancelled = false;

    async function loadFromBackend() {
      try {
        setLoading(true);
        setError(null);

        const detailRes = await api.get(`/contracts/${id}`);
        const meta = detailRes.data;

        const clauseRes = await api.get(`/contracts/${id}/clauses`);
        const termRes = await api.get(`/contracts/${id}/terms`);

        // ⭐ 수정된 pseudoDoc (백엔드 응답 구조 기반)
        const pseudoDoc = {
          document_id: String(meta.id),

          meta: {
            language: meta.language || "ko",
            domain_tags: meta.domain_tags ? meta.domain_tags.split(",") : [],
            parties: meta.parties ? meta.parties.split(",") : [],
            governing_law: meta.governing_law || null,
          },

          summary: {
            title: meta.title,
            overall_summary: meta.summary || "",
            one_line_summary: meta.summary || "",

            key_points: meta.key_points ? JSON.parse(meta.key_points) : [],
            main_risks: meta.main_risks ? JSON.parse(meta.main_risks) : [],
            main_protections: meta.main_protections
              ? JSON.parse(meta.main_protections)
              : [],
            recommended_actions: meta.recommended_actions
              ? JSON.parse(meta.recommended_actions)
              : [],
          },

          risk_profile: {
            overall_risk_level: meta.risk_level || "중간",
            overall_risk_score: meta.risk_score ?? 50,
            risk_dimensions: meta.risk_dimensions
              ? JSON.parse(meta.risk_dimensions)
              : {},
            comments: meta.risk_comments || "",
          },

          clauses: (clauseRes.data || []).map((c) => ({
            clause_id: c.clause_id,
            title: c.title,
            raw_text: c.raw_text,
            summary: c.summary,
            risk_level: c.risk_level,
            risk_score: c.risk_score,
            risk_factors: [],
            protections: [],
            red_flags: [],
            action_guides: [],
            key_points: [],
            tags: { domain: [], risk: [], parties: [] },
          })),

          causal_graph: [],

          terms: (termRes.data || []).map((t) => ({
            term: t.term,
            korean: t.korean,
            english: t.english,
            source: t.source || "MOLEG",
          })),

          __meta: {
            created_at: meta.created_at,
          },
        };

        if (!cancelled) {
          setDocumentResult(pseudoDoc);
          setIsFavorite(!!meta.is_favorite);
        }
      } catch (e) {
        console.error(e);
        if (!cancelled) setError(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadFromBackend();
    return () => (cancelled = true);
  }, [id, documentResult, t]);

  // ==============================
  // UI — 로딩/에러 처리
  // ==============================
  if (loading) {
    return (
      <div className="doc-detail-page">
        <div className="doc-detail-card doc-detail-loading">
          {t("detail.loading")}
        </div>
      </div>
    );
  }

  if (!documentResult || error) {
    return (
      <div className="doc-detail-page">
        <div className="doc-detail-card doc-detail-error">
          {t("detail.notFound")}
        </div>
      </div>
    );
  }

  // ==============================
  // 구조 분해
  // ==============================
  const { summary, risk_profile, meta: metaInfo, clauses, terms, __meta } =
    documentResult;

  const createdAt =
    __meta?.created_at || location.state?.created_at || null;

  // ==============================
  // 즐겨찾기
  // ==============================
  const handleToggleFavorite = async () => {
    try {
      const res = await api.post(`/contracts/${id}/favorite`);
      setIsFavorite(res.data.is_favorite);
    } catch (e) {
      console.error(e);
      setIsFavorite((prev) => !prev);
    }
  };

  const handleRename = () => alert(t("detail.rename_desc"));
  const handleExportPdf = () => alert(t("detail.export_desc"));

  // ==============================
  // 페이지 렌더
  // ==============================
  return (
    <div className="doc-detail-page">
      {/* 상단 메타 */}
      <div className="doc-detail-header">
        <div className="doc-detail-title-block">
          <div className="doc-detail-chip-row">
            {metaInfo?.language && (
              <span className="doc-chip">
                {t("detail.language")}: {metaInfo.language.toUpperCase()}
              </span>
            )}
            {metaInfo?.domain_tags?.length > 0 && (
              <span className="doc-chip">
                {t("detail.domain")}: {metaInfo.domain_tags.join(", ")}
              </span>
            )}
            {metaInfo?.parties?.length > 0 && (
              <span className="doc-chip">
                {t("detail.parties")}: {metaInfo.parties.join(", ")}
              </span>
            )}
          </div>

          <h1 className="doc-detail-title">
            {summary?.title || t("docs.no_title")}
          </h1>

          {createdAt && (
            <div className="doc-detail-meta-text">
              {t("detail.createdAt")}: {formatDate(createdAt)}
            </div>
          )}
        </div>

        <div className="doc-detail-actions">
          <button
            className={`doc-btn ghost ${isFavorite ? "favorite" : ""}`}
            onClick={handleToggleFavorite}
          >
            {isFavorite ? "★ " : "☆ "}
            {isFavorite ? t("detail.unfavorite") : t("detail.favorite")}
          </button>

          <button className="doc-btn ghost" onClick={handleRename}>
            ✏️ {t("detail.rename")}
          </button>

          <button className="doc-btn ghost" onClick={handleExportPdf}>
            📄 {t("detail.exportPdf")}
          </button>
        </div>
      </div>

      {/* Summary + Risk */}
      <div className="doc-detail-top-grid">
        <div className="doc-detail-card">
          <div className="doc-card-header">
            <span className="doc-card-title">{t("detail.summary")}</span>
          </div>

          <p className="doc-summary-main">{summary?.overall_summary}</p>

          {summary?.one_line_summary && (
            <p className="doc-summary-one-line">
              “{summary.one_line_summary}”
            </p>
          )}

          <div className="doc-summary-tags-grid">
            {summary?.key_points?.length > 0 && (
              <div className="doc-summary-tag-section">
                <div className="doc-summary-tag-label">
                  {t("detail.key_points")}
                </div>
                <ul>
                  {summary.key_points.map((k, i) => (
                    <li key={i}>{k}</li>
                  ))}
                </ul>
              </div>
            )}

            {summary?.main_risks?.length > 0 && (
              <div className="doc-summary-tag-section">
                <div className="doc-summary-tag-label">
                  {t("detail.main_risks")}
                </div>
                <ul>
                  {summary.main_risks.map((k, i) => (
                    <li key={i}>{k}</li>
                  ))}
                </ul>
              </div>
            )}

            {summary?.recommended_actions?.length > 0 && (
              <div className="doc-summary-tag-section">
                <div className="doc-summary-tag-label">
                  {t("detail.recommended_actions")}
                </div>
                <ul>
                  {summary.recommended_actions.map((k, i) => (
                    <li key={i}>{k}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="doc-detail-card doc-risk-card">
          <div className="doc-card-header">
            <span className="doc-card-title">{t("detail.risk")}</span>
          </div>

          <RiskGauge riskProfile={risk_profile} />

          {risk_profile?.comments && (
            <p className="doc-risk-comment">{risk_profile.comments}</p>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="doc-detail-card doc-detail-tabs-wrapper">
        <DocumentDetailTabs
          activeTab={activeTab}
          onChange={setActiveTab}
          counts={{ clauses: clauses?.length || 0, terms: terms?.length || 0 }}
        />

        <div className="doc-tab-content">
          {activeTab === "summary" && (
            <div className="doc-tab-section">
              <h3>{t("detail.summary")}</h3>
              <p>{summary?.overall_summary}</p>
            </div>
          )}

          {activeTab === "risk" && (
            <div className="doc-tab-section">
              <RiskGauge riskProfile={risk_profile} big />
            </div>
          )}

          {activeTab === "clauses" && (
            <div className="doc-tab-section">
              <ClauseAccordion clauses={clauses || []} />
            </div>
          )}

          {activeTab === "terms" && (
            <div className="doc-tab-section doc-term-grid">
              {(terms || []).map((t, i) => (
                <TermCard key={i} term={t} />
              ))}
            </div>
          )}

          {activeTab === "raw" && (
            <div className="doc-tab-section">
              <RawJsonViewer data={documentResult} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
