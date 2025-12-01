import { useLanguage } from "../context/LanguageContext";

export function useI18n() {
  const { t, formatDate, formatNumber, language, setLanguage } = useLanguage();
  return { t, formatDate, formatNumber, language, setLanguage };
}

// hook이 아닌 환경을 위한 placeholder
export const i18n = {
  t: (key) => key,
  formatDate: (date) => date,
  formatNumber: (num) => num,
};
