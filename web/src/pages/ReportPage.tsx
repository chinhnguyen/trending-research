import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getResearch } from "../api";
import { SourceList } from "../components/SourceList";
import { TrendCard } from "../components/TrendCard";
import { UsageStats } from "../components/UsageStats";
import type { ResearchDetail } from "../types";

export function ReportPage() {
  const { id } = useParams();
  const [detail, setDetail] = useState<ResearchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getResearch(id)
      .then(setDetail)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading panel panel-padding">Loading report…</div>;
  if (error) return <div className="error panel panel-padding">{error}</div>;
  if (!detail) return null;

  const { report } = detail;

  return (
    <>
      <section className="hero">
        <div className="badges">
          <span className="badge badge-accent">{report.mode}</span>
          <span className="badge">{report.category}</span>
          <span className="badge">{detail.research_time || report.research_time}</span>
          <span className="badge">{detail.region}</span>
        </div>
        {report.trends.find((trend) => trend.image_url)?.image_url ? (
          <div className="hero-gallery">
            {report.trends
              .filter((trend) => trend.image_url)
              .slice(0, 4)
              .map((trend) => (
                <img
                  key={trend.name}
                  src={trend.image_url!}
                  alt={trend.image_alt || trend.name}
                  loading="lazy"
                  referrerPolicy="no-referrer"
                />
              ))}
          </div>
        ) : null}
        <h1>{report.mode === "personalized" ? "Personalized picks" : "Neutral trends"}</h1>
        <p>{report.summary}</p>
        <p className="meta">
          {report.llm_provider}/{report.llm_model}
          {report.web_research ? ` · web:${report.web_research.search_provider}` : ""}
        </p>
        <UsageStats usage={report.llm_usage} />
      </section>

      <div className="grid-2">
        <section className="panel panel-padding">
          <div className="report-card-top" style={{ marginBottom: 18 }}>
            <h2 className="section-title" style={{ margin: 0 }}>
              Trends
            </h2>
            <span className="meta">Pick a trend to create a post</span>
          </div>
          <div className="trend-grid">
            {report.trends.map((trend) => (
              <TrendCard key={trend.name} trend={trend} reportId={detail.id} />
            ))}
          </div>
        </section>

        <aside className="panel panel-padding">
          <h2 className="section-title">Web sources</h2>
          <SourceList citations={report.web_research?.citations ?? []} />
          {detail.preferences ? (
            <>
              <h2 className="section-title" style={{ marginTop: 24 }}>
                Preferences
              </h2>
              <pre
                style={{
                  margin: 0,
                  padding: 16,
                  borderRadius: 12,
                  background: "var(--surface-muted)",
                  overflow: "auto",
                  fontSize: "0.85rem",
                }}
              >
                {JSON.stringify(detail.preferences, null, 2)}
              </pre>
            </>
          ) : null}
        </aside>
      </div>

      <div style={{ marginTop: 20 }}>
        <Link to="/" className="nav-link">
          Back to reports
        </Link>
      </div>
    </>
  );
}
