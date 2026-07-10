import { useEffect, useState } from "react";
import type { ContentIdea, MediaJob } from "../types";
import { copyPostBundle, formatHashtags, formatLabel } from "../utils/postFormat";
import { InstagramShareButton } from "./InstagramShareButton";
import { findActiveJobForIdea, lastPendingOptionIndex, OptionMediaProgress } from "./OptionMediaProgress";
import { PostSetupPicker, postSetupLabel, type PostSetup } from "./PostSetupPicker";

export type PostOption = {
  id: string;
  title: string;
  caption: string;
  hashtags: string[];
  hook?: string | null;
  imageUrl?: string | null;
  videoUrl?: string | null;
  formatLabel?: string;
  mediaPrompt?: string;
};

function buildPostOptions(idea: ContentIdea): PostOption[] {
  const review = idea.platform_review;
  const fallbackCaption =
    review?.caption ?? idea.captions[0]?.caption ?? "Share your latest salon work for this trend.";
  const fallbackHashtags = review?.hashtags.length ? review.hashtags : idea.hashtags;
  const fallbackHook = review?.hook ?? null;

  if (idea.post_format === "video") {
    if (idea.video_recommendations.length === 0) {
      return [
        {
          id: "video-main",
          title: "Video script",
          caption: fallbackCaption,
          hashtags: fallbackHashtags,
          hook: fallbackHook,
        },
      ];
    }

    return idea.video_recommendations.map((video, index) => ({
      id: `video-${index}`,
      title: video.label || `Video option ${index + 1}`,
      caption: video.caption ?? fallbackCaption,
      hashtags: video.hashtags.length > 0 ? video.hashtags : fallbackHashtags,
      hook: video.hook ?? fallbackHook,
      videoUrl: video.generated_url,
      formatLabel: formatLabel(video.aspect_ratio),
      mediaPrompt: video.prompt,
    }));
  }

  const options: PostOption[] = [];
  if (idea.image_recommendations.length === 0) {
    options.push({
      id: "text-main",
      title: "Caption only",
      caption: fallbackCaption,
      hashtags: fallbackHashtags,
      hook: fallbackHook,
    });
  } else {
    idea.image_recommendations.forEach((image, index) => {
      options.push({
        id: `post-${index}`,
        title: image.label || `Post option ${index + 1}`,
        caption: image.caption ?? fallbackCaption,
        hashtags: image.hashtags.length > 0 ? image.hashtags : fallbackHashtags,
        hook: image.hook ?? fallbackHook,
        imageUrl: image.generated_url,
        formatLabel: formatLabel(image.aspect_ratio),
        mediaPrompt: image.prompt,
      });
    });
  }

  return options;
}

export function PostOptionsList({
  idea,
  mediaJobs,
  onGenerateMore,
  generatingMore,
}: {
  idea: ContentIdea;
  mediaJobs?: MediaJob[];
  onGenerateMore?: (setup: PostSetup) => void;
  generatingMore?: boolean;
}) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [nextSetup, setNextSetup] = useState<PostSetup>({
    platform: idea.platform,
    postFormat: idea.post_format,
  });
  const options = buildPostOptions(idea);
  const isInstagram = idea.platform === "instagram";
  const isVideo = idea.post_format === "video";
  const activeJob = findActiveJobForIdea(mediaJobs, idea.id);
  const pendingOptionIndex = lastPendingOptionIndex(options);

  useEffect(() => {
    setNextSetup({ platform: idea.platform, postFormat: idea.post_format });
  }, [idea.id, idea.platform, idea.post_format]);

  async function handleCopy(option: PostOption) {
    const caption = option.hook ? `${option.hook}\n\n${option.caption}` : option.caption;
    await copyPostBundle(caption, option.hashtags);
    setCopiedId(option.id);
    window.setTimeout(() => setCopiedId(null), 2000);
  }

  return (
    <section className="post-options panel panel-padding">
      <div className="post-options-header">
        <div>
          <p className="meta section-eyebrow">Ready to post</p>
          <h2 className="section-title" style={{ margin: 0 }}>
            Pick a version
          </h2>
          <p className="meta">
            {isVideo
              ? "Each option is a short vertical video with its own hook and caption."
              : "Each option has its own hook, caption, and image."}{" "}
            {isInstagram
              ? "Post on Instagram copies your caption, saves the media, and opens Instagram for you."
              : "Generate more to add one new variant at a time (up to 6)."}
          </p>
        </div>
      </div>

      {onGenerateMore ? (
        <div className="post-generate-more panel panel-padding">
          <div className="post-generate-more-copy">
            <p className="meta section-eyebrow">Add another option</p>
            <h3 className="section-title" style={{ margin: "0 0 8px" }}>
              Choose platform for the next variant
            </h3>
            <p className="meta">Post type stays the same for this post.</p>
          </div>
          <PostSetupPicker
            value={nextSetup}
            onChange={setNextSetup}
            disabled={generatingMore}
            lockFormat
            compact
          />
          <div className="button-row">
            <button
              type="button"
              className="button button-secondary"
              onClick={() => onGenerateMore(nextSetup)}
              disabled={generatingMore}
            >
              {generatingMore ? "Generating…" : `Generate ${postSetupLabel(nextSetup)}`}
            </button>
          </div>
        </div>
      ) : null}

      <div className="post-options-list">
        {options.map((option, index) => (
          <article key={option.id} className="post-option-card">
            <div className="post-option-header">
              <div>
                <span className="badge badge-accent">Option {index + 1}</span>
                {option.formatLabel ? <span className="badge">{option.formatLabel}</span> : null}
                {isVideo ? <span className="badge">Short video</span> : null}
              </div>
              {isInstagram ? (
                <InstagramShareButton option={option} disabled={index === pendingOptionIndex && !!activeJob} />
              ) : (
                <button
                  type="button"
                  className="button button-primary button-compact"
                  onClick={() => handleCopy(option)}
                  disabled={index === pendingOptionIndex && !!activeJob}
                >
                  {copiedId === option.id ? "Copied" : "Copy for posting"}
                </button>
              )}
            </div>

            <div className="post-option-body">
              <div className="post-option-text">
                {option.hook ? (
                  <div className="post-hook">
                    <p className="meta">Hook</p>
                    <p>{option.hook}</p>
                  </div>
                ) : null}
                <div>
                  <p className="meta">Caption</p>
                  <p className="post-caption">{option.caption}</p>
                </div>
                {option.hashtags.length > 0 ? (
                  <div>
                    <p className="meta">Hashtags</p>
                    <p className="post-hashtags">{formatHashtags(option.hashtags)}</p>
                  </div>
                ) : null}
              </div>

              {option.videoUrl || option.imageUrl || option.mediaPrompt ? (
                <div className="post-option-media">
                  {option.videoUrl ? (
                    <video src={option.videoUrl} controls playsInline preload="metadata" />
                  ) : option.imageUrl ? (
                    <img src={option.imageUrl} alt={option.title} loading="lazy" />
                  ) : index === pendingOptionIndex && activeJob ? (
                    <div className="media-card-placeholder generating">
                      <OptionMediaProgress job={activeJob} />
                      {option.mediaPrompt ? <p className="media-prompt-preview">{option.mediaPrompt}</p> : null}
                    </div>
                  ) : (
                    <div className="media-card-placeholder">
                      <p className="meta">{option.formatLabel ?? (isVideo ? "Video" : "Image")}</p>
                      <p>{option.mediaPrompt}</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      {idea.video_recommendation && idea.video_recommendations.length === 0 ? (
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
