import type { TrendSignal } from "../types";

function popularityClass(value: string) {
  return value.toLowerCase().replace(/\s+/g, "-");
}

export function TrendReferencePanel({
  trend,
  evidenceSummary,
  whyNow,
}: {
  trend: TrendSignal;
  evidenceSummary?: string;
  whyNow?: string;
}) {
  return (
    <section className="trend-reference panel panel-padding">
      <p className="meta section-eyebrow">Trend reference</p>
      <div className="trend-reference-grid">
        {trend.image_url ? (
          <div className="trend-reference-media">
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
          <div className="trend-reference-media trend-media-empty">No reference image</div>
        )}

        <div className="trend-reference-copy">
          <div className="badges" style={{ marginBottom: 10 }}>
            <span className={`badge badge-accent popularity-${popularityClass(trend.popularity)}`}>
              {trend.popularity}
            </span>
            {trend.confidence ? (
              <span className="badge">{Math.round(trend.confidence * 100)}% confidence</span>
            ) : null}
          </div>
          <h2 className="section-title" style={{ marginTop: 0 }}>
            {trend.name}
          </h2>
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
          {evidenceSummary ? (
            <div className="trend-reference-note">
              <strong>Why this trend</strong>
              <p>{evidenceSummary}</p>
            </div>
          ) : null}
          {whyNow ? (
            <div className="trend-reference-note">
              <strong>Why now</strong>
              <p>{whyNow}</p>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
