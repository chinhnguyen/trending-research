import { Link } from "react-router-dom";
import type { TrendSignal } from "../types";

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
              View source
            </a>
          ) : null}
        </div>
      ) : (
        <div className="trend-media trend-media-empty">No reference image found</div>
      )}

      <div className="trend-card-body">
        <div className="badges" style={{ marginBottom: 10 }}>
          <span className={`badge badge-accent popularity-${popularityClass(trend.popularity)}`}>
            {trend.popularity}
          </span>
          {trend.confidence ? (
            <span className="badge">{Math.round(trend.confidence * 100)}% confidence</span>
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
            Source: {trend.source_hint}
          </p>
        ) : null}
        {reportId ? (
          <div className="trend-card-actions">
            <Link
              to={`/briefs/generate/${reportId}/${encodeURIComponent(trend.name)}`}
              className="button button-primary button-compact"
            >
              Create post
            </Link>
          </div>
        ) : null}
      </div>
    </article>
  );
}
