import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { generateBrief } from "../api";

export function GenerateBriefPage() {
  const { reportId, trendName } = useParams<{ reportId: string; trendName: string }>();
  const decodedTrend = trendName ? decodeURIComponent(trendName) : "";
  const navigate = useNavigate();
  const [step, setStep] = useState<"idle" | "scoring" | "generating" | "done">("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function runPipeline() {
    if (!reportId || !decodedTrend) return;
    setError(null);
    setStep("scoring");
    setMessage(`Scoring evidence for ${decodedTrend}…`);

    try {
      setStep("generating");
      setMessage("Drafting captions, hashtags, and service tie-ins…");
      const brief = await generateBrief({ report_id: reportId, trend_name: decodedTrend });
      setStep("done");
      setMessage("Post brief ready.");
      navigate(`/briefs/${brief.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Post brief generation failed");
      setStep("idle");
    }
  }

  return (
    <div className="page-stack">
      <section className="hero">
        <div className="badges">
          <span className="badge badge-accent">post brief</span>
          <span className="badge">trend-driven</span>
        </div>
        <h1>Create post for {decodedTrend || "trend"}</h1>
        <p>
          Turn this trend into salon-ready post copy: evidence, why-now context, captions,
          hashtags, and service tie-ins.
        </p>
      </section>

      <section className="panel panel-padding pipeline-panel">
        <div className="pipeline-steps">
          <div className={step !== "idle" ? "step active" : "step"}>
            <span>1</span>
            <div>
              <strong>Score trend</strong>
              <p>Confidence and citation support</p>
            </div>
          </div>
          <div className={step === "generating" || step === "done" ? "step active" : "step"}>
            <span>2</span>
            <div>
              <strong>Draft post</strong>
              <p>Evidence, why now, captions, hashtags</p>
            </div>
          </div>
          <div className={step === "done" ? "step active" : "step"}>
            <span>3</span>
            <div>
              <strong>Review and refine</strong>
              <p>Open the brief and regenerate ideas if needed</p>
            </div>
          </div>
        </div>

        {message ? <p className="status-message">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}

        <div className="button-row">
          <button
            className="button button-primary"
            onClick={runPipeline}
            disabled={!reportId || !decodedTrend || step !== "idle"}
          >
            {step === "idle" ? "Create post" : "Working…"}
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
