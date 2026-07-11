import { LOCALE_LABELS, useLocale, type Locale } from "../i18n/LocaleProvider";

const LOCALES = Object.keys(LOCALE_LABELS) as Locale[];

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale();

  return (
    <div className="language-switcher" role="group" aria-label={t.language}>
      <span className="language-switcher-label">{t.language}</span>
      <div className="language-switcher-options">
        {LOCALES.map((code) => (
          <button
            key={code}
            type="button"
            className={locale === code ? "language-option active" : "language-option"}
            aria-pressed={locale === code}
            onClick={() => setLocale(code)}
          >
            {LOCALE_LABELS[code]}
          </button>
        ))}
      </div>
    </div>
  );
}
