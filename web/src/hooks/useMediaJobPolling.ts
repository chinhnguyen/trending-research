import { useEffect, useRef, useState } from "react";
import { getMediaJob } from "../api";
import type { MediaJob, MediaJobStatus } from "../types";

const TERMINAL_STATUSES = new Set<MediaJobStatus>(["completed", "failed", "skipped"]);
const POLL_INTERVAL_MS = 2000;

export function useMediaJobPolling(jobIds: string[], onRefresh?: () => void | Promise<void>) {
  const [jobs, setJobs] = useState<MediaJob[]>([]);
  const onRefreshRef = useRef(onRefresh);

  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  useEffect(() => {
    const activeIds = [...new Set(jobIds.filter(Boolean))];
    if (activeIds.length === 0) {
      setJobs([]);
      return;
    }

    let cancelled = false;
    let interval: number | undefined;
    let refreshedAfterTerminal = false;

    async function poll() {
      try {
        const results = await Promise.all(activeIds.map((id) => getMediaJob(id)));
        if (cancelled) {
          return;
        }

        setJobs(results);

        const hasActive = results.some((job) => !TERMINAL_STATUSES.has(job.status));
        const hasTerminal = results.some((job) => TERMINAL_STATUSES.has(job.status));

        if (!hasActive && interval !== undefined) {
          window.clearInterval(interval);
          interval = undefined;
        }

        if (hasTerminal && !refreshedAfterTerminal && onRefreshRef.current) {
          refreshedAfterTerminal = true;
          await onRefreshRef.current();
        }
      } catch {
        // Keep polling through transient network errors.
      }
    }

    void poll();
    interval = window.setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (interval !== undefined) {
        window.clearInterval(interval);
      }
    };
  }, [jobIds.join("|")]);

  return jobs;
}
