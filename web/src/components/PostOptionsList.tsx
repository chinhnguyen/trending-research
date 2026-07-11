import { useState } from "react";
import type { RegenerateField } from "../api";
import type { ContentIdea, MediaJob, PostFormat, SocialPlatform } from "../types";
import { copyPostBundle, formatHashtags, formatLabel } from "../utils/postFormat";
import { InstagramShareButton } from "./InstagramShareButton";
import { MediaPromptReview, type OptionDraft } from "./MediaPromptReview";
import { findActiveJobForOption, OptionMediaProgress } from "./OptionMediaProgress";
import { PostSetupPicker, postSetupLabel, POST_PLATFORMS, POST_TYPES, type PostSetup } from "./PostSetupPicker";

export type { OptionDraft };

export type PostOption = {
  id: string;
  kind: "image" | "video";
  platform: SocialPlatform;
  postFormat: PostFormat;
  sequence: number;
  title: string;
  caption: string;
  hashtags: string[];
  hook?: string | null;
  imageUrl?: string | null;
  videoUrl?: string | null;
  formatLabel?: string;
  mediaPrompt?: string;
  generationStatus: string;
  generationError?: string | null;
};

export type MediaPromptTarget = {
  contentIdeaId: string;
  kind: "image" | "video";
  sequence: number;
};

function setupLabelForOption(platform: SocialPlatform, postFormat: PostFormat) {
  const platformLabel = POST_PLATFORMS.find((item) => item.id === platform)?.label ?? platform;
  const typeLabel = POST_TYPES.find((item) => item.id === postFormat)?.label ?? postFormat;
  return `${platformLabel} · ${typeLabel}`;
}

function optionDraft(option: PostOption): OptionDraft {
  return {
    hook: option.hook ?? "",
    caption: option.caption,
    hashtagsText: formatHashtags(option.hashtags),
    prompt: option.mediaPrompt ?? "",
  };
}

function buildPostOptions(idea: ContentIdea | null): PostOption[] {
  if (!idea) return [];

  const review = idea.platform_review;
  const fallbackCaption =
    review?.caption ?? idea.captions[0]?.caption ?? "Share your latest salon work for this trend.";
  const fallbackHashtags = review?.hashtags.length ? review.hashtags : idea.hashtags;
  const fallbackHook = review?.hook ?? null;
  const fallbackPlatform = idea.platform;

  const options: PostOption[] = [];

  idea.image_recommendations.forEach((image, index) => {
    const platform = image.platform ?? fallbackPlatform;
    options.push({
      id: `image-${image.sequence ?? index}-${index}`,
      kind: "image",
      platform,
      postFormat: "image",
      sequence: image.sequence ?? index + 1,
      title: image.label || `Post option ${index + 1}`,
      caption: image.caption ?? fallbackCaption,
      hashtags: image.hashtags.length > 0 ? image.hashtags : fallbackHashtags,
      hook: image.hook ?? fallbackHook,
      imageUrl: image.generated_url,
      formatLabel: formatLabel(image.aspect_ratio),
      mediaPrompt: image.prompt,
      generationStatus: image.generation_status,
      generationError: image.generation_error,
    });
  });

  idea.video_recommendations.forEach((video, index) => {
    const platform = video.platform ?? fallbackPlatform;
    options.push({
      id: `video-${video.sequence ?? index}-${index}`,
      kind: "video",
      platform,
      postFormat: "video",
      sequence: video.sequence ?? index + 1,
      title: video.label || `Video option ${index + 1}`,
      caption: video.caption ?? fallbackCaption,
      hashtags: video.hashtags.length > 0 ? video.hashtags : fallbackHashtags,
      hook: video.hook ?? fallbackHook,
      videoUrl: video.generated_url,
      formatLabel: formatLabel(video.aspect_ratio),
      mediaPrompt: video.prompt,
      generationStatus: video.generation_status,
      generationError: video.generation_error,
    });
  });

  return options.sort((left, right) => left.sequence - right.sequence);
}

