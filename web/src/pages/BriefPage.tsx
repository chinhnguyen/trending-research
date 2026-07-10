import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { generateContentIdea, getBrief } from "../api";
import { PostComposerView } from "../components/PostComposerView";
import { useMediaJobPolling } from "../hooks/useMediaJobPolling";
import type { MediaJob, PostFormat, SocialPlatform, TrendBrief } from "../types";

function mergeJobs(...groups: Array<MediaJob[] | undefined>) {
  const merged = new Map<string, MediaJob>();
  for (const group of groups) {
    for (const job of group ?? []) {
      merged.set(job.id, job);
    }
  }
  return Array.from(merged.values());
}

export function BriefPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const [brief, setBrief] = useState<TrendBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [trackedJobs, setTrackedJobs] = useState<MediaJob[]>(() => {
    const fromNav = (location.state as { mediaJobs?: MediaJob[] } | null)?.mediaJobs;
    return fromNav ?? [];
  });

  const loadBrief = useCallback(async () => {
    if (!id) return;
    const data = await getBrief(id);
    setBrief(data);
    if (data.active_media_jobs?.length) {
      setTrackedJobs((current) => mergeJobs(current, data.active_media_jobs));
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadBrief()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id, loadBrief]);

  const jobIds = useMemo(() => {
    const ids = new Set<string>();
    for (const job of trackedJobs) ids.add(job.id);
    for (const job of brief?.active_media_jobs ?? []) ids.add(job.id);
    return Array.from(ids);
  }, [trackedJobs, brief?.active_media_jobs]);

  const pollingJobs = useMediaJobPolling(jobIds, loadBrief);

  useEffect(() => {
    if (pollingJobs.length === 0) return;
    setTrackedJobs((current) => mergeJobs(current, pollingJobs));
  }, [pollingJobs]);

  const progressJobs = useMemo(
    () => mergeJobs(trackedJobs, brief?.active_media_jobs, pollingJobs),
    [trackedJobs, pollingJobs, brief?.active_media_jobs],
  );

  async function regenerateItem(briefItemId: string, platform: SocialPlatform, postFormat: PostFormat) {
    setRegeneratingId(briefItemId);
    setError(null);
    try {
      const updated = await generateContentIdea({ brief_item_id: briefItemId, platform, post_format: postFormat });
      if (updated.active_media_job) {
        setTrackedJobs((current) => mergeJobs(current, [updated.active_media_job!]));
      }
      setBrief((current) => {
        if (!current) return current;
        const { brief_item_id: _ignored, active_media_job: _job, ...contentIdea } = updated;
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
  const mediaBusy = progressJobs.some(
    (job) => job.status === "queued" || job.status === "generating_media",
  );

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
          mediaJobs={progressJobs}
          onGenerateMore={(setup) =>
            regenerateItem(item.id, setup.platform, setup.postFormat)
          }
          generatingMore={regeneratingId === item.id || mediaBusy}
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
