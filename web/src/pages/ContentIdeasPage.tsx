import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { generateContentIdea } from "../api";
import type { ContentIdeaOut } from "../types";

function useBriefId() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  return params.get("brief");
}

export function ContentIdeasPage() {
  const { briefItemId } = useParams<{ briefItemId: string }>();
  const briefId = useBriefId();
  const [idea, setIdea] = useState<ContentIdeaOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function regenerate() {
    if (!briefItemId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await generateContentIdea({ brief_item_id: briefItemId });
      setIdea(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Idea generation failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    regenerate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [briefItemId]);

  return (
    <div className="page-stack">
      <div className="button-row">
        {briefId ? (
          <Link to={`/briefs/${briefId}`} className="nav-link">
            Back to brief
          </Link>
        ) : null}
      </div>

      <section className="hero">
        <div className="badges">
          <span className="badge badge-accent">content ideas</span>
        </div>
        <h1>Refine content ideas</h1>
        <p>Regenerate a fresh set of angles, captions, hashtags, and tie-ins for this brief item.</p>
      </section>

      <section className="panel panel-padding">
        <div className="panel-header">
          <h2>Generated output</h2>
          <button className="button button-primary" onClick={regenerate} disabled={loading}>
            {loading ? "Generating…" : "Regenerate"}
          </button>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        {idea ? (
          <div className="brief-idea-grid">
            <div className="brief-section">
              <strong>Angles</strong>
              <ul className="plain-list">
                {idea.angles.map((angle) => (
                  <li key={angle}>{angle}</li>
                ))}
              </ul>
            </div>
            <div className="brief-section">
              <strong>Hashtags</strong>
              <div className="chips" style={{ marginTop: 8 }}>
                {idea.hashtags.map((tag) => (
                  <span key={tag} className="chip">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div className="brief-section brief-captions">
              <strong>Captions</strong>
              {idea.captions.map((caption) => (
                <div key={caption.locale} className="caption-block">
                  <label>{caption.locale.toUpperCase()}</label>
                  <p>{caption.caption}</p>
                  {caption.cta ? <span className="meta">{caption.cta}</span> : null}
                </div>
              ))}
            </div>
            {idea.posting_tip ? (
              <div className="brief-section">
                <strong>Posting tip</strong>
                <p>{idea.posting_tip}</p>
              </div>
            ) : null}
            {idea.product_mapping ? (
              <div className="brief-section">
                <strong>Service tie-in</strong>
                <p>
                  {idea.product_mapping.service_suggestion}
                  {" · "}
                  {idea.product_mapping.product_suggestion}
                </p>
                <p className="meta">{idea.product_mapping.rationale}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>
    </div>
  );
}
