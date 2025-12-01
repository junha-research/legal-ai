// src/pages/LoginPage.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithGoogle } from "../auth/firebase";
import { useAuth } from "../auth/AuthContext";
import { useLanguage } from "../context/LanguageContext";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const handleLogin = async () => {
    try {
      setLoading(true);
      const { token } = await loginWithGoogle();
      login(token); // AuthContext → /auth/me 호출
      navigate("/");
    } catch (e) {
      console.error(e);
      alert(t("login.error") + ": " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        background:
          "radial-gradient(circle at top left, #eef2ff, #f9fafb 40%, #e0f2fe)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          background: "#ffffff",
          borderRadius: 16,
          padding: 32,
          boxShadow: "0 20px 40px rgba(15,23,42,0.08)",
        }}
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 28, fontWeight: "bold" }}>⚖️ Legal AI</div>
          <div style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
            {t("login.subtitle")}
          </div>
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: 999,
            border: "1px solid #e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            background: "#111827",
            color: "#f9fafb",
            cursor: "pointer",
            fontWeight: 500,
          }}
        >
          {loading ? t("login.loading") : t("login.google")}
        </button>
      </div>
    </div>
  );
}
