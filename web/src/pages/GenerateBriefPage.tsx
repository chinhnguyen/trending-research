import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { generateBrief } from "../api";

export function GenerateBriefPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const [step, setStep] = useState<"idle" | "scoring" | "generating" | "done">("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function runPipeline() {
    if (!reportId) return;
    setError(null);
    setStep("scoring");
    setMessage("Ranking the saved trend report into a concise brief…");

    try {
      setStep("generating");
      setMessage("Generating evidence summaries, captions, and hashtags…");
      const brief = await generateBrief({ report_id: reportId });
      setStep("done");
      setMessage(`Brief ready with ${brief.items.length} ranked trends.`);
      navigate(`/briefs/${brief.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Brief generation failed");
      setStep("idle");
    }
  }

  return (
    <div className="page-stack">
      <section className="hero">
        <div className="badges">
          <span className="badge badge-accent">brief</span>
          <span className="badge">report-driven</span>
        </div>
        <h1>Generate trend brief</h1>
        <p>
          Turn an existing research report into a ranked salon-ready brief with why-now context,
          post angles, captions, hashtags, and service tie-ins.
        </p>
      </section>

      <section className="panel panel-padding pipeline-panel">
        <div className="pipeline-steps">
          <div className={step !== "idle" ? "step active" : "step"}>
            <span>1</span>
            <div>
              <strong>Score trends</strong>
              <p>Confidence, evidence, and idea richness</p>
            </div>
          </div>
          <div className={step === "generating" || step === "done" ? "step active" : "step"}>
            <span>2</span>
            <div>
              <strong>Enrich brief</strong>
              <p>Evidence summary, why now, captions, hashtags</p>
            </div>
          </div>
          <div className={step === "done" ? "step active" : "step"}>
            <span>3</span>
            <div>
              <strong>Review and refine</strong>
              <p>Open the brief and regenerate ideas per trend</p>
            </div>
          </div>
        </div>

        {message ? <p className="status-message">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}

        <div className="button-row">
          <button className="button button-primary" onClick={runPipeline} disabled={!reportId || step !== "idle"}>
            {step === "idle" ? "Generate brief" : "Working…"}
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
