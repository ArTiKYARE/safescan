'use client';

import React, { useEffect } from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  );
}

export function DialogContent({ children, className, title, description }: DialogContentProps) {
  return (
    <div className={cn(
      'relative z-50 w-full max-w-lg mx-4 bg-security-card border border-security-border rounded-xl shadow-2xl',
      'animate-in fade-in zoom-in-95 duration-200',
      className
    )}>
      {(title || description) && (
        <div className="px-6 py-4 border-b border-security-border">
          {title && <h2 className="text-lg font-semibold text-white">{title}</h2>}
          {description && <p className="text-sm text-gray-400 mt-1">{description}</p>}
        </div>
      )}
      <div className="px-6 py-4">{children}</div>
    </div>
  );
}

export function DialogHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('mb-4', className)}>{children}</div>;
}

export function DialogFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex items-center justify-end gap-2 mt-6 pt-4 border-t border-security-border', className)}>
      {children}
    </div>
  );
}

export function DialogTrigger({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return <div onClick={onClick}>{children}</div>;
}

export function DialogClose({ onClick, children }: { onClick: () => void; children?: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="absolute right-4 top-4 text-gray-400 hover:text-white transition-colors"
    >
      <X className="w-4 h-4" />
      {children}
    </button>
  );
}
