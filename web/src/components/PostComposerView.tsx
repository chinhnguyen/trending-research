import { Link } from "react-router-dom";
import type { ContentIdea, SocialPlatform, TrendSignal } from "../types";
import { PostGuidancePanel } from "./PostGuidancePanel";
import { PostOptionsList } from "./PostOptionsList";
import { TrendReferencePanel } from "./TrendReferencePanel";

const PLATFORM_LABELS: Record<SocialPlatform, string> = {
  instagram: "Instagram",
  tiktok: "TikTok",
};

export function PostComposerView({
  trend,
  evidenceSummary,
  whyNow,
  idea,
  briefId,
  briefItemId,
  onGenerateMore,
  generatingMore,
}: {
  trend: TrendSignal;
  evidenceSummary?: string;
  whyNow?: string;
  idea: ContentIdea;
  briefId?: string;
  briefItemId?: string;
  onGenerateMore?: () => void;
  generatingMore?: boolean;
}) {
  const review = idea.platform_review;

  return (
    <div className="post-composer">
      <div className="badges" style={{ marginBottom: 4 }}>
        <span className="badge badge-accent">{PLATFORM_LABELS[idea.platform]}</span>
        {review ? <span className="badge">{review.content_format.replace(/_/g, " ")}</span> : null}
      </div>

      <TrendReferencePanel trend={trend} evidenceSummary={evidenceSummary} whyNow={whyNow} />
      <PostGuidancePanel idea={idea} />
      <PostOptionsList idea={idea} onGenerateMore={onGenerateMore} generatingMore={generatingMore} />

      {briefId && briefItemId ? (
        <div className="button-row">
          <Link
            to={`/ideas/${briefItemId}?brief=${briefId}&platform=${idea.platform}`}
            className="nav-link"
          >
            Open full regenerate page
          </Link>
        </div>
      ) : null}
    </div>
  );
}
