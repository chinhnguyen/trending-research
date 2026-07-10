import type { ContentIdea, MediaJob, PostFormat, SocialPlatform, TrendSignal } from "../types";
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
  mediaJobs,
  onGenerateMore,
  generatingMore,
}: {
  trend: TrendSignal;
  evidenceSummary?: string;
  whyNow?: string;
  idea: ContentIdea;
  mediaJobs?: MediaJob[];
  onGenerateMore?: (setup: { platform: SocialPlatform; postFormat: PostFormat }) => void;
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
      <PostOptionsList
        idea={idea}
        mediaJobs={mediaJobs}
        onGenerateMore={onGenerateMore}
        generatingMore={generatingMore}
      />
    </div>
  );
}
