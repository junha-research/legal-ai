import React, { createContext, useContext, useState } from "react";

import ko from "../i18n/ko";
import en from "../i18n/en";
import vi from "../i18n/vi";

const LanguageContext = createContext();

const dictionaries = { ko, en, vi };

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState("ko");
  const dict = dictionaries[language];

  const t = (key) => dict[key] || key;

  const formatDate = (date) =>
    new Intl.DateTimeFormat(
      language === "ko" ? "ko-KR" :
      language === "vi" ? "vi-VN" : "en-US",
      { year: "numeric", month: "long", day: "numeric" }
    ).format(new Date(date));

  const formatNumber = (num) =>
    new Intl.NumberFormat(
      language === "ko" ? "ko-KR" :
      language === "vi" ? "vi-VN" : "en-US"
    ).format(num);

  const value = {
    language,
    setLanguage,
    t,
    formatDate,
    formatNumber,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
