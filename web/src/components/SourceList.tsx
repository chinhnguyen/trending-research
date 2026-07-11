import { useTranslation } from "../i18n/LocaleProvider";
import type { WebCitation } from "../types";

export function SourceList({ citations }: { citations: WebCitation[] }) {
  const t = useTranslation();

  if (citations.length === 0) {
    return <div className="empty-state">{t.noWebSources}</div>;
  }

  return (
    <div className="source-list">
      {citations.map((citation) => (
        <article key={`${citation.url}-${citation.title}`} className="source-item">
          <div className="badges" style={{ marginBottom: 8 }}>
            {citation.preferred ? <span className="badge badge-accent">{t.preferredBadge}</span> : null}
            {citation.source_name ? <span className="badge">{citation.source_name}</span> : null}
          </div>
          <strong>{citation.title}</strong>
          <p className="meta">{citation.snippet}</p>
          <a href={citation.url} target="_blank" rel="noreferrer">
            {citation.url}
          </a>
        </article>
      ))}
    </div>
  );
}
