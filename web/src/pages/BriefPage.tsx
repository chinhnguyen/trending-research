import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  acceptMediaPrompt,
  adjustMediaPrompt,
  generateContentIdea,
  getBrief,
  regenerateMediaPrompt,
  type RegenerateField,
} from "../api";
import { PostComposerView } from "../components/PostComposerView";
import type { MediaPromptTarget, OptionDraft } from "../components/PostOptionsList";
import { useMediaJobPolling } from "../hooks/useMediaJobPolling";
import { useLocale, useTranslation } from "../i18n/LocaleProvider";
import type { ContentIdeaOut, MediaJob, PostFormat, SocialPlatform, TrendBrief } from "../types";
import { parseHashtags } from "../utils/postFormat";

function mergeJobs(...groups: Array<MediaJob[] | undefined>) {
  const merged = new Map<string, MediaJob>();
  for (const group of groups) {
    for (const job of group ?? []) {
      merged.set(job.id, job);
    }
  }
  return Array.from(merged.values());
}

function applyContentIdeaUpdate(brief: TrendBrief, updated: ContentIdeaOut): TrendBrief {
  const { brief_item_id: briefItemId, active_media_job: _job, ...contentIdea } = updated;
  return {
    ...brief,
    items: brief.items.map((entry) =>
      entry.id === briefItemId ? { ...entry, content_idea: contentIdea } : entry,
    ),
  };
}

function apiTarget(target: MediaPromptTarget) {
  return {
    content_idea_id: target.contentIdeaId,
    kind: target.kind,
    sequence: target.sequence,
  };
}

function draftPayload(draft: OptionDraft) {
  return {
    prompt: draft.prompt.trim(),
    hook: draft.hook.trim() || null,
    caption: draft.caption.trim(),
    hashtags: parseHashtags(draft.hashtagsText),
  };
}

export function BriefPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const { preferredLocale } = useLocale();
  const t = useTranslation();
  const [brief, setBrief] = useState<TrendBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [promptBusyKey, setPromptBusyKey] = useState<string | null>(null);
  const [regeneratingField, setRegeneratingField] = useState<RegenerateField | null>(null);
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

  const mediaGenerating = progressJobs.some(
    (job) => job.status === "queued" || job.status === "generating_media",
  );

  async function withPromptAction(
    target: MediaPromptTarget,
    action: () => Promise<ContentIdeaOut>,
    field: RegenerateField | null = null,
  ) {
    const key = `${target.kind}-${target.sequence}`;
    setPromptBusyKey(key);
    setRegeneratingField(field);
    setError(null);
    try {
      const updated = await action();
      if (updated.active_media_job) {
        setTrackedJobs((current) => mergeJobs(current, [updated.active_media_job!]));
      }
      setBrief((current) => (current ? applyContentIdeaUpdate(current, updated) : current));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.couldNotUpdatePrompt);
    } finally {
      setPromptBusyKey(null);
      setRegeneratingField(null);
    }
  }

  async function generateOption(briefItemId: string, platform: SocialPlatform, postFormat: PostFormat) {
    setGenerating(true);
    setError(null);
    try {
      const updated = await generateContentIdea({
        brief_item_id: briefItemId,
        platform,
        post_format: postFormat,
        preferred_locale: preferredLocale,
      });
      setBrief((current) => (current ? applyContentIdeaUpdate(current, updated) : current));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.couldNotGenerate);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) return <div className="loading panel panel-padding">{t.loadingPost}</div>;
  if (error && !brief) return <div className="error panel panel-padding">{error}</div>;
  if (!brief) return null;

  const item = brief.items[0];
  const optionCount =
    (item?.content_idea?.image_recommendations.length ?? 0) +
    (item?.content_idea?.video_recommendations.length ?? 0);

  return (
    <div className="page-stack">
      <section className="hero hero-compact">
        <div className="badges">
          <span className="badge badge-accent">{optionCount ? t.postComposer : t.createPost}</span>
          <span className="badge">{brief.region}</span>
        </div>
        <h1>{brief.title}</h1>
        <p>{brief.summary}</p>
      </section>

      {error ? <p className="error-text panel panel-padding">{error}</p> : null}

      {item ? (
        <PostComposerView
          trend={item.trend}
          evidenceSummary={item.evidence_summary}
          whyNow={item.why_now}
          idea={item.content_idea}
          contentIdeaId={item.content_idea?.id}
          mediaJobs={progressJobs}
          onGenerate={(setup) => generateOption(item.id, setup.platform, setup.postFormat)}
          generating={generating}
          mediaGenerating={mediaGenerating}
          promptBusyKey={promptBusyKey}
          regeneratingField={regeneratingField}
          onAcceptPrompt={(target, draft) =>
            withPromptAction(target, async () => {
              await adjustMediaPrompt({ ...apiTarget(target), ...draftPayload(draft) });
              return acceptMediaPrompt(apiTarget(target));
            })
          }
          onRegeneratePrompt={(target, field) =>
            withPromptAction(
              target,
              () =>
                regenerateMediaPrompt({
                  ...apiTarget(target),
                  field,
                  preferred_locale: preferredLocale,
                }),
              field,
            )
          }
        />
      ) : null}

      {brief.items.length > 1 ? (
        <section className="panel panel-padding">
          <h2 className="section-title">{t.otherTrends}</h2>
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
          {t.backToReport}
        </Link>
      </div>
    </div>
  );
}
