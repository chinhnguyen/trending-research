import { useTranslation } from "../i18n/LocaleProvider";
import type { ContentIdea } from "../types";

export function PostGuidancePanel({ idea }: { idea: ContentIdea }) {
  const t = useTranslation();
  const review = idea.platform_review;
  const hints: string[] = [];
  if (idea.posting_tip) hints.push(idea.posting_tip);
  if (review?.cover_tip) hints.push(review.cover_tip);
  if (review?.sound_strategy) hints.push(`${t.soundPrefix}: ${review.sound_strategy}`);

  return (
    <section className="post-guidance panel panel-padding">
      <p className="meta section-eyebrow">{t.beforeYouPublish}</p>
      <div className="post-guidance-grid">
        <article className="guidance-card">
          <h3>{t.hints}</h3>
          {hints.length > 0 ? (
            <ul className="plain-list">
              {hints.map((hint) => (
                <li key={hint}>{hint}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">{t.guidanceDefaultHint}</p>
          )}
          {review?.posting_checklist.length ? (
            <>
              <p className="meta" style={{ marginTop: 14 }}>
                {t.checklist}
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
          <h3>{t.whatWorks}</h3>
          {review?.strengths.length ? (
            <ul className="plain-list">
              {review.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">{t.guidanceDefaultStrength}</p>
          )}
        </article>

        <article className="guidance-card">
          <h3>{t.beforeYouPost}</h3>
          {review?.improvements.length ? (
            <ul className="plain-list">
              {review.improvements.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="meta">{t.guidanceDefaultImprove}</p>
          )}
        </article>
      </div>
    </section>
  );
}
