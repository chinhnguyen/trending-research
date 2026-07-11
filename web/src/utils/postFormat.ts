export const FORMAT_LABELS: Record<string, string> = {
  "1:1": "Square feed",
  "4:5": "Portrait feed",
  "9:16": "Reels / Story",
  "16:9": "Landscape",
};

export function formatLabel(aspectRatio: string): string {
  return FORMAT_LABELS[aspectRatio] ?? aspectRatio;
}

export function formatHashtags(tags: string[]): string {
  return tags.join(" ");
}

export function parseHashtags(text: string): string[] {
  return text
    .split(/[\n,]+/)
    .map((tag) => tag.trim())
    .filter(Boolean)
    .map((tag) => (tag.startsWith("#") ? tag : `#${tag}`));
}

export async function copyPostBundle(caption: string, hashtags: string[]): Promise<void> {
  const text = hashtags.length > 0 ? `${caption}\n\n${formatHashtags(hashtags)}` : caption;
  await navigator.clipboard.writeText(text);
}