function isMediaGenerating(options: PostOption[], mediaJobs?: MediaJob[]) {
  const jobActive = mediaJobs?.some(
    (job) => job.status === "queued" || job.status === "generating_media",
  );
  const optionActive = options.some((option) => option.generationStatus === "generating");
  return Boolean(jobActive || optionActive);
}

function MediaPreview({
  option,
  activeJob,
  accepting = false,
}: {
  option: PostOption;
  activeJob?: MediaJob;
  accepting?: boolean;
}) {
  const isGenerating =
    accepting ||
    option.generationStatus === "generating" ||
    activeJob?.status === "queued" ||
    activeJob?.status === "generating_media";

  if (option.videoUrl && !isGenerating) {
    return <video src={option.videoUrl} controls playsInline preload="metadata" />;
  }
  if (option.imageUrl && !isGenerating) {
    return <img src={option.imageUrl} alt={option.title} loading="lazy" />;
  }
  if (isGenerating) {
    return (
      <div className="media-preview-generating">
        {activeJob ? <OptionMediaProgress job={activeJob} /> : <p className="meta">Generating…</p>}
      </div>
    );
  }
  return (
    <div className="media-preview-empty">
      <p className="meta">{option.formatLabel ?? (option.kind === "video" ? "Video" : "Image")}</p>
      {option.generationError ? <p className="error-text">{option.generationError}</p> : null}
      <p>Preview will appear here after you accept.</p>
    </div>
  );
}

