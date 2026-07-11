import { useTranslation } from "../i18n/LocaleProvider";
import type { TrendSignal } from "../types";
import { popularityLabel } from "../utils/formatLabels";

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
  const t = useTranslation();

  return (
    <section className="trend-reference panel panel-padding">
      <p className="meta section-eyebrow">{t.trendReference}</p>
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
                {t.viewSource}
              </a>
            ) : null}
          </div>
        ) : (
          <div className="trend-reference-media trend-media-empty">{t.noReferenceImage}</div>
        )}

        <div className="trend-reference-copy">
          <div className="badges" style={{ marginBottom: 10 }}>
            <span className={`badge badge-accent popularity-${popularityClass(trend.popularity)}`}>
              {popularityLabel(trend.popularity, t)}
            </span>
            {trend.confidence ? (
              <span className="badge">{t.confidence(Math.round(trend.confidence * 100))}</span>
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
              <strong>{t.whyThisTrend}</strong>
              <p>{evidenceSummary}</p>
            </div>
          ) : null}
          {whyNow ? (
            <div className="trend-reference-note">
              <strong>{t.whyNow}</strong>
              <p>{whyNow}</p>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
