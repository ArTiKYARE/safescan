'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { scansApi, reportsApi } from '@/lib/api';
import { ScanStatusBadge, GradeBadge } from '@/components/ui/badge';
import { formatDateTime } from '@/lib/utils';
import type { ScanSummary } from '@/types';
import {
  FileText, Download, ExternalLink, BarChart3, Shield, Calendar, Clock,
  ArrowUpRight, Eye, FileDown, Globe, CheckCircle2, AlertTriangle, Info,
} from 'lucide-react';

const severityColors: Record<string, { text: string; bg: string; bar: string; dot: string }> = {
  critical: { text: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', bar: 'bg-red-500', dot: 'bg-red-500' },
  high: { text: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30', bar: 'bg-orange-500', dot: 'bg-orange-500' },
  medium: { text: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', bar: 'bg-yellow-500', dot: 'bg-yellow-500' },
  low: { text: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30', bar: 'bg-blue-500', dot: 'bg-blue-500' },
  info: { text: 'text-gray-500 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-700/30', bar: 'bg-gray-400', dot: 'bg-gray-400' },
};

const gradeConfig: Record<string, { color: string; bg: string; label: string }> = {
  'A+': { color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30', label: 'Отлично' },
  'A': { color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30', label: 'Отлично' },
  'B': { color: 'text-lime-600 dark:text-lime-400', bg: 'bg-lime-100 dark:bg-lime-900/30', label: 'Хорошо' },
  'C': { color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', label: 'Средне' },
  'D': { color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30', label: 'Плохо' },
  'F': { color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', label: 'Критично' },
};

function getBestGrade(scans: ScanSummary[]): { grade: string; color: string; label: string } {
  const gradeOrder = ['A+', 'A', 'B', 'C', 'D', 'F'];
  const grades = scans.map(s => s.grade).filter(Boolean);
  for (const g of gradeOrder) {
    if (grades.includes(g)) {
      const cfg = gradeConfig[g];
      return { grade: g, color: cfg.color, label: cfg.label };
    }
  }
  return { grade: 'N/A', color: 'text-gray-400', label: '' };
}

export default function ReportsPage() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    scansApi.list({ status: 'completed' })
      .then((r) => setScans(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (scanId: string, format: 'json' | 'pdf' | 'html') => {
    setDownloading(`${scanId}-${format}`);
    try {
      if (format === 'pdf') {
        const resp = await reportsApi.getPdf(scanId);
        const url = URL.createObjectURL(new Blob([resp.data]));
        const a = document.createElement('a');
        a.href = url;
        a.download = `safescan-report-${scanId}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'html') {
        const resp = await reportsApi.getHtml(scanId);
        const win = window.open('', '_blank');
        if (win) win.document.write(resp.data);
      } else {
        const resp = await reportsApi.getJson(scanId);
        const blob = new Blob([JSON.stringify(resp.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `safescan-report-${scanId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setDownloading(null);
    }
  };

  // Aggregate stats
  const totalFindings = scans.reduce((sum, s) => sum + (s.total_findings || 0), 0);
  const totalCritical = scans.reduce((sum, s) => sum + (s.critical_count || 0), 0);
  const totalHigh = scans.reduce((sum, s) => sum + (s.high_count || 0), 0);
  const totalMedium = scans.reduce((sum, s) => sum + (s.medium_count || 0), 0);
  const totalLow = scans.reduce((sum, s) => sum + (s.low_count || 0), 0);
  const totalInfo = scans.reduce((sum, s) => sum + (s.info_count || 0), 0);
  const bestGrade = getBestGrade(scans);

  const domains = [...new Set(scans.map(s => s.domain))];

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Отчёты</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Экспорт результатов сканирования</p>
        </div>
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  if (scans.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Отчёты</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Экспорт результатов сканирования</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-16 text-center">
          <div className="mx-auto w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Нет отчётов</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Завершите сканирование для получения отчёта</p>
          <Link
            href="/scans/new"
            className="inline-flex items-center gap-2 mt-4 text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium"
          >
            Запустить скан
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <FileDown className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Отчёты</h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400">
            Экспорт результатов сканирования в PDF, HTML и JSON
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Сканов</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{scans.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Доменов</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{domains.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Уязвимостей</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalFindings}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Лучшая оценка</span>
          </div>
          <p className={`text-2xl font-bold ${bestGrade.color}`}>{bestGrade.grade}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Critical</span>
          </div>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">{totalCritical}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Info className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Info</span>
          </div>
          <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">{totalInfo}</p>
        </div>
      </div>

      {/* Vulnerability distribution bar */}
      {totalFindings > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Распределение уязвимостей по всем сканам</h3>
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-700 gap-0.5">
            {totalCritical > 0 && (
              <div className={`${severityColors.critical.bar} rounded-l-full transition-all`} style={{ width: `${(totalCritical / totalFindings) * 100}%` }} title={`Critical: ${totalCritical}`} />
            )}
            {totalHigh > 0 && (
              <div className={`${severityColors.high.bar} transition-all`} style={{ width: `${(totalHigh / totalFindings) * 100}%` }} title={`High: ${totalHigh}`} />
            )}
            {totalMedium > 0 && (
              <div className={`${severityColors.medium.bar} transition-all`} style={{ width: `${(totalMedium / totalFindings) * 100}%` }} title={`Medium: ${totalMedium}`} />
            )}
            {totalLow > 0 && (
              <div className={`${severityColors.low.bar} transition-all`} style={{ width: `${(totalLow / totalFindings) * 100}%` }} title={`Low: ${totalLow}`} />
            )}
            {totalInfo > 0 && (
              <div className={`${severityColors.info.bar} rounded-r-full transition-all`} style={{ width: `${(totalInfo / totalFindings) * 100}%` }} title={`Info: ${totalInfo}`} />
            )}
          </div>
          <div className="flex flex-wrap gap-4 mt-3">
            {[
              { label: 'Critical', count: totalCritical, color: severityColors.critical.dot },
              { label: 'High', count: totalHigh, color: severityColors.high.dot },
              { label: 'Medium', count: totalMedium, color: severityColors.medium.dot },
              { label: 'Low', count: totalLow, color: severityColors.low.dot },
              { label: 'Info', count: totalInfo, color: severityColors.info.dot },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                <span>{item.label}</span>
                <span className="font-semibold text-gray-700 dark:text-gray-300">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scan report cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Сканы ({scans.length})
        </h2>
        <div className="space-y-3">
          {scans.map((scan) => {
            const findings = scan.total_findings || 0;
            const crit = scan.critical_count || 0;
            const high = scan.high_count || 0;
            const med = scan.medium_count || 0;
            const low = scan.low_count || 0;
            const info = scan.info_count || 0;
            const maxBar = Math.max(crit, high, med, low, info, 1);

            return (
              <div
                key={scan.id}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Top section */}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                          {scan.domain}
                        </h3>
                        <GradeBadge grade={scan.grade} />
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDateTime(scan.completed_at)}
                        </span>
                        {scan.scan_type && (
                          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-medium capitalize">
                            {scan.scan_type}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Link
                        href={`/scans/${scan.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Детали</span>
                      </Link>
                    </div>
                  </div>

                  {/* Findings bar */}
                  {findings > 0 && (
                    <div className="mb-4">
                      <div className="flex h-2 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-700 gap-px">
                        {crit > 0 && <div className={`${severityColors.critical.bar} rounded-l-full`} style={{ width: `${(crit / findings) * 100}%` }} />}
                        {high > 0 && <div className={`${severityColors.high.bar}`} style={{ width: `${(high / findings) * 100}%` }} />}
                        {med > 0 && <div className={`${severityColors.medium.bar}`} style={{ width: `${(med / findings) * 100}%` }} />}
                        {low > 0 && <div className={`${severityColors.low.bar}`} style={{ width: `${(low / findings) * 100}%` }} />}
                        {info > 0 && <div className={`${severityColors.info.bar} rounded-r-full`} style={{ width: `${(info / findings) * 100}%` }} />}
                      </div>
                    </div>
                  )}

                  {/* Severity counts as mini bar chart */}
                  <div className="grid grid-cols-5 gap-2">
                    {[
                      { label: 'C', value: crit, color: severityColors.critical, full: 'Critical' },
                      { label: 'H', value: high, color: severityColors.high, full: 'High' },
                      { label: 'M', value: med, color: severityColors.medium, full: 'Medium' },
                      { label: 'L', value: low, color: severityColors.low, full: 'Low' },
                      { label: 'I', value: info, color: severityColors.info, full: 'Info' },
                    ].map(item => (
                      <div key={item.label} className="flex flex-col items-center">
                        <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-sm h-6 flex items-end overflow-hidden">
                          <div
                            className={`${item.color.bar} w-full transition-all`}
                            style={{ height: item.value > 0 ? `${Math.max((item.value / maxBar) * 100, 15)}%` : '0%' }}
                          />
                        </div>
                        <span className={`text-xs font-semibold mt-1 ${item.color.text}`}>{item.value}</span>
                        <span className="text-[10px] text-gray-400">{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Download buttons */}
                <div className="px-5 py-3 bg-gray-50 dark:bg-gray-800/80 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <FileText className="w-3.5 h-3.5" />
                    <span>Экспорт:</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDownload(scan.id, 'json')}
                      disabled={downloading === `${scan.id}-json`}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                    >
                      <Download className="w-3 h-3" />
                      JSON
                    </button>
                    <button
                      onClick={() => handleDownload(scan.id, 'html')}
                      disabled={downloading === `${scan.id}-html`}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                    >
                      <ExternalLink className="w-3 h-3" />
                      HTML
                    </button>
                    <button
                      onClick={() => handleDownload(scan.id, 'pdf')}
                      disabled={downloading === `${scan.id}-pdf`}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 shadow-sm"
                    >
                      <Download className="w-3 h-3" />
                      PDF
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