export function PostOptionsList({
  idea,
  contentIdeaId,
  mediaJobs,
  onGenerate,
  generating,
  mediaGenerating,
  promptBusyKey,
  regeneratingField,
  onAcceptPrompt,
  onRegeneratePrompt,
}: {
  idea: ContentIdea | null;
  contentIdeaId?: string | null;
  mediaJobs?: MediaJob[];
  onGenerate?: (setup: PostSetup) => void;
  generating?: boolean;
  mediaGenerating?: boolean;
  promptBusyKey?: string | null;
  regeneratingField?: RegenerateField | null;
  onAcceptPrompt?: (target: MediaPromptTarget, draft: OptionDraft) => void | Promise<void>;
  onRegeneratePrompt?: (target: MediaPromptTarget, field: RegenerateField) => void | Promise<void>;
}) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [nextSetup, setNextSetup] = useState<PostSetup>({ platform: "instagram", postFormat: "image" });
  const options = buildPostOptions(idea);
  const locked = mediaGenerating ?? isMediaGenerating(options, mediaJobs);

  async function handleCopy(option: PostOption) {
    const caption = option.hook ? `${option.hook}\n\n${option.caption}` : option.caption;
    await copyPostBundle(caption, option.hashtags);
    setCopiedId(option.id);
    window.setTimeout(() => setCopiedId(null), 2000);
  }

  function targetFor(option: PostOption): MediaPromptTarget | null {
    if (!contentIdeaId) return null;
    return { contentIdeaId, kind: option.kind, sequence: option.sequence };
  }

  function busyKeyFor(option: PostOption) {
    return `${option.kind}-${option.sequence}`;
  }

  return (
    <section className={`post-options panel panel-padding${locked ? " post-options-locked" : ""}`}>
      <div className="post-options-header">
        <div>
          <p className="meta section-eyebrow">{options.length ? "Generated options" : "Post composer"}</p>
          <h2 className="section-title" style={{ margin: 0 }}>
            {options.length ? "Your post options" : "Generate your first option"}
          </h2>
          <p className="meta">
            {locked
              ? "Media is generating — all options are paused until it finishes."
              : "Review each image or video prompt before generation. Mix platforms and formats freely in one list."}
          </p>
        </div>
      </div>

      <div className="post-options-list">
        {options.length === 0 ? (
          <div className="post-option-empty panel panel-padding">
            <p className="meta">No options yet. Choose a setup below and generate your first post.</p>
          </div>
        ) : null}

        {options.map((option, index) => {
          const target = targetFor(option);
          const activeJob =
            contentIdeaId && target
              ? findActiveJobForOption(mediaJobs, contentIdeaId, option.kind, option.sequence)
              : undefined;
          const promptBusy = promptBusyKey === busyKeyFor(option);
          const hasMedia = Boolean(option.imageUrl || option.videoUrl);
          const isThisGenerating =
            option.generationStatus === "generating" ||
            activeJob?.status === "queued" ||
            activeJob?.status === "generating_media";
          const lockedByOther = locked && !isThisGenerating;
          const showComposer = Boolean(target && onAcceptPrompt && !lockedByOther);

          return (
            <article
              key={option.id}
              className={`post-option-card${lockedByOther ? " is-locked" : ""}`}
              aria-disabled={lockedByOther || undefined}
            >
              <div className="post-option-header">
                <div>
                  <span className="badge badge-accent">Option {index + 1}</span>
                  <span className="badge">{setupLabelForOption(option.platform, option.postFormat)}</span>
                  {option.formatLabel ? <span className="badge">{option.formatLabel}</span> : null}
                </div>
                {option.platform === "instagram" ? (
                  <InstagramShareButton option={option} disabled={lockedByOther || !hasMedia} />
                ) : (
                  <button
                    type="button"
                    className="button button-primary button-compact"
                    onClick={() => handleCopy(option)}
                    disabled={lockedByOther || !hasMedia}
                  >
                    {copiedId === option.id ? "Copied" : "Copy for posting"}
                  </button>
                )}
              </div>

              {showComposer ? (
                <div className="post-option-body">
                  <MediaPromptReview
                    draft={optionDraft(option)}
                    kind={option.kind}
                    disabled={generating}
                    mediaBusy={isThisGenerating}
                    accepting={promptBusy && !regeneratingField}
                    regeneratingField={promptBusy ? regeneratingField : null}
                    mediaPreview={
                      <MediaPreview
                        option={option}
                        activeJob={activeJob}
                        accepting={promptBusy && !regeneratingField}
                      />
                    }
                    onRegenerate={(field) => {
                      if (target) void onRegeneratePrompt?.(target, field);
                    }}
                    onAccept={(draft) => {
                      if (target) void onAcceptPrompt?.(target, draft);
                    }}
                  />
                </div>
              ) : null}
            </article>
          );
        })}
      </div>

      {onGenerate ? (
        <div className="post-generate-more panel panel-padding">
          <div className="post-generate-more-copy">
            <p className="meta section-eyebrow">Generate</p>
            <h3 className="section-title" style={{ margin: "0 0 8px" }}>
              Add another option
            </h3>
            <p className="meta">Choose platform and post type for the next output. You can mix formats freely.</p>
          </div>
          <PostSetupPicker value={nextSetup} onChange={setNextSetup} disabled={generating || locked} compact />
          <div className="button-row">
            <button
              type="button"
              className="button button-primary"
              onClick={() => onGenerate(nextSetup)}
              disabled={generating || locked}
            >
              {generating ? "Generating…" : `Generate ${postSetupLabel(nextSetup)}`}
            </button>
          </div>
        </div>
      ) : null}

      {idea?.video_recommendation && idea.video_recommendations.length === 0 ? (
        <div className="video-brief panel panel-padding" style={{ marginTop: 16 }}>
          <h3 className="section-title">Video storyboard</h3>
          <p>{idea.video_recommendation.hook}</p>
          <div className="video-scene-list">
            {idea.video_recommendation.scenes.map((scene) => (
              <article key={scene.scene_number} className="video-scene-card">
                {scene.generated_frame_url ? (
                  <img src={scene.generated_frame_url} alt={`Scene ${scene.scene_number}`} loading="lazy" />
                ) : null}
                <div>
                  <strong>Scene {scene.scene_number}</strong>
                  <p>{scene.visual_prompt}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
