'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { scansApi } from '@/lib/api';
import { ScanStatusBadge, GradeBadge } from '@/components/ui/badge';
import { formatDateTime } from '@/lib/utils';
import { ScanLine, Plus, ExternalLink } from 'lucide-react';
import type { ScanSummary } from '@/types';

export default function ScansPage() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');

  const fetchScans = async () => {
    try {
      const params = filter ? { status: filter } : {};
      const resp = await scansApi.list(params);
      setScans(resp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchScans(); }, [filter]);

  // Poll for running scans
  useEffect(() => {
    const hasRunning = scans.some((s) => s.status === 'running' || s.status === 'queued');
    if (!hasRunning) return;
    const interval = setInterval(fetchScans, 5000);
    return () => clearInterval(interval);
  }, [scans]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Сканы</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">История сканирований уязвимостей</p>
        </div>
        <Link href="/scans/new">
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
            <Plus className="w-4 h-4" />
            Новый скан
          </button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['', 'running', 'completed', 'failed', 'queued'].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === s
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {s || 'Все'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
      ) : scans.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <ScanLine className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Нет сканов</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Запустите первый скан уязвимостей</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          {/* Table header */}
          <div className="hidden sm:grid sm:grid-cols-6 gap-4 px-6 py-3 border-b border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            <div className="col-span-2">Домен</div>
            <div>Тип</div>
            <div>Статус</div>
            <div>Результат</div>
            <div>Завершён</div>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {scans.map((scan) => (
              <Link
                key={scan.id}
                href={`/scans/${scan.id}`}
                className="grid sm:grid-cols-6 gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors cursor-pointer"
              >
                <div className="sm:col-span-2">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{scan.domain}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 sm:hidden">
                    {scan.completed_at ? formatDateTime(scan.completed_at) : '...'}
                  </p>
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{scan.scan_type}</span>
                </div>
                <div className="flex items-center">
                  <ScanStatusBadge status={scan.status} />
                </div>
                <div className="flex items-center gap-2">
                  <GradeBadge grade={scan.grade} />
                  {scan.critical_count > 0 && (
                    <span className="text-xs text-red-600 font-medium">{scan.critical_count} crit</span>
                  )}
                  <span className="text-xs text-gray-500">{scan.total_findings}</span>
                </div>
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                  {scan.completed_at ? formatDateTime(scan.completed_at) : '—'}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
