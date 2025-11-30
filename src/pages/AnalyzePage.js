// src/pages/AnalyzePage.js
import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useLanguage } from "../context/LanguageContext";
import "./AnalyzePage.css";

export default function AnalyzePage() {
  const { t, language } = useLanguage();

  const [file, setFile] = useState(null);
  const [fileURL, setFileURL] = useState(null);
  const [preview, setPreview] = useState("");
  const [docResult, setDocResult] = useState(null);
  const [step, setStep] = useState("idle");
  const [dragOver, setDragOver] = useState(false);

  const navigate = useNavigate();

  // ------------------------------------------------------------------
  // 파일 선택 처리 (useCallback 적용)
  // ------------------------------------------------------------------
  const handleFileSelect = useCallback(
    async (f) => {
      if (!f) return;

      setFile(f);
      setFileURL(URL.createObjectURL(f));
      setPreview("");
      setDocResult(null);

      const form = new FormData();
      form.append("file", f);

      try {
        setStep("extracting");
        const res = await api.post("/api/files/extract-text", form);
        setPreview(res.data.preview);
        setStep("idle");
      } catch (e) {
        alert(
          t("analyze.error_extract") +
            ": " +
            (e.response?.data?.detail || e.message)
        );
        setStep("idle");
      }
    },
    [t] // ★ 필요한 deps 추가
  );

  const handleInputChange = (e) => handleFileSelect(e.target.files[0]);

  // ------------------------------------------------------------------
  // DnD
  // ------------------------------------------------------------------
  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      handleFileSelect(e.dataTransfer.files[0]);
    },
    [handleFileSelect] // ★ 경고 해결
  );

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  // ------------------------------------------------------------------
  // 분석 실행
  // ------------------------------------------------------------------
  const handleAnalyze = async () => {
    if (!file) return alert(t("analyze.alert_no_file"));

    const form = new FormData();
    form.append("file", file);
    form.append("language", language || "ko");

    try {
      setStep("analyzing");
      const res = await api.post("/api/files/full-interpret", form);
      setDocResult(res.data.document);
      setStep("done");
    } catch (e) {
      alert(
        t("analyze.error_analyze") +
          ": " +
          (e.response?.data?.detail || e.message)
      );
      setStep("idle");
    }
  };

  // 상세보기 이동
  const handleOpenDetail = () => {
    if (!docResult?.document_id) return;
    navigate(`/documents/${docResult.document_id}`, {
      state: { document: docResult },
    });
  };

  // 파일 초기화
  const resetFile = () => {
    setFile(null);
    setFileURL(null);
    setPreview("");
    setDocResult(null);
    setStep("idle");
  };

  // 파일 타입 판별
  const ext = file?.name?.split(".").pop().toLowerCase();
  const isImage = ["png", "jpg", "jpeg"].includes(ext);
  const isPDF = ext === "pdf";
  const isText = ext === "txt";
  const isDocx = ext === "docx";

  const progressValue =
    step === "idle"
      ? 0
      : step === "extracting"
      ? 33
      : step === "analyzing"
      ? 66
      : 100;

  // ------------------------------------------------------------------
  // UI
  // ------------------------------------------------------------------
  return (
    <div className="analyze-page">
      <div className="analyze-header">
        <h1>{t("analyze.title")}</h1>
        <p>{t("analyze.subtitle")}</p>
      </div>

      <div className="analyze-grid">
        {/* ---------------------------------- 왼쪽: 업로드 영역 ---------------------------------- */}
        <div className="analyze-card">
          {!file && (
            <div
              className={`dropzone ${dragOver ? "over" : ""}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                type="file"
                id="file-input"
                onChange={handleInputChange}
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
              />
              <label htmlFor="file-input" className="dropzone-label">
                <span className="dropzone-icon">📂</span>
                <span className="dropzone-title">
                  {t("analyze.drop.title")}
                </span>
                <span className="dropzone-sub">
                  {t("analyze.drop.sub")}
                </span>
              </label>
            </div>
          )}

          {file && (
            <>
              <div className="file-info">
                <div className="file-name">
                  <b>{file.name}</b>
                </div>
                <button className="reset-btn" onClick={resetFile}>
                  {t("analyze.change_file")}
                </button>
              </div>

              <div className="preview-box big-preview">
                {isImage && (
                  <img
                    src={fileURL}
                    className="img-preview-large"
                    alt="preview"
                  />
                )}
                {isPDF && (
                  <embed
                    src={fileURL}
                    type="application/pdf"
                    className="pdf-preview-large"
                  />
                )}
                {(isText || isDocx) && (
                  <textarea
                    className="preview-textarea large-textarea"
                    readOnly
                    value={preview}
                  />
                )}
              </div>

              <button className="analyze-btn" onClick={handleAnalyze}>
                {step === "analyzing"
                  ? t("analyze.button.analyzing")
                  : t("analyze.button.default")}
              </button>

              <div className="progress-wrapper">
                <div className="progress-label">
                  {step === "idle" && t("analyze.progress.idle")}
                  {step === "extracting" &&
                    t("analyze.progress.extracting")}
                  {step === "analyzing" &&
                    t("analyze.progress.analyzing")}
                  {step === "done" && t("analyze.progress.done")}
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${progressValue}%` }}
                  />
                </div>
              </div>
            </>
          )}
        </div>

        {/* 오른쪽 패널 */}
        <div className="analyze-card premium-panel">
          <div className="panel-title">
            <span className="emoji">🤖</span> {t("analyze.panel.title")}
          </div>

          {!docResult && (
            <p className="result-placeholder">
              {t("analyze.panel.placeholder")}
            </p>
          )}

          {docResult && (
            <div className="premium-cards">
              <div className="glass-card">
                <h3>
                  <span className="emoji">📌</span>{" "}
                  {t("analyze.panel.doc_info")}
                </h3>

                <div className="tag-row">
                  <span className="tag blue">
                    {t("analyze.panel.language")}
                  </span>
                  <span>{docResult.meta?.language}</span>
                </div>

                <div className="tag-row">
                  <span className="tag purple">
                    {t("analyze.panel.domain")}
                  </span>
                  <span>{docResult.meta?.domain_tags?.join(", ")}</span>
                </div>

                <div className="tag-row">
                  <span className="tag green">
                    {t("analyze.panel.parties")}
                  </span>
                  <span>{docResult.meta?.parties?.join(", ")}</span>
                </div>

                <div className="tag-row">
                  <span className="tag orange">
                    {t("analyze.panel.law")}
                  </span>
                  <span>{docResult.meta?.governing_law}</span>
                </div>
              </div>

              <div className="glass-card">
                <h3>
                  <span className="emoji">📝</span>{" "}
                  {t("analyze.panel.summary")}
                </h3>
                <p className="summary-text">
                  {docResult.summary?.overall_summary}
                </p>
              </div>

              <div className="glass-card">
                <h3>
                  <span className="emoji">⚠️</span>{" "}
                  {t("analyze.panel.risk")}
                </h3>

                <div className="risk-meta">
                  <span>
                    {t("analyze.panel.risk_total")}:{" "}
                    {docResult.risk_profile.overall_risk_score}
                  </span>
                  <span>
                    {t("analyze.panel.risk_level")}:{" "}
                    {docResult.risk_profile.overall_risk_level}
                  </span>
                </div>

                <div className="risk-bars">
                  {Object.entries(
                    docResult.risk_profile.risk_dimensions || {}
                  ).map(([k, v], idx) => (
                    <div className="risk-bar-item" key={idx}>
                      <span className="risk-name">{k}</span>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{ width: `${v}%` }}
                        />
                      </div>
                      <span className="bar-value">{v}</span>
                    </div>
                  ))}
                </div>
              </div>

              {docResult.summary?.key_points?.length > 0 && (
                <div className="glass-card">
                  <h3>
                    <span className="emoji">✨</span>{" "}
                    {t("analyze.panel.key_points")}
                  </h3>
                  <ul className="bullet-list">
                    {docResult.summary.key_points.map((p, idx) => (
                      <li key={idx}>• {p}</li>
                    ))}
                  </ul>
                </div>
              )}

              {docResult.summary?.recommended_actions?.length > 0 && (
                <div className="glass-card">
                  <h3>
                    <span className="emoji">🚀</span>{" "}
                    {t("analyze.panel.recommended_actions")}
                  </h3>
                  <ul className="bullet-list">
                    {docResult.summary.recommended_actions.map((a, idx) => (
                      <li key={idx}>👉 {a}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                className="detail-btn-premium"
                onClick={handleOpenDetail}
              >
                🔍 {t("analyze.panel.detail_button")}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
