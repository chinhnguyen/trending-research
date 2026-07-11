import { useEffect, useRef, useState, type ReactNode } from "react";
import type { RegenerateField } from "../api";
import { useTranslation } from "../i18n/LocaleProvider";

export type OptionDraft = {
  hook: string;
  caption: string;
  hashtagsText: string;
  prompt: string;
};

type DraftFieldKey = RegenerateField;

const AUTO_GENERATE_SECONDS = 10;

function ReloadIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M21 12a9 9 0 1 1-2.64-6.36"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M21 3v6h-6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M13.5 6.5l4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function FieldSpinner() {
  return <span className="field-spinner" aria-hidden="true" />;
}

function DraftField({
  label,
  value,
  rows,
  placeholder,
  editing,
  reloading,
  disabled,
  reloadLabel,
  editLabel,
  stopEditLabel,
  doneEditingLabel,
  loadingLabel,
  extraActions,
  onToggleEdit,
  onChange,
  onReload,
}: {
  label: string;
  value: string;
  rows: number;
  placeholder?: string;
  editing: boolean;
  reloading?: boolean;
  disabled?: boolean;
  reloadLabel: string;
  editLabel: string;
  stopEditLabel: string;
  doneEditingLabel: string;
  loadingLabel: string;
  extraActions?: ReactNode;
  onToggleEdit: () => void;
  onChange: (value: string) => void;
  onReload: () => void;
}) {
  const showLoading = reloading;

  return (
    <div className={`media-prompt-field${showLoading ? " is-loading" : ""}${editing ? " is-editing" : ""}`}>
      <div className="media-prompt-field-header">
        <span className="meta">{label}</span>
        <div className="media-prompt-field-actions">
          {extraActions}
          <button
            type="button"
            className={`button-icon${editing ? " active" : ""}`}
            onClick={() => onToggleEdit()}
            disabled={disabled || showLoading}
            aria-label={editing ? stopEditLabel : editLabel}
            title={editing ? doneEditingLabel : editLabel}
          >
            <PencilIcon />
          </button>
          <button
            type="button"
            className="button-icon"
            onClick={() => onReload()}
            disabled={disabled || showLoading}
            aria-label={reloadLabel}
            title={reloadLabel}
          >
            <ReloadIcon />
          </button>
        </div>
      </div>

      {showLoading ? (
        <div className="media-prompt-field-loading" aria-live="polite">
          <FieldSpinner />
          <p className="meta">{loadingLabel}</p>
        </div>
      ) : editing ? (
        <textarea
          value={value}
          rows={rows}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <div className="media-prompt-readonly">{value.trim() ? value : placeholder}</div>
      )}
    </div>
  );
}

