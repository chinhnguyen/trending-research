import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "../i18n/LocaleProvider";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Layout() {
  const t = useTranslation();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/" className="brand-mark">
            Willbe Trends
          </Link>
          <span className="brand-sub">{t.brandSub}</span>
        </div>
        <div className="topbar-actions">
          <LanguageSwitcher />
          <nav className="nav-links" aria-label="Main">
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
        </div>
      </header>
      <Outlet />
    </div>
  );
}
