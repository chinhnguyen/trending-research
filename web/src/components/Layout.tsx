import { Link, Outlet } from "react-router-dom";
import { LOCALE_LABELS, useLocale, type Locale } from "../i18n/LocaleProvider";

export function Layout() {
  const { locale, setLocale, t } = useLocale();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/" className="brand-mark">
            Willbe Trends
          </Link>
          <span className="brand-sub">{t.brandSub}</span>
        </div>
        <nav className="nav-links">
          <label className="locale-switcher meta">
            <span className="sr-only">{t.language}</span>
            <select
              value={locale}
              onChange={(event) => setLocale(event.target.value as Locale)}
              aria-label={t.language}
            >
              {(Object.keys(LOCALE_LABELS) as Locale[]).map((code) => (
                <option key={code} value={code}>
                  {LOCALE_LABELS[code]}
                </option>
              ))}
            </select>
          </label>
          <Link to="/" className="nav-link">
            {t.navReports}
          </Link>
          <Link to="/settings/prompts" className="nav-link">
            {t.navPrompts}
          </Link>
          <Link to="/settings/sources" className="nav-link">
            {t.navSources}
          </Link>
          <Link to="/new" className="nav-link button-primary">
            {t.navNewResearch}
          </Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
