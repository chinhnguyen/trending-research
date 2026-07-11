import { useTranslation } from "../i18n/LocaleProvider";
import type { MediaJob } from "../types";

export function OptionMediaProgress({ job }: { job: MediaJob }) {
  const t = useTranslation();

  function statusLabel(status: MediaJob["status"]) {
    switch (status) {
      case "queued":
        return t.statusQueued;
      case "generating_media":
        return t.statusGenerating;
      case "completed":
        return t.statusReady;
      case "failed":
        return t.statusFailed;
      case "skipped":
        return t.statusSkipped;
      case "cancelled":
        return t.statusCancelled;
      default:
        return status;
    }
  }

  const isFailed = job.status === "failed";
  const isActive = job.status === "queued" || job.status === "generating_media";

  if (!isActive && !isFailed) {
    return null;
  }

  return (
    <div className="option-media-progress" aria-live="polite">
      <div className="option-media-progress-header">
        <strong>{isFailed ? t.generationFailed : statusLabel(job.status)}</strong>
        {isActive ? <span className="meta">{job.progress_percent}%</span> : null}
      </div>
      {isActive ? (
        <div className="media-job-progress" aria-hidden="true">
          <span style={{ width: `${job.progress_percent}%` }} />
        </div>
      ) : null}
      <p className="media-job-stage">{isFailed ? job.error_message ?? job.stage : job.stage}</p>
      {isActive ? <p className="meta option-media-hint">{t.safeToReload}</p> : null}
    </div>
  );
}

export function findActiveJobForOption(
  jobs: MediaJob[] | undefined,
  contentIdeaId: string,
  kind: "image" | "video",
  sequence: number,
) {
  return jobs
    ?.filter(
      (job) =>
        job.content_idea_id === contentIdeaId &&
        job.target_kind === kind &&
        job.target_sequence === sequence &&
        (job.status === "queued" || job.status === "generating_media" || job.status === "failed"),
    )
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0];
}

export function findActiveJobForIdea(jobs: MediaJob[] | undefined, contentIdeaId: string) {
  return jobs
    ?.filter(
      (job) =>
        job.content_idea_id === contentIdeaId &&
        (job.status === "queued" || job.status === "generating_media" || job.status === "failed"),
    )
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0];
}

export function lastPendingOptionIndex(
  options: Array<{ imageUrl?: string | null; videoUrl?: string | null }>,
) {
  let lastIndex = -1;
  options.forEach((option, index) => {
    if (!option.imageUrl && !option.videoUrl) {
      lastIndex = index;
    }
  });
  return lastIndex;
}
