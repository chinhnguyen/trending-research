import { Link } from "react-router-dom";
import { useTranslation } from "../i18n/LocaleProvider";
import type { TrendSignal } from "../types";
import { popularityLabel } from "../utils/formatLabels";

function popularityClass(value: string) {
  return value.toLowerCase().replace(/\s+/g, "-");
}

export function TrendCard({
  trend,
  reportId,
}: {
  trend: TrendSignal;
  reportId?: string;
}) {
  const t = useTranslation();

  return (
    <article className="trend-card">
      {trend.image_url ? (
        <div className="trend-media">
          <img
            src={trend.image_url}
            alt={trend.image_alt || trend.name}
            loading="lazy"
            referrerPolicy="no-referrer"
          />
          {trend.image_source_url ? (
            <a
              className="trend-media-link"
              href={trend.image_source_url}
              target="_blank"
              rel="noreferrer"
            >
              {t.viewSource}
            </a>
          ) : null}
        </div>
      ) : (
        <div className="trend-media trend-media-empty">{t.noReferenceImageFound}</div>
      )}

      <div className="trend-card-body">
        <div className="badges" style={{ marginBottom: 10 }}>
          <span className={`badge badge-accent popularity-${popularityClass(trend.popularity)}`}>
            {popularityLabel(trend.popularity, t)}
          </span>
          {trend.confidence ? (
            <span className="badge">{t.confidence(Math.round(trend.confidence * 100))}</span>
          ) : null}
        </div>
        <h3>{trend.name}</h3>
        <p>{trend.description}</p>
        {(trend.colors.length > 0 || trend.techniques.length > 0) && (
          <div className="chips">
            {trend.colors.map((color) => (
              <span key={color} className="chip">
                {color}
              </span>
            ))}
            {trend.techniques.map((technique) => (
              <span key={technique} className="chip">
                {technique}
              </span>
            ))}
          </div>
        )}
        {trend.source_hint ? (
          <p className="meta" style={{ marginTop: 12 }}>
            {t.sourceLabel}: {trend.source_hint}
          </p>
        ) : null}
        {reportId ? (
          <div className="trend-card-actions">
            <Link
              to={`/briefs/generate/${reportId}/${encodeURIComponent(trend.name)}`}
              className="button button-primary button-compact"
            >
              {t.createPost}
            </Link>
          </div>
        ) : null}
      </div>
    </article>
  );
}
