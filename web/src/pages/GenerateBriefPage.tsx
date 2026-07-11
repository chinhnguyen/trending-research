import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { initBrief } from "../api";

export function GenerateBriefPage() {
  const { reportId, trendName } = useParams<{ reportId: string; trendName: string }>();
  const decodedTrend = trendName ? decodeURIComponent(trendName) : "";
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId || !decodedTrend) return;
    initBrief({ report_id: reportId, trend_name: decodedTrend })
      .then((brief) => navigate(`/briefs/${brief.id}`, { replace: true }))
      .catch((err: Error) => setError(err.message));
  }, [reportId, decodedTrend, navigate]);

  if (error) {
    return <div className="error panel panel-padding">{error}</div>;
  }

  return <div className="loading panel panel-padding">Opening post composer…</div>;
}
