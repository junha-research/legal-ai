// src/components/Sidebar.js
import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { logoutFirebase } from "../auth/firebase";

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const location = useLocation();

  const isActive = (path) =>
    location.pathname === path ||
    (path !== "/" && location.pathname.startsWith(path));

  const handleLogout = async () => {
    await logoutFirebase();
    logout();
  };

  return (
    <div
      style={{
        width: 260,
        borderRight: "1px solid #e2e8f0",
        padding: 20,
        background: "#f8fafc",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        boxSizing: "border-box",
      }}
    >
      {/* 로고 영역 */}
      <div style={{ marginBottom: 30 }}>
        <div
          style={{
            fontSize: 26,
            fontWeight: 800,
            color: "#0f172a",
            letterSpacing: "-0.5px",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          ⚖️ Legal AI
        </div>

        <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>
          {t("sidebar.slogan")}
        </div>
      </div>

      {/* 사용자 정보 */}
      {user && (
        <div
          style={{
            padding: 14,
            borderRadius: 10,
            background: "#e0f2fe",
            marginBottom: 20,
            fontSize: 13,
            boxShadow: "inset 0 0 4px rgba(0,0,0,0.05)",
          }}
        >
          <div style={{ fontWeight: 600, color: "#0f172a" }}>
            {user.name || user.email}
          </div>
          <div style={{ color: "#475569", marginTop: 3, fontSize: 12 }}>
            {user.email}
          </div>
        </div>
      )}

      {/* 네비게이션 */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <SideLink to="/" active={isActive("/")}>
          📄 {t("nav.analyze")}
        </SideLink>

        <SideLink to="/documents" active={isActive("/documents")}>
          🗂 {t("nav.documents")}
        </SideLink>

        <SideLink to="/chat" active={isActive("/chat")}>
          💬 {t("nav.chat")}
        </SideLink>
      </nav>

      {/* 언어 선택 */}
      <div style={{ marginTop: 32 }}>
        <div style={{ fontSize: 13, color: "#475569", marginBottom: 6 }}>
          🌐 {t("sidebar.language")}
        </div>

        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          style={{
            width: "100%",
            padding: "8px 10px",
            borderRadius: 6,
            border: "1px solid #cbd5e1",
            background: "#fff",
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          <option value="ko">한국어</option>
          <option value="en">English</option>
          <option value="vi">Tiếng Việt</option>
        </select>
      </div>

      {/* 로그아웃 버튼 */}
      {user && (
        <button
          onClick={handleLogout}
          style={{
            marginTop: "auto",
            padding: "10px 12px",
            fontSize: 13,
            borderRadius: 6,
            border: "none",
            background: "#fee2e2",
            color: "#b91c1c",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {t("sidebar.logout")}
        </button>
      )}
    </div>
  );
}

/* 네비 링크 */
function SideLink({ to, active, children }) {
  return (
    <Link
      to={to}
      style={{
        padding: "10px 12px",
        borderRadius: 6,
        textDecoration: "none",
        fontSize: 14,
        color: active ? "#2563eb" : "#1e293b",
        background: active ? "#dbeafe" : "transparent",
        fontWeight: active ? 600 : 500,
        transition: "0.2s",
      }}
    >
      {children}
    </Link>
  );
}
