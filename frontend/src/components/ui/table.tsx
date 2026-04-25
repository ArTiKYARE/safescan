import React from 'react';
import { cn } from '@/lib/utils';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export function Table({ children, className }: TableProps) {
  return (
    <div className="w-full overflow-auto">
      <table className={cn('w-full text-sm', className)}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className }: TableProps) {
  return (
    <thead className={cn('bg-security-border/50', className)}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className }: TableProps) {
  return (
    <tbody className={cn('divide-y divide-security-border', className)}>
      {children}
    </tbody>
  );
}

export function TableRow({ children, className }: TableProps) {
  return (
    <tr className={cn('hover:bg-security-border/30 transition-colors', className)}>
      {children}
    </tr>
  );
}

export function TableHead({ children, className }: TableProps) {
  return (
    <th className={cn('px-4 py-3 text-left font-medium text-gray-400 uppercase tracking-wider text-xs', className)}>
      {children}
    </th>
  );
}

export function TableCell({ children, className }: TableProps) {
  return (
    <td className={cn('px-4 py-3 text-gray-300', className)}>
      {children}
    </td>
  );
}
