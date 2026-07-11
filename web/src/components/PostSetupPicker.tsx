import type { PostFormat, SocialPlatform } from "../types";
import { useTranslation } from "../i18n/LocaleProvider";

export type PostSetup = {
  platform: SocialPlatform;
  postFormat: PostFormat;
};

export function usePostPlatforms() {
  const t = useTranslation();
  return [
    { id: "instagram" as const, label: t.instagram, description: t.instagramDesc },
    { id: "tiktok" as const, label: t.tiktok, description: t.tiktokDesc },
  ];
}

export function usePostTypes() {
  const t = useTranslation();
  return [
    { id: "image" as const, label: t.textWithImages, description: t.textWithImagesDesc },
    { id: "video" as const, label: t.videoPost, description: t.videoPostDesc },
  ];
}

export function usePostSetupLabel(setup: PostSetup) {
  const platforms = usePostPlatforms();
  const postTypes = usePostTypes();
  const platform = platforms.find((item) => item.id === setup.platform)?.label ?? setup.platform;
  const type = postTypes.find((item) => item.id === setup.postFormat)?.label ?? setup.postFormat;
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
  const t = useTranslation();
  const platforms = usePostPlatforms();
  const postTypes = usePostTypes();

  return (
    <div className={`post-setup-picker${compact ? " compact" : ""}`}>
      <fieldset className="post-setup-field" disabled={disabled}>
        <legend>{t.platformLegend}</legend>
        <div className={`platform-picker${compact ? " compact" : ""}`}>
          {platforms.map((option) => (
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
          {t.postTypeLegend}
          {lockFormat ? <span className="post-setup-locked">{t.lockedForPost}</span> : null}
        </legend>
        <div className={`platform-picker${compact ? " compact" : ""}`}>
          {postTypes.map((option) => (
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
