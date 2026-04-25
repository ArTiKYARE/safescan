import { cn, severityColor, severityBgColor, scanStatusColor, scanStatusLabel, gradeBg } from '@/lib/utils';
import type { Severity, ScanStatus } from '@/types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'severity' | 'scan-status' | 'grade' | 'custom';
  value?: Severity | ScanStatus | string | null;
  className?: string;
}

export function Badge({ children, variant = 'default', value, className }: BadgeProps) {
  let badgeClass = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

  if (variant === 'severity' && value) {
    return (
      <span className={cn(badgeClass, severityBgColor(value as Severity), className)}>
        {children}
      </span>
    );
  }

  if (variant === 'scan-status' && value) {
    return (
      <span className={cn(badgeClass, scanStatusColor(value as ScanStatus), className)}>
        {children}
      </span>
    );
  }

  if (variant === 'grade' && value) {
    return (
      <span className={cn(badgeClass, gradeBg(value as string), className)}>
        {children}
      </span>
    );
  }

  // Default
  return (
    <span className={cn(badgeClass, 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', className)}>
      {children}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const labels: Record<Severity, string> = {
    critical: 'CRITICAL',
    high: 'HIGH',
    medium: 'MEDIUM',
    low: 'LOW',
    info: 'INFO',
  };
  return <Badge variant="severity" value={severity}>{labels[severity]}</Badge>;
}

export function ScanStatusBadge({ status }: { status: ScanStatus }) {
  return <Badge variant="scan-status" value={status}>{scanStatusLabel(status)}</Badge>;
}

export function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span className="text-gray-400 text-sm">N/A</span>;
  return <Badge variant="grade" value={grade}>{grade}</Badge>;
}
