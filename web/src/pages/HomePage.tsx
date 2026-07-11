import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listResearch } from "../api";
import { UsageStats } from "../components/UsageStats";
import { useLocale, useTranslation } from "../i18n/LocaleProvider";
import type { ResearchListItem } from "../types";

function formatDate(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function HomePage() {
  const t = useTranslation();
  const { locale } = useLocale();
  const [items, setItems] = useState<ResearchListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listResearch()
      .then((response) => {
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <section className="hero">
        <h1>{t.homeTitle}</h1>
        <p>{t.homeSubtitle}</p>
      </section>

      {loading ? <div className="loading panel panel-padding">{t.loadingReports}</div> : null}
      {error ? <div className="error panel panel-padding">{error}</div> : null}

      {!loading && !error ? (
        <section className="panel panel-padding">
          <div className="report-card-top" style={{ marginBottom: 18 }}>
            <h2 className="section-title" style={{ margin: 0 }}>
              {t.savedRuns}
            </h2>
            <span className="meta">{t.totalCount(total)}</span>
          </div>

          {items.length === 0 ? (
            <div className="empty-state">
              <p>{t.noReports}</p>
              <Link to="/new" className="button button-primary" style={{ display: "inline-block", marginTop: 12 }}>
                {t.runFirstResearch}
              </Link>
            </div>
          ) : (
            <div className="report-list">
              {items.map((item) => (
                <Link key={item.id} to={`/reports/${item.id}`} className="report-card">
                  <div className="report-card-layout">
                    {item.cover_image_url ? (
                      <img
                        className="report-card-thumb"
                        src={item.cover_image_url}
                        alt=""
                        loading="lazy"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <div className="report-card-thumb report-card-thumb-empty">{t.noImage}</div>
                    )}
                    <div className="report-card-content">
                      <div className="report-card-top">
                        <div className="badges">
                          <span className="badge badge-accent">{t.modeBadge(item.mode)}</span>
                          <span className="badge">{item.category === "nails" ? t.categoryNails : item.category}</span>
                          <span className="badge">{item.research_time}</span>
                          {item.web_search_enabled ? (
                            <span className="badge">{t.webSearchBadge}</span>
                          ) : null}
                        </div>
                        <span className="meta">{formatDate(item.created_at, locale)}</span>
                      </div>
                      <p>{item.summary}</p>
                      <div className="meta">
                        {t.trends(item.trend_count)} · {t.imagesCount(item.image_count)} ·{" "}
                        {t.sourcesCount(item.citation_count)} · {item.llm_provider}/{item.llm_model}
                        {item.llm_usage ? (
                          <>
                            {" "}
                            · <UsageStats usage={item.llm_usage} compact />
                          </>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </>
  );
}
