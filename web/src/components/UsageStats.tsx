import { useTranslation } from "../i18n/LocaleProvider";
import type { LLMUsageStats } from "../types";
import { formatCostUsd, formatTokenCount } from "../utils/usage";

interface UsageStatsProps {
  usage: LLMUsageStats | null | undefined;
  compact?: boolean;
}

export function UsageStats({ usage, compact = false }: UsageStatsProps) {
  const t = useTranslation();

  if (!usage || (!usage.total_tokens && !usage.estimated_cost_usd)) {
    return compact ? null : <span className="meta">{t.usageNotRecorded}</span>;
  }

  if (compact) {
    return (
      <span className="usage-inline">
        {t.usageCompact(formatTokenCount(usage.total_tokens), formatCostUsd(usage.estimated_cost_usd, t))}
      </span>
    );
  }

  return (
    <div className="usage-panel">
      <div className="usage-row">
        <span className="usage-label">{t.promptTokens}</span>
        <span>{formatTokenCount(usage.prompt_tokens)}</span>
      </div>
      <div className="usage-row">
        <span className="usage-label">{t.completionTokens}</span>
        <span>{formatTokenCount(usage.completion_tokens)}</span>
      </div>
      <div className="usage-row usage-row-total">
        <span className="usage-label">{t.totalTokens}</span>
        <span>{formatTokenCount(usage.total_tokens)}</span>
      </div>
      <div className="usage-row usage-row-cost">
        <span className="usage-label">{t.estimatedCost}</span>
        <span>{formatCostUsd(usage.estimated_cost_usd, t)}</span>
      </div>
    </div>
  );
}
