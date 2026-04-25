import React from 'react';
import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

const colorStyles: Record<string, string> = {
  primary: 'bg-primary-600',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  danger: 'bg-red-500',
};

export function Progress({ value, max = 100, className, showLabel = false, color = 'primary' }: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between mb-1.5">
        {showLabel && (
          <span className="text-xs text-gray-400">{Math.round(percentage)}%</span>
        )}
      </div>
      <div className="w-full bg-security-dark rounded-full h-2 overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', colorStyles[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
