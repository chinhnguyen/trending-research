import type { TranslationFn } from "../i18n/translations";

const ASPECT_RATIO_KEYS: Record<string, keyof TranslationFn> = {
  "1:1": "formatSquareFeed",
  "4:5": "formatPortraitFeed",
  "9:16": "formatReelsStory",
  "16:9": "formatLandscape",
};

export function aspectRatioLabel(ratio: string, t: TranslationFn): string {
  const key = ASPECT_RATIO_KEYS[ratio];
  return key ? String(t[key]) : ratio;
}

const POPULARITY_KEYS: Record<string, keyof TranslationFn> = {
  rising: "popularityRising",
  peak: "popularityPeak",
  steady: "popularitySteady",
  niche: "popularityNiche",
};

export function popularityLabel(value: string, t: TranslationFn): string {
  const key = POPULARITY_KEYS[value.toLowerCase()];
  return key ? String(t[key]) : value;
}
