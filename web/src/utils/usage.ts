export function formatTokenCount(value: number): string {
  return new Intl.NumberFormat(undefined).format(value);
}

type CostLabels = {
  costFree: string;
  costUnderCent: string;
};

export function formatCostUsd(value: number, labels?: CostLabels): string {
  if (value <= 0) return labels?.costFree ?? "Free";
  if (value < 0.01) return labels?.costUnderCent ?? "< $0.01";
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}
