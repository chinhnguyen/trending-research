import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { generateContentIdea, getBrief } from "../api";
import { PostComposerView } from "../components/PostComposerView";
import type { ContentIdeaOut, SocialPlatform } from "../types";

export function BriefPage() {
  const { id } = useParams<{ id: string }>();
  const [brief, setBrief] = useState<Awaited<ReturnType<typeof getBrief>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getBrief(id)
      .then(setBrief)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function regenerateItem(briefItemId: string, platform: SocialPlatform) {
    setRegeneratingId(briefItemId);
    setError(null);
    try {
      const updated = await generateContentIdea({ brief_item_id: briefItemId, platform });
      setBrief((current) => {
        if (!current) return current;
        const { brief_item_id: _ignored, ...contentIdea } = updated;
        return {
          ...current,
          items: current.items.map((entry) =>
            entry.id === briefItemId ? { ...entry, content_idea: contentIdea } : entry,
          ),
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate more options");
    } finally {
      setRegeneratingId(null);
    }
  }

  if (loading) return <div className="loading panel panel-padding">Loading post…</div>;
  if (error && !brief) return <div className="error panel panel-padding">{error}</div>;
  if (!brief) return null;

  const item = brief.items[0];

  return (
    <div className="page-stack">
      <section className="hero hero-compact">
        <div className="badges">
          <span className="badge badge-accent">post ready</span>
          <span className="badge">{brief.region}</span>
        </div>
        <h1>{brief.title}</h1>
        <p>{brief.summary}</p>
      </section>

      {error ? <p className="error-text panel panel-padding">{error}</p> : null}

      {item?.content_idea ? (
        <PostComposerView
          trend={item.trend}
          evidenceSummary={item.evidence_summary}
          whyNow={item.why_now}
          idea={item.content_idea}
          briefId={brief.id}
          briefItemId={item.id}
          onGenerateMore={() => regenerateItem(item.id, item.content_idea!.platform)}
          generatingMore={regeneratingId === item.id}
        />
      ) : null}

      {brief.items.length > 1 ? (
        <section className="panel panel-padding">
          <h2 className="section-title">Other ranked trends</h2>
          <div className="brief-list">
            {brief.items.slice(1).map((other) => (
              <article key={other.id} className="brief-card">
                <h3>{other.trend.name}</h3>
                <p>{other.trend.description}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <div className="button-row">
        <Link to={`/reports/${brief.report_id}`} className="nav-link">
          Back to report
        </Link>
      </div>
    </div>
  );
}
