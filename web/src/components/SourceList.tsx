import type { WebCitation } from "../types";

export function SourceList({ citations }: { citations: WebCitation[] }) {
  if (citations.length === 0) {
    return <div className="empty-state">No web sources attached to this report.</div>;
  }

  return (
    <div className="source-list">
      {citations.map((citation) => (
        <article key={`${citation.url}-${citation.title}`} className="source-item">
          <div className="badges" style={{ marginBottom: 8 }}>
            {citation.preferred ? <span className="badge badge-accent">Preferred</span> : null}
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
