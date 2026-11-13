export function formatNumber(value: number, digits = 0): string {
  if (!Number.isFinite(value)) return '—';
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatMoney(value: number, digits = 2): string {
  return `¥${formatNumber(value, digits)}`;
}

export function formatMetric(value: number, unit: string, scale: number): string {
  const digits = scale >= 100 ? 2 : 1;
  if (unit === '元') return formatMoney(value, digits);
  return `${formatNumber(value, digits)} ${unit}`;
}

export function formatPct(value: number, digits = 2): string {
  return `${value.toFixed(digits)}%`;
}

export function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)} s`;
  return `${ms.toFixed(2)} ms`;
}

export function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(2)} s`;
}

export function formatInt(value: number): string {
  return value.toLocaleString('zh-CN');
}

export function shortCode(code: string): string {
  return code.length > 18 ? `${code.slice(0, 18)}…` : code;
}
