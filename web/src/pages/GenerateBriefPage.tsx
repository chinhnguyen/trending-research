import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { generateBrief, getResearch } from "../api";
import { PostSetupPicker, postSetupLabel, type PostSetup } from "../components/PostSetupPicker";
import { TrendReferencePanel } from "../components/TrendReferencePanel";
import type { TrendSignal } from "../types";

export function GenerateBriefPage() {
  const { reportId, trendName } = useParams<{ reportId: string; trendName: string }>();
  const decodedTrend = trendName ? decodeURIComponent(trendName) : "";
  const navigate = useNavigate();
  const [setup, setSetup] = useState<PostSetup>({ platform: "instagram", postFormat: "image" });
  const [trend, setTrend] = useState<TrendSignal | null>(null);
  const [reportSummary, setReportSummary] = useState("");
  const [loadingTrend, setLoadingTrend] = useState(true);
  const [step, setStep] = useState<"idle" | "generating" | "done">("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId || !decodedTrend) return;
    getResearch(reportId)
      .then((detail) => {
        setReportSummary(detail.report.summary);
        const match = detail.report.trends.find(
          (item) => item.name.toLowerCase() === decodedTrend.toLowerCase(),
        );
        setTrend(match ?? null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoadingTrend(false));
  }, [reportId, decodedTrend]);

  const setupLabel = useMemo(() => postSetupLabel(setup), [setup]);

  async function runPipeline() {
    if (!reportId || !decodedTrend) return;
    setError(null);
    setStep("generating");
    setMessage(`Writing captions for ${setupLabel.toLowerCase()}…`);

    try {
      const brief = await generateBrief({
        report_id: reportId,
        trend_name: decodedTrend,
        platform: setup.platform,
        post_format: setup.postFormat,
      });
      setMessage(
        brief.active_media_jobs?.length
          ? "Captions are ready. Creating media in the background…"
          : "Post is ready.",
      );
      setStep("done");
      navigate(`/briefs/${brief.id}`, {
        state: brief.active_media_jobs?.length ? { mediaJobs: brief.active_media_jobs } : undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Post generation failed");
      setStep("idle");
    }
  }

  return (
    <div className="page-stack">
      <section className="hero hero-compact">
        <div className="badges">
          <span className="badge badge-accent">create post</span>
        </div>
        <h1>Create post for {decodedTrend || "trend"}</h1>
        <p>Review the trend, choose where you want to publish, then generate your first post option.</p>
      </section>

      {loadingTrend ? (
        <div className="loading panel panel-padding">Loading trend reference…</div>
      ) : trend ? (
        <TrendReferencePanel trend={trend} evidenceSummary={reportSummary} />
      ) : (
        <div className="panel panel-padding error-text">Trend not found in this report.</div>
      )}

      <section className="panel panel-padding post-setup-panel">
        <div className="post-setup-intro">
          <p className="meta section-eyebrow">Post setup</p>
          <h2 className="section-title">Choose platform and type</h2>
          <p className="meta">
            Each post can target a different network and format. Start with one combination for this trend.
          </p>
        </div>

        <PostSetupPicker value={setup} onChange={setSetup} disabled={step !== "idle"} />

        <div className="post-setup-summary">
          <span className="badge badge-accent">{setupLabel}</span>
          <p className="meta">
            {setup.postFormat === "video"
              ? "We'll draft a vertical clip with hook, caption, and hashtags."
              : "We'll draft caption copy, hashtags, and a salon image for this post."}
          </p>
        </div>

        {message ? <p className="status-message">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}

        <div className="button-row">
          <button
            className="button button-primary"
            onClick={runPipeline}
            disabled={!reportId || !decodedTrend || !trend || step !== "idle"}
          >
            {step === "generating" ? "Generating post…" : `Generate ${setupLabel}`}
          </button>
          {reportId ? (
            <Link to={`/reports/${reportId}`} className="nav-link">
              Back to report
            </Link>
          ) : null}
        </div>
      </section>
    </div>
  );
}
