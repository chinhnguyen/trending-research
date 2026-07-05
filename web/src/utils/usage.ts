export function formatTokenCount(value: number): string {
  return new Intl.NumberFormat(undefined).format(value);
}

export function formatCostUsd(value: number): string {
  if (value <= 0) return "Free";
  if (value < 0.01) return "< $0.01";
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}
