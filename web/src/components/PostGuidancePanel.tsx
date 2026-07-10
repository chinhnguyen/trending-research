import type { ContentIdea } from "../types";

export function PostGuidancePanel({ idea }: { idea: ContentIdea }) {
  const review = idea.platform_review;
  const hints: string[] = [];
  if (idea.posting_tip) hints.push(idea.posting_tip);
  if (review?.cover_tip) hints.push(review.cover_tip);
  if (review?.sound_strategy) hints.push(`Sound: ${review.sound_strategy}`);

  return (
    <section className="post-guidance panel panel-padding">
      <p className="meta section-eyebrow">Before you publish</p>
      <div className="post-guidance-grid">
        <article className="guidance-card">
          <h3>Hints</h3>
          {hints.length > 0 ? (
            <ul className="plain-list">
              {hints.map((hint) => (
                <li key={hint}>{hint}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">Add your own salon photo and keep the hook in the first line.</p>
          )}
          {review?.posting_checklist.length ? (
            <>
              <p className="meta" style={{ marginTop: 14 }}>
                Checklist
              </p>
              <ul className="plain-list">
                {review.posting_checklist.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : null}
        </article>

        <article className="guidance-card">
          <h3>What works</h3>
          {review?.strengths.length ? (
            <ul className="plain-list">
              {review.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">Lead with a close-up of your latest client set.</p>
          )}
        </article>

        <article className="guidance-card">
          <h3>Before you post</h3>
          {review?.improvements.length ? (
            <ul className="plain-list">
              {review.improvements.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">Edit the caption so it sounds like your salon voice.</p>
          )}
        </article>
      </div>
    </section>
  );
}
