import { useState } from "react";
import { useTranslation } from "../i18n/LocaleProvider";
import { shareToInstagram, type InstagramShareResult } from "../utils/instagramShare";
import type { PostOption } from "./PostOptionsList";

type ButtonState = "idle" | "sharing" | "done" | "error";

function shareHint(
  result: InstagramShareResult | null,
  hasMedia: boolean,
  isVideo: boolean,
  t: ReturnType<typeof useTranslation>,
): string | null {
  if (!result) return null;
  if (result.mode === "native_share") {
    return t.instagramShareNative;
  }
  if (hasMedia && result.mediaDownloaded) {
    return isVideo ? t.instagramShareVideoSaved : t.instagramShareImageSaved;
  }
  if (hasMedia) {
    return t.instagramShareCaptionOnly;
  }
  return t.instagramShareCaptionPaste;
}

export function InstagramShareButton({ option, disabled }: { option: PostOption; disabled?: boolean }) {
  const t = useTranslation();
  const [state, setState] = useState<ButtonState>("idle");
  const [result, setResult] = useState<InstagramShareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mediaUrl = option.videoUrl ?? option.imageUrl;
  const isVideo = Boolean(option.videoUrl);
  const hint = shareHint(result, Boolean(mediaUrl), isVideo, t);

  async function handleShare() {
    setState("sharing");
    setError(null);
    setResult(null);
    try {
      const shareResult = await shareToInstagram({
        hook: option.hook,
        caption: option.caption,
        hashtags: option.hashtags,
        mediaUrl,
        filename: `${option.id}.${isVideo ? "mp4" : "png"}`,
      });
      setResult(shareResult);
      setState("done");
      window.setTimeout(() => {
        setState("idle");
        setResult(null);
      }, 8000);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setState("idle");
        return;
      }
      setError(err instanceof Error ? err.message : t.couldNotOpenInstagram);
      setState("error");
    }
  }

  const label =
    state === "sharing"
      ? t.openingInstagram
      : state === "done"
        ? t.readyInInstagram
        : t.postOnInstagram;

  return (
    <div className="instagram-action">
      <button
        type="button"
        className="button button-primary button-compact"
        onClick={handleShare}
        disabled={disabled || state === "sharing"}
        title={mediaUrl ? t.instagramShareTitleMedia : t.instagramShareTitleCaption}
      >
        {label}
      </button>
      {hint ? <p className="meta instagram-action-note">{hint}</p> : null}
      {error ? <p className="error-text instagram-action-note">{error}</p> : null}
    </div>
  );
}
