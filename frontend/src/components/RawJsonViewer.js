// src/components/RawJsonViewer.js
import React, { useState } from "react";

export default function RawJsonViewer({ data }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!data) return null;

  return (
    <div className="raw-json">
      <div className="raw-json-header">
        <span>Raw JSON</span>
        <button
          className="raw-json-toggle"
          onClick={() => setCollapsed((p) => !p)}
        >
          {collapsed ? "펼치기" : "접기"}
        </button>
      </div>
      {!collapsed && (
        <pre className="raw-json-body">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
