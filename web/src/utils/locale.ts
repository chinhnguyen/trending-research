import type { BriefCaption } from "../types";

export function pickCaption(captions: BriefCaption[], preferredLocale: string): string | undefined {
  const preferred = preferredLocale.toLowerCase().split("-")[0];
  const match = captions.find((item) => item.locale.toLowerCase().startsWith(preferred));
  if (match) return match.caption;
  const english = captions.find((item) => item.locale.toLowerCase().startsWith("en"));
  return english?.caption ?? captions[0]?.caption;
}
