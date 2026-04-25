'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';

const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  domains: 'Домены',
  scans: 'Сканы',
  vulnerabilities: 'Уязвимости',
  reports: 'Отчёты',
  settings: 'Настройки',
  'api-keys': 'API ключи',
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  // Убираем группу роутов (dashboard)
  const cleaned = segments.filter((s) => !s.startsWith('('));

  if (cleaned.length === 0) return null;

  return (
    <nav className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 mb-4">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
      >
        <Home className="w-4 h-4" />
      </Link>

      {cleaned.map((segment, i) => {
        const isLast = i === cleaned.length - 1;
        const label = routeLabels[segment] || segment;

        // Пропускаем dashboard как корневой сегмент
        if (segment === 'dashboard') return null;

        // UUID-сегменты (id записей) — показываем сокращённо
        const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment);
        if (isUuid) return null;

        const href = `/${cleaned.slice(0, i + 1).join('/')}`;

        return (
          <span key={segment} className="inline-flex items-center gap-1.5">
            <ChevronRight className="w-3.5 h-3.5 text-gray-300 dark:text-gray-600" />
            {isLast ? (
              <span className="text-gray-900 dark:text-white font-medium">{label}</span>
            ) : (
              <Link
                href={href}
                className="hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              >
                {label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
