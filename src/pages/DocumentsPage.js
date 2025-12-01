// src/pages/DocumentsPage.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useLanguage } from "../context/LanguageContext";
import "./DocumentsPage.css";

export default function DocumentsPage() {
  const { t, formatDate } = useLanguage();
  const navigate = useNavigate();

  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  // 검색 & 필터
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");

  // 삭제 모달 상태
  const [deleteId, setDeleteId] = useState(null);

  const fetchDocs = () => {
    setLoading(true);
    api
      .get("/contracts/list")
      .then((res) => setDocs(res.data))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const toggleFavorite = async (id) => {
    try {
      await api.post(`/contracts/${id}/favorite`);
      fetchDocs();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteDoc = async () => {
    try {
      await api.delete(`/contracts/${deleteId}/delete`);
      setDeleteId(null);
      fetchDocs();
    } catch (e) {
      console.error(e);
    }
  };

  // 검색 + 필터 적용
  const filteredDocs = docs.filter((d) => {
    const matchSearch =
      d.title?.toLowerCase().includes(search.toLowerCase()) ||
      d.summary?.toLowerCase().includes(search.toLowerCase());

    const matchRisk =
      riskFilter === "all" || String(d.risk_level) === riskFilter;

    return matchSearch && matchRisk;
  });

  return (
    <div className="docs-page">
      <h1 className="docs-title">{t("docs.title")}</h1>
      <p className="docs-sub">{t("docs.subtitle")}</p>

      {/* 검색 + 필터 UI */}
      <div className="docs-controls">
        <input
          className="search-input"
          type="text"
          placeholder={t("docs.search_placeholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select
          className="filter-select"
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
        >
          <option value="all">{t("docs.filter.all")}</option>
          <option value="낮음">{t("docs.filter.low")}</option>
          <option value="중간">{t("docs.filter.mid")}</option>
          <option value="높음">{t("docs.filter.high")}</option>
        </select>
      </div>

      {/* 로딩 / 빈 화면 */}
      {loading ? (
        <div className="docs-loading">{t("docs.loading")}</div>
      ) : filteredDocs.length === 0 ? (
        <div className="docs-empty">{t("docs.empty")}</div>
      ) : (
        <div className="docs-grid">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              className="doc-card"
              onClick={() =>
                navigate(`/documents/${doc.id}`, {
                  state: { document: doc },
                })
              }
            >
              <div className="doc-icon">📄</div>

              <div className="doc-content">
                <div className="doc-title">
                  {doc.title || t("docs.no_title")}
                </div>

                <div className="doc-summary">{doc.summary}</div>

                <div className="doc-info-row">
                  <span className={`badge risk-${doc.risk_level}`}>
                    {doc.risk_level}
                  </span>
                  <span className="badge score">{doc.risk_score}</span>
                </div>

                <div className="doc-date">{formatDate(doc.created_at)}</div>
              </div>

              {/* 즐겨찾기 + 삭제 */}
              <div className="doc-actions" onClick={(e) => e.stopPropagation()}>
                <button
                  className="btn-fav"
                  onClick={() => toggleFavorite(doc.id)}
                >
                  {doc.is_favorite ? "★" : "☆"}
                </button>
                <button
                  className="btn-delete"
                  onClick={() => setDeleteId(doc.id)}
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 삭제 모달 */}
      {deleteId && (
        <div className="modal-bg">
          <div className="modal-box">
            <h3>{t("docs.delete_confirm")}</h3>
            <p style={{ fontSize: 13, color: "#6b7280" }}>
              {t("docs.delete_desc")}
            </p>

            <div className="modal-buttons">
              <button
                className="modal-cancel"
                onClick={() => setDeleteId(null)}
              >
                {t("docs.cancel")}
              </button>

              <button className="modal-delete" onClick={deleteDoc}>
                {t("docs.delete")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
