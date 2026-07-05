import { useEffect, useState } from "react";
import { getPrompts, resetPrompts, updatePrompts } from "../api";
import type { PromptConfig } from "../types";

const TEMPLATE_HINTS = {
  neutral_user_template: "{category}, {region}, {research_time}",
  personalized_user_template: "{category}, {region}, {research_time}, {preferences_json}",
};

const FIELDS: Array<{
  key: keyof PromptConfig;
  label: string;
  hint: string;
  rows: number;
}> = [
  {
    key: "neutral_system_prompt",
    label: "Neutral system prompt",
    hint: "Instructions for objective trend research. Appended with web grounded rules before sending.",
    rows: 14,
  },
  {
    key: "personalized_system_prompt",
    label: "Personalized system prompt",
    hint: "Instructions for tailored recommendations. Appended with web grounded rules before sending.",
    rows: 14,
  },
  {
    key: "web_grounded_rules",
    label: "Web grounded rules",
    hint: "Appended to both system prompts when web search is enabled.",
    rows: 6,
  },
  {
    key: "neutral_user_template",
    label: "Neutral user template",
    hint: `Placeholders: ${TEMPLATE_HINTS.neutral_user_template}. Web snippets are appended separately.`,
    rows: 5,
  },
  {
    key: "personalized_user_template",
    label: "Personalized user template",
    hint: `Placeholders: ${TEMPLATE_HINTS.personalized_user_template}. Web snippets are appended separately.`,
    rows: 6,
  },
];

export function PromptsPage() {
  const [config, setConfig] = useState<PromptConfig | null>(null);
  const [isDefault, setIsDefault] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    getPrompts()
      .then((response) => {
        setConfig(response.config);
        setIsDefault(response.is_default);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function updateField(key: keyof PromptConfig, value: string) {
    setConfig((current) => (current ? { ...current, [key]: value } : current));
    setSavedMessage(null);
  }

  async function handleSave() {
    if (!config) return;
    setSaving(true);
    setError(null);
    setSavedMessage(null);
    try {
      const response = await updatePrompts(config);
      setConfig(response.config);
      setIsDefault(response.is_default);
      setSavedMessage("Prompts saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save prompts");
    } finally {
      setSaving(false);
    }
  }

  async function handleReset() {
    setResetting(true);
    setError(null);
    setSavedMessage(null);
    try {
      const response = await resetPrompts();
      setConfig(response.config);
      setIsDefault(true);
      setSavedMessage("Restored default prompts.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset prompts");
    } finally {
      setResetting(false);
    }
  }

  if (loading) return <div className="loading panel panel-padding">Loading prompts…</div>;
  if (error && !config) return <div className="error panel panel-padding">{error}</div>;
  if (!config) return null;

  return (
    <>
      <section className="hero">
        <h1>Prompt settings</h1>
        <p>
          Edit the system and user prompts used for neutral and personalized research runs.
          Changes apply to new research only.
        </p>
      </section>

      <section className="panel panel-padding">
        <div className="prompts-toolbar">
          <div>
            <h2 className="section-title" style={{ marginBottom: 6 }}>
              Active configuration
            </h2>
            <p className="meta" style={{ margin: 0 }}>
              {isDefault ? "Using built-in defaults" : "Using custom prompts from config/prompts.yaml"}
            </p>
          </div>
          <div className="prompts-actions">
            <button type="button" className="button" onClick={handleReset} disabled={resetting || saving}>
              {resetting ? "Resetting…" : "Reset to defaults"}
            </button>
            <button type="button" className="button button-primary" onClick={handleSave} disabled={saving || resetting}>
              {saving ? "Saving…" : "Save prompts"}
            </button>
          </div>
        </div>

        {error ? <div className="error" style={{ marginTop: 16 }}>{error}</div> : null}
        {savedMessage ? <div className="success" style={{ marginTop: 16 }}>{savedMessage}</div> : null}

        <div className="prompts-form">
          {FIELDS.map((field) => (
            <div className="field" key={field.key}>
              <label htmlFor={field.key}>{field.label}</label>
              <p className="field-hint">{field.hint}</p>
              <textarea
                id={field.key}
                rows={field.rows}
                value={config[field.key]}
                onChange={(event) => updateField(field.key, event.target.value)}
              />
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