export function MediaPromptReview({
  draft: initialDraft,
  optionKey,
  kind,
  disabled = false,
  mediaBusy = false,
  regeneratingField = null,
  accepting = false,
  autoAcceptEnabled = false,
  mediaPreview,
  onAccept,
  onRegenerate,
}: {
  draft: OptionDraft;
  optionKey: string;
  kind: "image" | "video";
  disabled?: boolean;
  mediaBusy?: boolean;
  regeneratingField?: RegenerateField | null;
  accepting?: boolean;
  autoAcceptEnabled?: boolean;
  mediaPreview: ReactNode;
  onAccept: (draft: OptionDraft) => void | Promise<void>;
  onRegenerate: (field: RegenerateField) => void | Promise<void>;
}) {
  const t = useTranslation();
  const [draft, setDraft] = useState(initialDraft);
  const [editingFields, setEditingFields] = useState<Set<DraftFieldKey>>(new Set());
  const [countdown, setCountdown] = useState<number | null>(null);
  const [autoAcceptArmed, setAutoAcceptArmed] = useState(false);
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const onAcceptRef = useRef(onAccept);
  onAcceptRef.current = onAccept;
  const pendingReloadRef = useRef(false);
  const pendingEditArmRef = useRef(false);
  const countdownActiveRef = useRef(false);

  useEffect(() => {
    setDraft(initialDraft);
    setEditingFields(new Set());
    setAutoAcceptArmed(false);
    setCountdown(null);
    pendingReloadRef.current = false;
    pendingEditArmRef.current = false;
    countdownActiveRef.current = false;
  }, [optionKey]);

  useEffect(() => {
    setDraft(initialDraft);
  }, [initialDraft]);

  const formLocked = disabled || accepting || mediaBusy;
  const draftReady = Boolean(draft.prompt.trim() && draft.caption.trim());

  function disarmAutoAccept() {
    setAutoAcceptArmed(false);
    setCountdown(null);
    countdownActiveRef.current = false;
  }

  function armAutoAccept() {
    if (!autoAcceptEnabled || !draftReady || formLocked || mediaBusy || regeneratingField !== null) {
      return;
    }
    setAutoAcceptArmed(true);
  }

  useEffect(() => {
    if (editingFields.size > 0 || regeneratingField !== null || formLocked || mediaBusy || !autoAcceptEnabled) {
      disarmAutoAccept();
    }
  }, [editingFields, regeneratingField, formLocked, mediaBusy, autoAcceptEnabled]);

  useEffect(() => {
    if (!pendingEditArmRef.current || editingFields.size > 0) {
      return;
    }
    pendingEditArmRef.current = false;
    armAutoAccept();
  }, [editingFields, draftReady, autoAcceptEnabled, formLocked, mediaBusy, regeneratingField]);

  useEffect(() => {
    if (!pendingReloadRef.current || regeneratingField !== null) {
      return;
    }
    pendingReloadRef.current = false;
    armAutoAccept();
  }, [initialDraft, regeneratingField, draftReady, autoAcceptEnabled, formLocked, mediaBusy]);

  useEffect(() => {
    if (!autoAcceptArmed || countdownActiveRef.current) {
      return;
    }
    if (!autoAcceptEnabled || formLocked || mediaBusy || regeneratingField !== null || editingFields.size > 0 || !draftReady) {
      return;
    }

    countdownActiveRef.current = true;
    setCountdown(AUTO_GENERATE_SECONDS);

    const interval = window.setInterval(() => {
      setCountdown((current) => {
        if (current === null) return null;
        if (current <= 1) {
          window.clearInterval(interval);
          countdownActiveRef.current = false;
          setAutoAcceptArmed(false);
          void onAcceptRef.current(draftRef.current);
          return null;
        }
        return current - 1;
      });
    }, 1000);

    return () => {
      window.clearInterval(interval);
      countdownActiveRef.current = false;
    };
  }, [autoAcceptArmed, autoAcceptEnabled, formLocked, mediaBusy, regeneratingField, editingFields, draftReady]);

  function updateField<K extends keyof OptionDraft>(field: K, value: OptionDraft[K]) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  function toggleEdit(field: DraftFieldKey) {
    if (disabled || mediaBusy || regeneratingField === field) {
      return;
    }
    setEditingFields((current) => {
      const next = new Set(current);
      const wasEditing = next.has(field);
      if (wasEditing) {
        next.delete(field);
        pendingEditArmRef.current = true;
      } else {
        disarmAutoAccept();
        next.add(field);
      }
      return next;
    });
  }

  function handleReload(field: DraftFieldKey) {
    disarmAutoAccept();
    pendingReloadRef.current = true;
    void onRegenerate(field);
  }

  function fieldProps(field: DraftFieldKey, label: string, rows: number, placeholder: string) {
    const draftKey = field === "hashtags" ? "hashtagsText" : field;
    const fieldLocked = disabled || mediaBusy || regeneratingField === field;
    const lowerLabel = label.toLowerCase();
    return {
      label,
      rows,
      placeholder,
      editing: editingFields.has(field),
      reloading: regeneratingField === field,
      disabled: fieldLocked,
      reloadLabel: t.regenerateField(lowerLabel),
      editLabel: t.editField(lowerLabel),
      stopEditLabel: t.stopEditingField(lowerLabel),
      doneEditingLabel: t.doneEditing,
      loadingLabel: t.regenerating,
      value: draft[draftKey as keyof OptionDraft],
      onToggleEdit: () => toggleEdit(field),
      onChange: (value: string) => updateField(draftKey as keyof OptionDraft, value),
      onReload: () => handleReload(field),
    };
  }

  const acceptLabel =
    accepting || mediaBusy
      ? t.generating
      : countdown !== null
        ? t.autoGenerateCountdown(countdown)
        : t.acceptAndGenerate;

  return (
    <div className="media-prompt-review-layout">
      <div className="media-prompt-fields">
        <div className="media-prompt-review-header">
          <p className="meta section-eyebrow">{t.reviewBeforeGenerating}</p>
          <h4>{t.yourPrompt(kind)}</h4>
          <p className="meta">{t.reviewHint}</p>
        </div>

        {countdown !== null ? (
          <div className="media-prompt-auto-countdown" aria-live="polite">
            <div className="media-prompt-auto-countdown-copy">
              <span className="field-spinner" aria-hidden="true" />
              <span>{t.autoGenerateCountdown(countdown)}</span>
            </div>
            <button type="button" className="button button-compact" onClick={disarmAutoAccept}>
              {t.cancelAutoGenerate}
            </button>
            <div
              className="media-prompt-auto-countdown-bar"
              aria-hidden="true"
              style={{ width: `${(countdown / AUTO_GENERATE_SECONDS) * 100}%` }}
            />
          </div>
        ) : null}

        <DraftField {...fieldProps("hook", t.hook, 2, t.hookPlaceholder)} />
        <DraftField {...fieldProps("caption", t.caption, 4, t.captionPlaceholder)} />
        <DraftField {...fieldProps("hashtags", t.hashtags, 2, t.hashtagsPlaceholder)} />
        <DraftField
          {...fieldProps("prompt", t.generationPrompt, 5, t.promptPlaceholder)}
          extraActions={
            <button
              type="button"
              className="button button-primary button-compact media-prompt-accept-inline"
              onClick={() => {
                disarmAutoAccept();
                void onAccept(draft);
              }}
              disabled={
                formLocked || regeneratingField !== null || !draft.prompt.trim() || !draft.caption.trim()
              }
            >
              {acceptLabel}
            </button>
          }
        />
      </div>

      <div className="media-prompt-preview-column">
        <div className="media-prompt-preview-frame">{mediaPreview}</div>
      </div>
    </div>
  );
}
