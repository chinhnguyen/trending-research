import { useEffect, useState } from "react";
import { getSources, resetSources, updateSources } from "../api";
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
      setSavedMessage("Sources saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save sources");
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
      setSavedMessage("Restored default sources.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset sources");
    } finally {
      setResetting(false);
    }
  }

  if (loading) return <div className="loading panel panel-padding">Loading sources…</div>;
  if (error && !config) return <div className="error panel panel-padding">{error}</div>;
  if (!config) return null;

  return (
    <>
      <section className="hero">
        <h1>Web search sources</h1>
        <p>
          Configure trusted domains to boost ranking and trigger site-specific queries during web
          research. Changes apply to new research only.
        </p>
      </section>

      <section className="panel panel-padding">
        <div className="prompts-toolbar">
          <div>
            <h2 className="section-title" style={{ marginBottom: 6 }}>
              Preferred sources
            </h2>
            <p className="meta" style={{ margin: 0 }}>
              {isDefault
                ? "Using the default editorial source list"
                : "Using custom sources from config/preferred_sources.yaml"}
            </p>
          </div>
          <div className="prompts-actions">
            <button type="button" className="button" onClick={addSource} disabled={saving || resetting}>
              Add source
            </button>
            <button type="button" className="button" onClick={handleReset} disabled={resetting || saving}>
              {resetting ? "Resetting…" : "Reset to defaults"}
            </button>
            <button type="button" className="button button-primary" onClick={handleSave} disabled={saving || resetting}>
              {saving ? "Saving…" : "Save sources"}
            </button>
          </div>
        </div>

        {error ? <div className="error" style={{ marginTop: 16 }}>{error}</div> : null}
        {savedMessage ? <div className="success" style={{ marginTop: 16 }}>{savedMessage}</div> : null}

        {config.sources.length === 0 ? (
          <div className="empty-state sources-empty">
            <p>No preferred sources yet.</p>
            <p className="meta">
              Defaults include editorial sites already used in research runs — Allure, Vogue, Marie
              Claire, Byrdie, and others. Add or remove domains as needed.
            </p>
            <button type="button" className="button button-primary" onClick={addSource} style={{ marginTop: 12 }}>
              Add your first source
            </button>
          </div>
        ) : (
          <div className="sources-list">
            {config.sources.map((source, index) => (
              <article className="source-card" key={`${source.domain}-${index}`}>
                <div className="source-card-header">
                  <h3>{source.name || `Source ${index + 1}`}</h3>
                  <label className="source-toggle">
                    <input
                      type="checkbox"
                      checked={source.enabled}
                      onChange={(event) => updateSource(index, { enabled: event.target.checked })}
                    />
                    Enabled
                  </label>
                </div>

                <div className="source-fields">
                  <div className="source-field">
                    <label htmlFor={`source-name-${index}`}>Name</label>
                    <input
                      id={`source-name-${index}`}
                      value={source.name}
                      placeholder="Allure Beauty"
                      onChange={(event) => updateSource(index, { name: event.target.value })}
                    />
                    <p className="field-hint">Editorial label shown in results.</p>
                  </div>
                  <div className="source-field">
                    <label htmlFor={`source-domain-${index}`}>Domain</label>
                    <input
                      id={`source-domain-${index}`}
                      value={source.domain}
                      placeholder="allure.com"
                      onChange={(event) => updateSource(index, { domain: event.target.value })}
                    />
                    <p className="field-hint">Without https:// — e.g. allure.com</p>
                  </div>
                  <div className="source-field">
                    <label htmlFor={`source-weight-${index}`}>Weight</label>
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
                    <p className="field-hint">Higher weight ranks results from this domain first.</p>
                  </div>
                </div>

                <div className="field">
                  <label>Categories</label>
                  <div className="chips">
                    {CATEGORY_OPTIONS.map((category) => (
                      <label className="chip chip-toggle" key={category}>
                        <input
                          type="checkbox"
                          checked={source.categories.includes(category)}
                          onChange={() => toggleCategory(index, category)}
                        />
                        {category}
                      </label>
                    ))}
                  </div>
                  <p className="field-hint">
                    Leave all unchecked to apply this source to every category.
                  </p>
                </div>

                <button type="button" className="button source-remove" onClick={() => removeSource(index)}>
                  Remove source
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
