import React from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  className?: string;
}

const variantConfig: Record<string, { icon: React.ReactNode; styles: string }> = {
  info: {
    icon: <Info className="w-5 h-5" />,
    styles: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
  },
  success: {
    icon: <CheckCircle className="w-5 h-5" />,
    styles: 'bg-green-500/10 border-green-500/30 text-green-400',
  },
  warning: {
    icon: <AlertTriangle className="w-5 h-5" />,
    styles: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
  },
  error: {
    icon: <AlertCircle className="w-5 h-5" />,
    styles: 'bg-red-500/10 border-red-500/30 text-red-400',
  },
};

export function Alert({ children, variant = 'info', title, className }: AlertProps) {
  const config = variantConfig[variant];

  return (
    <div className={cn(
      'flex gap-3 p-4 rounded-lg border',
      config.styles,
      className
    )}>
      <div className="flex-shrink-0 mt-0.5">{config.icon}</div>
      <div>
        {title && <p className="font-medium mb-1">{title}</p>}
        <div className="text-sm opacity-90">{children}</div>
      </div>
    </div>
  );
}
