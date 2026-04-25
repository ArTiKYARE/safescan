import { Severity, ScanStatus } from '@/types';

// ==================== Severity Helpers ====================

export function severityColor(severity: Severity): string {
  const colors: Record<Severity, string> = {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#d97706',
    low: '#2563eb',
    info: '#6b7280',
  };
  return colors[severity] || '#6b7280';
}

export function severityBgColor(severity: Severity): string {
  const colors: Record<Severity, string> = {
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    low: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    info: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  };
  return colors[severity] || colors.info;
}

// ==================== Scan Status Helpers ====================

export function scanStatusColor(status: ScanStatus): string {
  const colors: Record<ScanStatus, string> = {
    pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    queued: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    running: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  };
  return colors[status] || colors.pending;
}

export function scanStatusLabel(status: ScanStatus): string {
  const labels: Record<ScanStatus, string> = {
    pending: 'Ожидание',
    queued: 'В очереди',
    running: 'Запущен',
    completed: 'Завершён',
    failed: 'Ошибка',
    cancelled: 'Отменён',
  };
  return labels[status] || status;
}

// ==================== Grade Helpers ====================

export function gradeColor(grade: string | null): string {
  if (!grade) return 'text-gray-400';
  const colors: Record<string, string> = {
    'A+': 'text-green-500',
    'A': 'text-green-500',
    'B': 'text-lime-500',
    'C': 'text-yellow-500',
    'D': 'text-orange-500',
    'F': 'text-red-500',
  };
  return colors[grade] || 'text-gray-400';
}

export function gradeBg(grade: string | null): string {
  if (!grade) return 'bg-gray-100 text-gray-400';
  const colors: Record<string, string> = {
    'A+': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'A': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'B': 'bg-lime-100 text-lime-700 dark:bg-lime-900/30 dark:text-lime-400',
    'C': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'D': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'F': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };
  return colors[grade] || 'bg-gray-100 text-gray-400';
}

// ==================== Date Helpers ====================

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'только что';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} мин назад`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} ч назад`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} дн назад`;
  return formatDate(dateStr);
}

// ==================== CVSS Helpers ====================

export function cvssLabel(score: number | null): string {
  if (score === null) return 'N/A';
  if (score >= 9.0) return `${score} Critical`;
  if (score >= 7.0) return `${score} High`;
  if (score >= 4.0) return `${score} Medium`;
  if (score > 0) return `${score} Low`;
  return `${score} Info`;
}

// ==================== Misc ====================

export function cn(...classes: (string | boolean | undefined | null | 0 | 0n)[]) {
  return classes.filter((c) => c && c !== true).join(' ');
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}
