import type { PostFormat, SocialPlatform } from "../types";

export type PostSetup = {
  platform: SocialPlatform;
  postFormat: PostFormat;
};

export const POST_PLATFORMS: {
  id: SocialPlatform;
  label: string;
  description: string;
}[] = [
  {
    id: "instagram",
    label: "Instagram",
    description: "Feed posts, carousels, and Reels.",
  },
  {
    id: "tiktok",
    label: "TikTok",
    description: "Short vertical clips for discovery.",
  },
];

export const POST_TYPES: {
  id: PostFormat;
  label: string;
  description: string;
}[] = [
  {
    id: "image",
    label: "Text with images",
    description: "Caption, hashtags, and a salon still image.",
  },
  {
    id: "video",
    label: "Video",
    description: "Short vertical clip with hook and caption.",
  },
];

export function postSetupLabel(setup: PostSetup) {
  const platform = POST_PLATFORMS.find((item) => item.id === setup.platform)?.label ?? setup.platform;
  const type = POST_TYPES.find((item) => item.id === setup.postFormat)?.label ?? setup.postFormat;
  return `${platform} · ${type}`;
}

export function PostSetupPicker({
  value,
  onChange,
  disabled = false,
  lockFormat = false,
  compact = false,
}: {
  value: PostSetup;
  onChange: (next: PostSetup) => void;
  disabled?: boolean;
  lockFormat?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={`post-setup-picker${compact ? " compact" : ""}`}>
      <fieldset className="post-setup-field" disabled={disabled}>
        <legend>Platform</legend>
        <div className={`platform-picker${compact ? " compact" : ""}`}>
          {POST_PLATFORMS.map((option) => (
            <button
              key={option.id}
              type="button"
              className={value.platform === option.id ? "platform-card active" : "platform-card"}
              onClick={() => onChange({ ...value, platform: option.id })}
              aria-pressed={value.platform === option.id}
            >
              <strong>{option.label}</strong>
              {compact ? null : <p>{option.description}</p>}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="post-setup-field" disabled={disabled || lockFormat}>
        <legend>
          Post type
          {lockFormat ? <span className="post-setup-locked">Locked for this post</span> : null}
        </legend>
        <div className={`platform-picker${compact ? " compact" : ""}`}>
          {POST_TYPES.map((option) => (
            <button
              key={option.id}
              type="button"
              className={value.postFormat === option.id ? "platform-card active" : "platform-card"}
              onClick={() => onChange({ ...value, postFormat: option.id })}
              aria-pressed={value.postFormat === option.id}
              disabled={lockFormat}
            >
              <strong>{option.label}</strong>
              {compact ? null : <p>{option.description}</p>}
            </button>
          ))}
        </div>
      </fieldset>
    </div>
  );
}
