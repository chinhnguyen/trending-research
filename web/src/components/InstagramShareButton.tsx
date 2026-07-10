import { useState } from "react";
import { shareToInstagram, type InstagramShareResult } from "../utils/instagramShare";
import type { PostOption } from "./PostOptionsList";

type ButtonState = "idle" | "sharing" | "done" | "error";

function shareHint(result: InstagramShareResult | null, hasImage: boolean): string | null {
  if (!result) return null;
  if (result.mode === "native_share") {
    return "Shared to your device. Pick Instagram and finish the post there.";
  }
  if (hasImage && result.imageDownloaded) {
    return "Caption copied and image saved. In Instagram, upload the image and paste your caption.";
  }
  if (hasImage) {
    return "Caption copied. In Instagram, upload your image and paste the caption.";
  }
  return "Caption copied. Paste it into your new Instagram post.";
}

export function InstagramShareButton({ option }: { option: PostOption }) {
  const [state, setState] = useState<ButtonState>("idle");
  const [result, setResult] = useState<InstagramShareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const hasImage = Boolean(option.imageUrl);
  const hint = shareHint(result, hasImage);

  async function handleShare() {
    setState("sharing");
    setError(null);
    setResult(null);
    try {
      const shareResult = await shareToInstagram({
        hook: option.hook,
        caption: option.caption,
        hashtags: option.hashtags,
        imageUrl: option.imageUrl,
        filename: `${option.id}.png`,
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
      setError(err instanceof Error ? err.message : "Could not open Instagram");
      setState("error");
    }
  }

  const label =
    state === "sharing" ? "Opening Instagram…" : state === "done" ? "Ready in Instagram" : "Post on Instagram";

  return (
    <div className="instagram-action">
      <button
        type="button"
        className="button button-primary button-compact"
        onClick={handleShare}
        disabled={state === "sharing"}
        title={
          hasImage
            ? "Copy caption, save the image, and open Instagram"
            : "Copy caption and open Instagram"
        }
      >
        {label}
      </button>
      {hint ? <p className="meta instagram-action-note">{hint}</p> : null}
      {error ? <p className="error-text instagram-action-note">{error}</p> : null}
    </div>
  );
}
