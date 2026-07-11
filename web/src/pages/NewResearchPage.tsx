import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { runNeutralResearch, runPersonalizedResearch } from "../api";
import { useLocale, useTranslation } from "../i18n/LocaleProvider";
import type { UserPreferences } from "../types";

const defaultPreferences: UserPreferences = {
  display_name: "Maya",
  favorite_colors: ["cherry red", "milky white", "soft gold"],
  avoided_colors: ["neon green", "harsh black"],
  preferred_shapes: ["almond", "coffin"],
  preferred_lengths: ["medium", "long"],
  preferred_finishes: ["glossy", "chrome"],
  style_keywords: ["clean girl", "minimalist", "soft glam"],
  occasion: "everyday office with weekend events",
  budget: "salon",
  notes: "Likes subtle nail art, not busy 3D charms.",
};

const defaultResearchTime = new Intl.DateTimeFormat("en-US", {
  month: "long",
  year: "numeric",
}).format(new Date());

export function NewResearchPage() {
  const navigate = useNavigate();
  const { preferredLocale } = useLocale();
  const t = useTranslation();
  const [mode, setMode] = useState<"neutral" | "personalized">("neutral");
  const [provider, setProvider] = useState("openai");
  const [region, setRegion] = useState("global");
  const [researchTime, setResearchTime] = useState(defaultResearchTime);
  const [webSearch, setWebSearch] = useState(true);
  const [displayName, setDisplayName] = useState(defaultPreferences.display_name);
  const [favoriteColors, setFavoriteColors] = useState(
    defaultPreferences.favorite_colors.join(", "),
  );
  const [styleKeywords, setStyleKeywords] = useState(
    defaultPreferences.style_keywords.join(", "),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const base = {
      category: "nails" as const,
      region,
      research_time: researchTime,
      provider,
      web_search: webSearch,
      preferred_locale: preferredLocale,
    };

    try {
      const result =
        mode === "neutral"
          ? await runNeutralResearch(base)
          : await runPersonalizedResearch({
              ...base,
              preferences: {
                ...defaultPreferences,
                display_name: displayName,
                favorite_colors: favoriteColors.split(",").map((v) => v.trim()).filter(Boolean),
                style_keywords: styleKeywords.split(",").map((v) => v.trim()).filter(Boolean),
              },
            });
      navigate(`/reports/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.researchFailed);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="hero">
        <h1>{t.newResearchTitle}</h1>
        <p>{t.newResearchSubtitle}</p>
      </section>

      <form className="panel panel-padding form-grid" onSubmit={handleSubmit}>
        <div className="inline-fields">
          <div className="field">
            <label htmlFor="mode">Mode</label>
            <select id="mode" value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
              <option value="neutral">{t.modeNeutral}</option>
              <option value="personalized">{t.modePersonalized}</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="provider">{t.provider}</label>
            <select id="provider" value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
        </div>

        <div className="inline-fields">
          <div className="field">
            <label htmlFor="region">{t.region}</label>
            <input id="region" value={region} onChange={(e) => setRegion(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="research-time">{t.researchTime}</label>
            <input
              id="research-time"
              value={researchTime}
              onChange={(e) => setResearchTime(e.target.value)}
              placeholder="July 2026"
            />
          </div>
        </div>

        <div className="inline-fields">
          <div className="field">
            <label htmlFor="web-search">{t.webSearch}</label>
            <select
              id="web-search"
              value={webSearch ? "on" : "off"}
              onChange={(e) => setWebSearch(e.target.value === "on")}
            >
              <option value="on">Enabled</option>
              <option value="off">Disabled</option>
            </select>
          </div>
        </div>

        {mode === "personalized" ? (
          <>
            <div className="field">
              <label htmlFor="display-name">{t.displayName}</label>
              <input
                id="display-name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="favorite-colors">{t.favoriteColors}</label>
              <input
                id="favorite-colors"
                value={favoriteColors}
                onChange={(e) => setFavoriteColors(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="style-keywords">{t.styleKeywords}</label>
              <input
                id="style-keywords"
                value={styleKeywords}
                onChange={(e) => setStyleKeywords(e.target.value)}
              />
            </div>
          </>
        ) : null}

        {error ? <div className="error">{error}</div> : null}

        <button className="button button-primary" type="submit" disabled={loading}>
          {loading ? t.running : t.runResearch}
        </button>
      </form>
    </>
  );
}
