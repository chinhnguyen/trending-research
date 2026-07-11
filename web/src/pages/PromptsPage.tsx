import { useEffect, useMemo, useState } from "react";
import { getPrompts, resetPrompts, updatePrompts } from "../api";
import { useTranslation } from "../i18n/LocaleProvider";
import type { PromptConfig } from "../types";
import type { TranslationFn } from "../i18n/translations";

function promptFields(t: TranslationFn): Array<{
  key: keyof PromptConfig;
  label: string;
  hint: string;
  rows: number;
}> {
  return [
    {
      key: "neutral_system_prompt",
      label: t.promptNeutralSystem,
      hint: t.promptNeutralSystemHint,
      rows: 14,
    },
    {
      key: "personalized_system_prompt",
      label: t.promptPersonalizedSystem,
      hint: t.promptPersonalizedSystemHint,
      rows: 14,
    },
    {
      key: "web_grounded_rules",
      label: t.promptWebGrounded,
      hint: t.promptWebGroundedHint,
      rows: 6,
    },
    {
      key: "neutral_user_template",
      label: t.promptNeutralUser,
      hint: t.promptNeutralUserHint,
      rows: 5,
    },
    {
      key: "personalized_user_template",
      label: t.promptPersonalizedUser,
      hint: t.promptPersonalizedUserHint,
      rows: 6,
    },
  ];
}

export function PromptsPage() {
  const t = useTranslation();
  const fields = useMemo(() => promptFields(t), [t]);
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
      setSavedMessage(t.promptsSaved);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.failedSavePrompts);
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
      setSavedMessage(t.promptsRestored);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.failedResetPrompts);
    } finally {
      setResetting(false);
    }
  }

  if (loading) return <div className="loading panel panel-padding">{t.loadingPrompts}</div>;
  if (error && !config) return <div className="error panel panel-padding">{error}</div>;
  if (!config) return null;

  return (
    <>
      <section className="hero">
        <h1>{t.promptsTitle}</h1>
        <p>{t.promptsSubtitle}</p>
      </section>

      <section className="panel panel-padding">
        <div className="prompts-toolbar">
          <div>
            <h2 className="section-title" style={{ marginBottom: 6 }}>
              {t.activeConfiguration}
            </h2>
            <p className="meta" style={{ margin: 0 }}>
              {isDefault ? t.usingBuiltInDefaults : t.usingCustomPrompts}
            </p>
          </div>
          <div className="prompts-actions">
            <button type="button" className="button" onClick={handleReset} disabled={resetting || saving}>
              {resetting ? t.resetting : t.resetToDefaults}
            </button>
            <button type="button" className="button button-primary" onClick={handleSave} disabled={saving || resetting}>
              {saving ? t.saving : t.savePrompts}
            </button>
          </div>
        </div>

        {error ? <div className="error" style={{ marginTop: 16 }}>{error}</div> : null}
        {savedMessage ? <div className="success" style={{ marginTop: 16 }}>{savedMessage}</div> : null}

        <div className="prompts-form">
          {fields.map((field) => (
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
