import { PostGuidancePanel } from "./PostGuidancePanel";
import { PostOptionsList, type MediaPromptTarget, type OptionDraft } from "./PostOptionsList";
import { TrendReferencePanel } from "./TrendReferencePanel";
import type { RegenerateField } from "../api";
import type { TrendSignal, ContentIdea, MediaJob as MediaJobType, PostFormat, SocialPlatform } from "../types";
import type { PostSetup } from "./PostSetupPicker";

export function PostComposerView({
  trend,
  evidenceSummary,
  whyNow,
  idea,
  mediaJobs,
  contentIdeaId,
  onGenerate,
  generating,
  pendingSetup,
  mediaGenerating,
  promptBusyKey,
  regeneratingField,
  onAcceptPrompt,
  onRegeneratePrompt,
}: {
  trend: TrendSignal;
  evidenceSummary?: string;
  whyNow?: string;
  idea: ContentIdea | null;
  mediaJobs?: MediaJobType[];
  contentIdeaId?: string | null;
  onGenerate?: (setup: PostSetup) => void;
  generating?: boolean;
  pendingSetup?: PostSetup | null;
  mediaGenerating?: boolean;
  promptBusyKey?: string | null;
  regeneratingField?: RegenerateField | null;
  onAcceptPrompt?: (target: MediaPromptTarget, draft: OptionDraft) => void | Promise<void>;
  onRegeneratePrompt?: (target: MediaPromptTarget, field: RegenerateField) => void | Promise<void>;
}) {
  const hasOptions =
    (idea?.image_recommendations.length ?? 0) + (idea?.video_recommendations.length ?? 0) > 0;

  return (
    <div className="post-composer">
      <TrendReferencePanel trend={trend} evidenceSummary={evidenceSummary} whyNow={whyNow} />
      {idea && hasOptions ? <PostGuidancePanel idea={idea} /> : null}
      <PostOptionsList
        idea={idea}
        contentIdeaId={contentIdeaId}
        mediaJobs={mediaJobs}
        onGenerate={onGenerate}
        generating={generating}
        pendingSetup={pendingSetup}
        mediaGenerating={mediaGenerating}
        promptBusyKey={promptBusyKey}
        regeneratingField={regeneratingField}
        onAcceptPrompt={onAcceptPrompt}
        onRegeneratePrompt={onRegeneratePrompt}
      />
    </div>
  );
}
