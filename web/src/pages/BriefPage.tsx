import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getBrief } from "../api";
import { UsageStats } from "../components/UsageStats";
import type { TrendBrief } from "../types";

export function BriefPage() {
  const { id } = useParams<{ id: string }>();
  const [brief, setBrief] = useState<TrendBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getBrief(id)
      .then(setBrief)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading panel panel-padding">Loading brief…</div>;
  if (error) return <div className="error panel panel-padding">{error}</div>;
  if (!brief) return null;

  return (
    <div className="page-stack">
      <section className="hero">
        <div className="badges">
          <span className="badge badge-accent">brief</span>
          <span className="badge">{brief.region}</span>
          <span className="badge">{brief.research_time || "current"}</span>
        </div>
        <h1>{brief.title}</h1>
        <p>{brief.summary}</p>
        <p className="meta">
          {brief.llm_provider}/{brief.llm_model}
        </p>
        <UsageStats usage={brief.llm_usage} />
      </section>

      <section className="panel panel-padding">
        <div className="report-card-top" style={{ marginBottom: 18 }}>
          <h2 className="section-title" style={{ margin: 0 }}>
            Ranked trends
          </h2>
          <span className="meta">{brief.items.length} items</span>
        </div>
        <div className="brief-list">
          {brief.items.map((item) => (
            <article key={item.id} className="brief-card">
              <div className="brief-card-top">
                <div>
                  <div className="badges" style={{ marginBottom: 10 }}>
                    <span className="badge badge-accent">#{item.rank}</span>
                    <span className="badge">{Math.round(item.score * 100)} brief score</span>
                    <span className="badge">{item.trend.popularity}</span>
                  </div>
                  <h3>{item.trend.name}</h3>
                </div>
                <Link to={`/ideas/${item.id}?brief=${brief.id}`} className="nav-link">
                  Regenerate ideas
                </Link>
              </div>

              <p>{item.trend.description}</p>
              <div className="brief-section">
                <strong>Evidence</strong>
                <p>{item.evidence_summary}</p>
              </div>
              <div className="brief-section">
                <strong>Why now</strong>
                <p>{item.why_now}</p>
              </div>
              {item.caveats ? (
                <div className="brief-section">
                  <strong>Caveat</strong>
                  <p>{item.caveats}</p>
                </div>
              ) : null}

              {item.content_idea ? (
                <div className="brief-idea-grid">
                  <div className="brief-section">
                    <strong>Angles</strong>
                    <ul className="plain-list">
                      {item.content_idea.angles.map((angle) => (
                        <li key={angle}>{angle}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="brief-section">
                    <strong>Hashtags</strong>
                    <div className="chips" style={{ marginTop: 8 }}>
                      {item.content_idea.hashtags.map((tag) => (
                        <span key={tag} className="chip">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="brief-section brief-captions">
                    <strong>Captions</strong>
                    {item.content_idea.captions.map((caption) => (
                      <div key={caption.locale} className="caption-block">
                        <label>{caption.locale.toUpperCase()}</label>
                        <p>{caption.caption}</p>
                        {caption.cta ? <span className="meta">{caption.cta}</span> : null}
                      </div>
                    ))}
                  </div>
                  {item.content_idea.posting_tip ? (
                    <div className="brief-section">
                      <strong>Posting tip</strong>
                      <p>{item.content_idea.posting_tip}</p>
                    </div>
                  ) : null}
                  {item.content_idea.product_mapping ? (
                    <div className="brief-section">
                      <strong>Service tie-in</strong>
                      <p>
                        {item.content_idea.product_mapping.service_suggestion}
                        {" · "}
                        {item.content_idea.product_mapping.product_suggestion}
                      </p>
                      <p className="meta">{item.content_idea.product_mapping.rationale}</p>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <div className="button-row">
        <Link to={`/reports/${brief.report_id}`} className="nav-link">
          Back to report
        </Link>
      </div>
    </div>
  );
}
