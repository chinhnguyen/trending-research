import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { initBrief } from "../api";
import { useLocale, useTranslation } from "../i18n/LocaleProvider";

export function GenerateBriefPage() {
  const { reportId, trendName } = useParams<{ reportId: string; trendName: string }>();
  const decodedTrend = trendName ? decodeURIComponent(trendName) : "";
  const navigate = useNavigate();
  const { preferredLocale } = useLocale();
  const t = useTranslation();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId || !decodedTrend) return;
    initBrief({
      report_id: reportId,
      trend_name: decodedTrend,
      preferred_locale: preferredLocale,
    })
      .then((brief) => navigate(`/briefs/${brief.id}`, { replace: true }))
      .catch((err: Error) => setError(err.message));
  }, [reportId, decodedTrend, navigate, preferredLocale]);

  if (error) {
    return <div className="error panel panel-padding">{error}</div>;
  }

  return <div className="loading panel panel-padding">{t.openingComposer}</div>;
}
