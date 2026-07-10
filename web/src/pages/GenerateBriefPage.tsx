import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { generateBrief, getResearch } from "../api";
import { TrendReferencePanel } from "../components/TrendReferencePanel";
import type { SocialPlatform, TrendSignal } from "../types";

const PLATFORMS: { id: SocialPlatform; label: string; description: string }[] = [
  {
    id: "instagram",
    label: "Instagram",
    description: "Feed, carousel, or Reels.",
  },
  {
    id: "tiktok",
    label: "TikTok",
    description: "Vertical short-form video.",
  },
];

export function GenerateBriefPage() {
  const { reportId, trendName } = useParams<{ reportId: string; trendName: string }>();
  const decodedTrend = trendName ? decodeURIComponent(trendName) : "";
  const navigate = useNavigate();
  const [platform, setPlatform] = useState<SocialPlatform>("instagram");
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

  const platformLabel = useMemo(
    () => PLATFORMS.find((item) => item.id === platform)?.label ?? platform,
    [platform],
  );

  async function runPipeline() {
    if (!reportId || !decodedTrend) return;
    setError(null);
    setStep("generating");
    setMessage(`Creating your ${platformLabel} post…`);

    try {
      const brief = await generateBrief({
        report_id: reportId,
        trend_name: decodedTrend,
        platform,
      });
      setStep("done");
      navigate(`/briefs/${brief.id}`);
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
          <span className="badge">{platformLabel}</span>
        </div>
        <h1>Create post for {decodedTrend || "trend"}</h1>
        <p>Review the trend below, then generate caption options and images for your salon.</p>
      </section>

      {loadingTrend ? (
        <div className="loading panel panel-padding">Loading trend reference…</div>
      ) : trend ? (
        <TrendReferencePanel trend={trend} evidenceSummary={reportSummary} />
      ) : (
        <div className="panel panel-padding error-text">Trend not found in this report.</div>
      )}

      <section className="panel panel-padding">
        <h2 className="section-title">Platform</h2>
        <div className="platform-picker">
          {PLATFORMS.map((option) => (
            <button
              key={option.id}
              type="button"
              className={platform === option.id ? "platform-card active" : "platform-card"}
              onClick={() => setPlatform(option.id)}
              disabled={step !== "idle"}
            >
              <strong>{option.label}</strong>
              <p>{option.description}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="panel panel-padding pipeline-panel">
        {message ? <p className="status-message">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}

        <div className="button-row">
          <button
            className="button button-primary"
            onClick={runPipeline}
            disabled={!reportId || !decodedTrend || !trend || step !== "idle"}
          >
            {step === "generating" ? "Generating post options…" : `Generate ${platformLabel} post`}
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
