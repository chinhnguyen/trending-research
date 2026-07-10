import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { generateContentIdea, getBrief } from "../api";
import { PostComposerView } from "../components/PostComposerView";
import type { BriefItem, ContentIdeaOut, SocialPlatform } from "../types";

function useBriefId() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  return params.get("brief");
}

function useInitialPlatform() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const value = params.get("platform");
  return value === "tiktok" ? "tiktok" : "instagram";
}

export function ContentIdeasPage() {
  const { briefItemId } = useParams<{ briefItemId: string }>();
  const briefId = useBriefId();
  const [platform, setPlatform] = useState<SocialPlatform>(useInitialPlatform());
  const [idea, setIdea] = useState<ContentIdeaOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [briefItem, setBriefItem] = useState<BriefItem | null>(null);

  useEffect(() => {
    if (!briefId) return;
    getBrief(briefId)
      .then((brief) => {
        const item = brief.items.find((entry) => entry.id === briefItemId);
        if (item) setBriefItem(item);
      })
      .catch(() => undefined);
  }, [briefId, briefItemId]);

  async function regenerate() {
    if (!briefItemId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await generateContentIdea({ brief_item_id: briefItemId, platform });
      const { brief_item_id: _ignored, ...contentIdea } = data;
      setIdea(data);
      if (briefItem) {
        setBriefItem({ ...briefItem, content_idea: contentIdea });
      }
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
            Back to post
          </Link>
        ) : null}
      </div>

      <section className="hero hero-compact">
        <h1>Generate more options</h1>
        <p>Switch platform or regenerate captions and images.</p>
      </section>

      <section className="panel panel-padding">
        <div className="panel-header">
          <div className="platform-picker compact">
            <button
              type="button"
              className={platform === "instagram" ? "platform-card active" : "platform-card"}
              onClick={() => setPlatform("instagram")}
              disabled={loading}
            >
              Instagram
            </button>
            <button
              type="button"
              className={platform === "tiktok" ? "platform-card active" : "platform-card"}
              onClick={() => setPlatform("tiktok")}
              disabled={loading}
            >
              TikTok
            </button>
          </div>
          <button className="button button-primary" onClick={regenerate} disabled={loading}>
            {loading ? "Generating…" : "Regenerate"}
          </button>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        {idea && briefItem ? (
          <PostComposerView
            trend={briefItem.trend}
            evidenceSummary={briefItem.evidence_summary}
            whyNow={briefItem.why_now}
            idea={idea}
            briefId={briefId ?? undefined}
            briefItemId={briefItemId}
            onGenerateMore={regenerate}
            generatingMore={loading}
          />
        ) : null}
      </section>
    </div>
  );
}
