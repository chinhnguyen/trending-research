import { useEffect, useState, type ReactNode } from "react";
import type { RegenerateField } from "../api";

export type OptionDraft = {
  hook: string;
  caption: string;
  hashtagsText: string;
  prompt: string;
};

type DraftFieldKey = RegenerateField;

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
  extraActions?: ReactNode;
  onToggleEdit: () => void;
  onChange: (value: string) => void;
  onReload: () => void;
}) {
  const showLoading = reloading;
  const loadingLabel = "Regenerating…";

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
            aria-label={editing ? `Stop editing ${label.toLowerCase()}` : `Edit ${label.toLowerCase()}`}
            title={editing ? "Done editing" : `Edit ${label.toLowerCase()}`}
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
  kind,
  disabled = false,
  mediaBusy = false,
  regeneratingField = null,
  accepting = false,
  mediaPreview,
  onAccept,
  onRegenerate,
}: {
  draft: OptionDraft;
  kind: "image" | "video";
  disabled?: boolean;
  mediaBusy?: boolean;
  regeneratingField?: RegenerateField | null;
  accepting?: boolean;
  mediaPreview: ReactNode;
  onAccept: (draft: OptionDraft) => void | Promise<void>;
  onRegenerate: (field: RegenerateField) => void | Promise<void>;
}) {
  const [draft, setDraft] = useState(initialDraft);
  const [editingFields, setEditingFields] = useState<Set<DraftFieldKey>>(new Set());

  useEffect(() => {
    setDraft(initialDraft);
    setEditingFields(new Set());
  }, [initialDraft]);

  const mediaLabel = kind === "video" ? "video" : "image";
  const formLocked = disabled || accepting || mediaBusy;

  function updateField<K extends keyof OptionDraft>(field: K, value: OptionDraft[K]) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  function toggleEdit(field: DraftFieldKey) {
    if (disabled || mediaBusy || regeneratingField === field) {
      return;
    }
    setEditingFields((current) => {
      const next = new Set(current);
      if (next.has(field)) {
        next.delete(field);
      } else {
        next.add(field);
      }
      return next;
    });
  }

  function fieldProps(field: DraftFieldKey, label: string, rows: number, placeholder: string) {
    const draftKey = field === "hashtags" ? "hashtagsText" : field;
    const fieldLocked = disabled || mediaBusy || regeneratingField === field;
    return {
      label,
      rows,
      placeholder,
      editing: editingFields.has(field),
      reloading: regeneratingField === field,
      disabled: fieldLocked,
      reloadLabel: `Regenerate ${label.toLowerCase()}`,
      value: draft[draftKey as keyof OptionDraft],
      onToggleEdit: () => toggleEdit(field),
      onChange: (value: string) => updateField(draftKey as keyof OptionDraft, value),
      onReload: () => onRegenerate(field),
    };
  }

  return (
    <div className="media-prompt-review-layout">
      <div className="media-prompt-fields">
        <div className="media-prompt-review-header">
          <p className="meta section-eyebrow">Review before generating</p>
          <h4>Your {mediaLabel} prompt</h4>
          <p className="meta">Reload any field for a fresh suggestion, or edit before you accept.</p>
        </div>

        <DraftField {...fieldProps("hook", "Hook", 2, "Opening line or first-frame hook")} />
        <DraftField {...fieldProps("caption", "Caption", 4, "Platform-ready caption")} />
        <DraftField {...fieldProps("hashtags", "Hashtags", 2, "#nailtrend, #saloninspo")} />
        <DraftField
          {...fieldProps("prompt", "Generation prompt", 5, "Describe the image or video to generate")}
          extraActions={
            <button
              type="button"
              className="button button-primary button-compact media-prompt-accept-inline"
              onClick={() => onAccept(draft)}
              disabled={
                formLocked || regeneratingField !== null || !draft.prompt.trim() || !draft.caption.trim()
              }
            >
              {accepting || mediaBusy ? "Generating…" : "Generate"}
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
