import React from "react";

export default function FileUpload({ onSelect }) {
  return (
    <div>
      <input
        type="file"
        onChange={(e) => onSelect(e.target.files[0])}
        accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
      />
    </div>
  );
}
