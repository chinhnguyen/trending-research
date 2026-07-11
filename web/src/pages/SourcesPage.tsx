import { useEffect, useState } from "react";
import { getSources, resetSources, updateSources } from "../api";
import { useTranslation } from "../i18n/LocaleProvider";
import type { PreferredSource, PreferredSourcesConfig, TrendCategory } from "../types";

const CATEGORY_OPTIONS: TrendCategory[] = ["nails"];

function emptySource(): PreferredSource {
  return {
    name: "",
    domain: "",
    weight: 1,
    categories: ["nails"],
    enabled: true,
  };
}

export function SourcesPage() {
  const t = useTranslation();
  const [config, setConfig] = useState<PreferredSourcesConfig | null>(null);
  const [isDefault, setIsDefault] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    getSources()
      .then((response) => {
        setConfig(response.config);
        setIsDefault(response.is_default);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function updateSource(index: number, patch: Partial<PreferredSource>) {
    setConfig((current) => {
      if (!current) return current;
      const sources = current.sources.map((source, i) =>
        i === index ? { ...source, ...patch } : source,
      );
      return { ...current, sources };
    });
    setSavedMessage(null);
  }

  function toggleCategory(index: number, category: TrendCategory) {
    setConfig((current) => {
      if (!current) return current;
      const sources = current.sources.map((source, i) => {
        if (i !== index) return source;
        const hasCategory = source.categories.includes(category);
        const categories = hasCategory
          ? source.categories.filter((item) => item !== category)
          : [...source.categories, category];
        return { ...source, categories };
      });
      return { ...current, sources };
    });
    setSavedMessage(null);
  }

  function addSource() {
    setConfig((current) =>
      current ? { ...current, sources: [...current.sources, emptySource()] } : current,
    );
    setSavedMessage(null);
  }

  function removeSource(index: number) {
    setConfig((current) => {
      if (!current) return current;
      return { ...current, sources: current.sources.filter((_, i) => i !== index) };
    });
    setSavedMessage(null);
  }

  async function handleSave() {
    if (!config) return;
    setSaving(true);
    setError(null);
    setSavedMessage(null);
    try {
      const response = await updateSources(config);
      setConfig(response.config);
      setIsDefault(response.is_default);
      setSavedMessage(t.sourcesSaved);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.failedSaveSources);
    } finally {
      setSaving(false);
    }
  }

  async function handleReset() {
    setResetting(true);
    setError(null);
    setSavedMessage(null);
    try {
      const response = await resetSources();
      setConfig(response.config);
      setIsDefault(true);
      setSavedMessage(t.sourcesRestored);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.failedResetSources);
    } finally {
      setResetting(false);
    }
  }

  if (loading) return <div className="loading panel panel-padding">{t.loadingSources}</div>;
  if (error && !config) return <div className="error panel panel-padding">{error}</div>;
  if (!config) return null;

  return (
    <>
      <section className="hero">
        <h1>{t.sourcesTitle}</h1>
        <p>{t.sourcesSubtitle}</p>
      </section>

      <section className="panel panel-padding">
        <div className="prompts-toolbar">
          <div>
            <h2 className="section-title" style={{ marginBottom: 6 }}>
              {t.preferredSources}
            </h2>
            <p className="meta" style={{ margin: 0 }}>
              {isDefault ? t.usingDefaultSources : t.usingCustomSources}
            </p>
          </div>
          <div className="prompts-actions">
            <button type="button" className="button" onClick={addSource} disabled={saving || resetting}>
              {t.addSource}
            </button>
            <button type="button" className="button" onClick={handleReset} disabled={resetting || saving}>
              {resetting ? t.resetting : t.resetToDefaults}
            </button>
            <button type="button" className="button button-primary" onClick={handleSave} disabled={saving || resetting}>
              {saving ? t.saving : t.saveSources}
            </button>
          </div>
        </div>

        {error ? <div className="error" style={{ marginTop: 16 }}>{error}</div> : null}
        {savedMessage ? <div className="success" style={{ marginTop: 16 }}>{savedMessage}</div> : null}

        {config.sources.length === 0 ? (
          <div className="empty-state sources-empty">
            <p>{t.noPreferredSources}</p>
            <p className="meta">{t.noPreferredSourcesHint}</p>
            <button type="button" className="button button-primary" onClick={addSource} style={{ marginTop: 12 }}>
              {t.addFirstSource}
            </button>
          </div>
        ) : (
          <div className="sources-list">
            {config.sources.map((source, index) => (
              <article className="source-card" key={`${source.domain}-${index}`}>
                <div className="source-card-header">
                  <h3>{source.name || t.sourceFallbackName(index + 1)}</h3>
                  <label className="source-toggle">
                    <input
                      type="checkbox"
                      checked={source.enabled}
                      onChange={(event) => updateSource(index, { enabled: event.target.checked })}
                    />
                    {t.enabled}
                  </label>
                </div>

                <div className="source-fields">
                  <div className="source-field">
                    <label htmlFor={`source-name-${index}`}>{t.sourceName}</label>
                    <input
                      id={`source-name-${index}`}
                      value={source.name}
                      placeholder="Allure Beauty"
                      onChange={(event) => updateSource(index, { name: event.target.value })}
                    />
                    <p className="field-hint">{t.sourceNameHint}</p>
                  </div>
                  <div className="source-field">
                    <label htmlFor={`source-domain-${index}`}>{t.sourceDomain}</label>
                    <input
                      id={`source-domain-${index}`}
                      value={source.domain}
                      placeholder="allure.com"
                      onChange={(event) => updateSource(index, { domain: event.target.value })}
                    />
                    <p className="field-hint">{t.sourceDomainHint}</p>
                  </div>
                  <div className="source-field">
                    <label htmlFor={`source-weight-${index}`}>{t.sourceWeight}</label>
                    <input
                      id={`source-weight-${index}`}
                      type="number"
                      min={0}
                      max={10}
                      step={0.1}
                      value={source.weight}
                      onChange={(event) =>
                        updateSource(index, { weight: Number(event.target.value) || 0 })
                      }
                    />
                    <p className="field-hint">{t.sourceWeightHint}</p>
                  </div>
                </div>

                <div className="field">
                  <label>{t.sourceCategories}</label>
                  <div className="chips">
                    {CATEGORY_OPTIONS.map((category) => (
                      <label className="chip chip-toggle" key={category}>
                        <input
                          type="checkbox"
                          checked={source.categories.includes(category)}
                          onChange={() => toggleCategory(index, category)}
                        />
                        {category === "nails" ? t.categoryNails : category}
                      </label>
                    ))}
                  </div>
                  <p className="field-hint">{t.sourceCategoriesHint}</p>
                </div>

                <button type="button" className="button source-remove" onClick={() => removeSource(index)}>
                  {t.removeSource}
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
