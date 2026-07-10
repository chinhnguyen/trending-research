import { copyPostBundle } from "./postFormat";

const INSTAGRAM_CREATE_URL = "https://www.instagram.com/create/select/";

export type InstagramShareResult = {
  mode: "native_share" | "browser_flow";
  captionCopied: boolean;
  mediaDownloaded: boolean;
};

function buildPostCaption(hook: string | null | undefined, caption: string, hashtags: string[]): string {
  const body = hook ? `${hook}\n\n${caption}` : caption;
  if (hashtags.length === 0) return body;
  const tags = hashtags
    .map((tag) => (tag.startsWith("#") ? tag : `#${tag.replace(/^#/, "")}`))
    .join(" ");
  return `${body}\n\n${tags}`;
}

async function fetchMediaFile(mediaUrl: string, filename: string): Promise<File | null> {
  try {
    const response = await fetch(mediaUrl, { credentials: "include" });
    if (!response.ok) return null;
    const blob = await response.blob();
    const type = blob.type || (filename.endsWith(".mp4") ? "video/mp4" : "image/png");
    return new File([blob], filename, { type });
  } catch {
    return null;
  }
}

function downloadFile(file: File) {
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = file.name;
  link.click();
  URL.revokeObjectURL(url);
}

function openInstagramCreate() {
  window.open(INSTAGRAM_CREATE_URL, "_blank", "noopener,noreferrer");
}

export async function shareToInstagram({
  hook,
  caption,
  hashtags,
  imageUrl,
  mediaUrl,
  filename = "willbe-post.png",
}: {
  hook?: string | null;
  caption: string;
  hashtags: string[];
  imageUrl?: string | null;
  mediaUrl?: string | null;
  filename?: string;
}): Promise<InstagramShareResult> {
  const resolvedMediaUrl = mediaUrl ?? imageUrl;
  const postCaption = buildPostCaption(hook, caption, hashtags);
  await copyPostBundle(postCaption, []);
  const result: InstagramShareResult = {
    mode: "browser_flow",
    captionCopied: true,
    mediaDownloaded: false,
  };

  if (!resolvedMediaUrl) {
    openInstagramCreate();
    return result;
  }

  const mediaFile = await fetchMediaFile(resolvedMediaUrl, filename);
  if (!mediaFile) {
    openInstagramCreate();
    return result;
  }

  if (typeof navigator.share === "function" && typeof navigator.canShare === "function") {
    const shareData = { files: [mediaFile], text: postCaption };
    if (navigator.canShare(shareData)) {
      try {
        await navigator.share(shareData);
        return { mode: "native_share", captionCopied: true, mediaDownloaded: false };
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          throw error;
        }
      }
    }
  }

  downloadFile(mediaFile);
  result.mediaDownloaded = true;
  openInstagramCreate();
  return result;
}
