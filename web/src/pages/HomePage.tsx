import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listResearch } from "../api";
import { UsageStats } from "../components/UsageStats";
import type { ResearchListItem } from "../types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function HomePage() {
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
        <h1>Research reports</h1>
        <p>
          Browse saved nail trend analyses from neutral and personalized runs, complete with
          web sources and model metadata.
        </p>
      </section>

      {loading ? <div className="loading panel panel-padding">Loading reports…</div> : null}
      {error ? <div className="error panel panel-padding">{error}</div> : null}

      {!loading && !error ? (
        <section className="panel panel-padding">
          <div className="report-card-top" style={{ marginBottom: 18 }}>
            <h2 className="section-title" style={{ margin: 0 }}>
              Saved runs
            </h2>
            <span className="meta">{total} total</span>
          </div>

          {items.length === 0 ? (
            <div className="empty-state">
              <p>No reports yet.</p>
              <Link to="/new" className="button button-primary" style={{ display: "inline-block", marginTop: 12 }}>
                Run your first research
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
                      <div className="report-card-thumb report-card-thumb-empty">No image</div>
                    )}
                    <div className="report-card-content">
                      <div className="report-card-top">
                        <div className="badges">
                          <span className="badge badge-accent">{item.mode}</span>
                          <span className="badge">{item.category}</span>
                          <span className="badge">{item.research_time}</span>
                          {item.web_search_enabled ? (
                            <span className="badge">web search</span>
                          ) : null}
                        </div>
                        <span className="meta">{formatDate(item.created_at)}</span>
                      </div>
                      <p>{item.summary}</p>
                      <div className="meta">
                        {item.trend_count} trends · {item.image_count} images · {item.citation_count}{" "}
                        sources · {item.llm_provider}/{item.llm_model}
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
