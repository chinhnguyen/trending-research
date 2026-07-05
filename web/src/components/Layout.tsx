import { Link, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/" className="brand-mark">
            Willbe Trends
          </Link>
          <span className="brand-sub">AI nail trend research</span>
        </div>
        <nav className="nav-links">
          <Link to="/" className="nav-link">
            Reports
          </Link>
          <Link to="/settings/prompts" className="nav-link">
            Prompts
          </Link>
          <Link to="/settings/sources" className="nav-link">
            Sources
          </Link>
          <Link to="/new" className="nav-link button-primary">
            New research
          </Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
