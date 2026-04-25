'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { scansApi, vulnsApi, reportsApi } from '@/lib/api';
import { ScanStatusBadge, SeverityBadge, GradeBadge } from '@/components/ui/badge';
import { formatDateTime, timeAgo, cvssLabel } from '@/lib/utils';
import { ArrowLeft, Download, ExternalLink, RefreshCw, Shield, AlertTriangle, Terminal, ChevronDown, ChevronUp, Clock, Eye, ArrowUpRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Scan, Vulnerability } from '@/types';

interface ScanLog {
  timestamp: string;
  level: string;
  module: string | null;
  message: string;
}

/* ── Severity card colors (same as vulnerabilities page) ── */
const severityCardColors: Record<string, { left: string; bg: string; text: string; badge: string; lightBg: string }> = {
  critical: {
    left: 'border-l-red-500',
    bg: 'bg-red-50 dark:bg-red-950/30',
    text: 'text-red-600 dark:text-red-400',
    badge: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    lightBg: 'bg-red-50 dark:bg-red-950/20',
  },
  high: {
    left: 'border-l-orange-500',
    bg: 'bg-orange-50 dark:bg-orange-950/30',
    text: 'text-orange-600 dark:text-orange-400',
    badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
    lightBg: 'bg-orange-50 dark:bg-orange-950/20',
  },
  medium: {
    left: 'border-l-yellow-500',
    bg: 'bg-yellow-50 dark:bg-yellow-950/30',
    text: 'text-yellow-600 dark:text-yellow-400',
    badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    lightBg: 'bg-yellow-50 dark:bg-yellow-950/20',
  },
  low: {
    left: 'border-l-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    text: 'text-blue-600 dark:text-blue-400',
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    lightBg: 'bg-blue-50 dark:bg-blue-950/20',
  },
  info: {
    left: 'border-l-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-800/50',
    text: 'text-gray-500 dark:text-gray-400',
    badge: 'bg-gray-100 text-gray-600 dark:bg-gray-700/60 dark:text-gray-300',
    lightBg: 'bg-gray-50 dark:bg-gray-800/30',
  },
};

function cvssColor(score: number): string {
  if (score >= 9) return 'text-red-600 dark:text-red-400';
  if (score >= 7) return 'text-orange-600 dark:text-orange-400';
  if (score >= 4) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-blue-600 dark:text-blue-400';
}

function severityLabel(sev: string): string {
  const labels: Record<string, string> = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    info: 'Info',
  };
  return labels[sev] || sev;
}

export default function ScanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [scan, setScan] = useState<Scan | null>(null);
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  // Scan logs
  const [logs, setLogs] = useState<ScanLog[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [autoScrollLogs, setAutoScrollLogs] = useState(true);
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  const fetchData = async () => {
    try {
      const [scanResp, vulnsResp] = await Promise.all([
        scansApi.get(scanId),
        vulnsApi.list({ scan_id: scanId }),
      ]);
      setScan(scanResp.data);
      setVulns(vulnsResp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [scanId]);

  // Fetch scan logs
  const fetchLogs = async () => {
    try {
      const resp = await scansApi.getLogs(scanId, 0, 500);
      setLogs(resp.data.logs || []);
    } catch (e) {
      // Logs may not be available yet
    }
  };

  // Auto-scroll logs
  useEffect(() => {
    if (autoScrollLogs && logsEndRef.current && showLogs) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScrollLogs, showLogs]);

  // Auto-refresh for running scans
  useEffect(() => {
    if (scan?.status !== 'running' && scan?.status !== 'queued') return;
    const interval = setInterval(() => {
      fetchData();
      if (showLogs) fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [scan?.status, showLogs]);

  const toggleExpand = (id: string) => {
    setExpandedVuln(expandedVuln === id ? null : id);
  };

  const handleDownload = async (format: 'json' | 'pdf' | 'html') => {
    setDownloading(format);
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

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  if (!scan) {
    return (
      <div className="text-center py-12">
        <Shield className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Скан не найден</h3>
        <Button variant="ghost" onClick={() => router.back()} className="mt-4">Назад</Button>
      </div>
    );
  }

  const isRunning = scan.status === 'running' || scan.status === 'queued';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-4">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600 mt-1">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{scan.domain}</h1>
              <ScanStatusBadge status={scan.status} />
              <GradeBadge grade={scan.grade} />
            </div>
            <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">
              Скан {scan.scan_type} • Создан {formatDateTime(scan.created_at)}
              {scan.started_at && ` • Запущен ${formatDateTime(scan.started_at)}`}
              {scan.completed_at && ` • Завершён ${formatDateTime(scan.completed_at)}`}
            </p>
          </div>
        </div>
        {scan.status === 'completed' && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" isLoading={downloading === 'json'} onClick={() => handleDownload('json')}>
              <Download className="w-3 h-3 mr-1" /> JSON
            </Button>
            <Button variant="outline" size="sm" isLoading={downloading === 'html'} onClick={() => handleDownload('html')}>
              <ExternalLink className="w-3 h-3 mr-1" /> HTML
            </Button>
            <Button variant="outline" size="sm" isLoading={downloading === 'pdf'} onClick={() => handleDownload('pdf')}>
              <Download className="w-3 h-3 mr-1" /> PDF
            </Button>
          </div>
        )}
      </div>

      {/* Progress */}
      {isRunning && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              {scan.current_module || 'Запуск...'}
            </span>
            <span className="text-sm text-gray-500">{scan.progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${scan.progress_percentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Страниц просканировано: {scan.pages_crawled} • Запросов: {scan.requests_made}
          </p>
        </div>
      )}

      {/* Error */}
      {scan.status === 'failed' && scan.error_message && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка сканирования</h4>
              <p className="text-xs text-red-600 dark:text-red-400 mt-1 font-mono">{scan.error_message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Scan Logs */}
      {isRunning && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <button
            onClick={() => {
              setShowLogs(!showLogs);
              if (!showLogs && logs.length === 0) fetchLogs();
            }}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Terminal className="w-5 h-5 text-gray-400" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                Логи сканирования
              </h3>
              {logs.length > 0 && (
                <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-full">
                  {logs.length} записей
                </span>
              )}
            </div>
            {showLogs ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>

          {showLogs && (
            <>
              <div className="px-6 pb-3 flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoScrollLogs}
                    onChange={(e) => setAutoScrollLogs(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  Автопрокрутка
                </label>
                <button
                  onClick={fetchLogs}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Обновить
                </button>
              </div>
              <div
                ref={logsContainerRef}
                className="max-h-80 overflow-y-auto bg-gray-950 px-4 py-3 font-mono text-xs border-t border-gray-200 dark:border-gray-700"
              >
                {logs.length === 0 ? (
                  <div className="flex items-center gap-2 text-gray-500">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    <p>Загрузка логов...</p>
                  </div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="flex gap-3 py-0.5 leading-relaxed">
                      <span className="text-gray-600 flex-shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`flex-shrink-0 w-12 ${
                        log.level === 'ERROR' ? 'text-red-400' :
                        log.level === 'WARN' ? 'text-yellow-400' :
                        log.level === 'WARNING' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        [{log.level}]
                      </span>
                      {log.module && (
                        <span className="text-blue-400 flex-shrink-0">
                          [{log.module}]
                        </span>
                      )}
                      <span className="text-gray-300 break-all">{log.message}</span>
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </>
          )}
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Всего', value: scan.total_findings, color: 'text-gray-900 dark:text-white' },
          { label: 'Critical', value: scan.critical_count, color: 'text-red-600' },
          { label: 'High', value: scan.high_count, color: 'text-orange-600' },
          { label: 'Medium', value: scan.medium_count, color: 'text-yellow-600' },
          { label: 'Low', value: scan.low_count, color: 'text-blue-600' },
          { label: 'Info', value: scan.info_count, color: 'text-gray-500' },
        ].map((s) => (
          <div key={s.label} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Risk Score */}
      {scan.risk_score !== null && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Risk Score</p>
              <p className="text-4xl font-bold text-gray-900 dark:text-white">{scan.risk_score}<span className="text-lg text-gray-400">/10</span></p>
            </div>
            <div className={`text-6xl font-black ${scan.grade ? `text-${scan.grade === 'A+' || scan.grade === 'A' ? 'green' : scan.grade === 'B' ? 'lime' : scan.grade === 'C' ? 'yellow' : scan.grade === 'D' ? 'orange' : 'red'}-500` : 'text-gray-400'}`}>
              {scan.grade || 'N/A'}
            </div>
          </div>
        </div>
      )}

      {/* Vulnerabilities */}
      <div className="space-y-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Уязвимости ({vulns.length})
          </h3>
        </div>

        {vulns.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-16 text-center">
            {isRunning ? (
              <div className="flex items-center justify-center gap-2 text-gray-400">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <p>Сканирование в процессе...</p>
              </div>
            ) : (
              <>
                <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                  <Shield className="w-8 h-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Уязвимостей не обнаружено</h3>
                <p className="text-gray-500 dark:text-gray-400 mt-1">Отличный результат! Ваш ресурс в безопасности 🎉</p>
              </>
            )}
          </div>
        ) : (
          vulns.map((v) => {
            const colors = severityCardColors[v.severity] || severityCardColors.info;
            const isExpanded = expandedVuln === v.id;

            return (
              <div
                key={v.id}
                className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden border-l-4 ${colors.left} transition-shadow duration-200 hover:shadow-md`}
              >
                {/* Main row */}
                <div className="flex items-stretch">
                  {/* Severity badge stripe */}
                  <div className={`hidden sm:flex flex-col items-center justify-center w-24 py-5 ${colors.bg} border-r border-gray-100 dark:border-gray-700`}>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors.badge}`}>
                      {severityLabel(v.severity)}
                    </span>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 px-5 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                          {v.title}
                        </h3>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                          <span className="text-xs text-gray-400">{v.module}</span>
                          {v.cvss_score != null && (
                            <span className={`text-xs font-bold ${cvssColor(v.cvss_score)}`}>
                              CVSS {v.cvss_score}
                            </span>
                          )}
                          {v.owasp_category && (
                            <span className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 font-medium">
                              {v.owasp_category}
                            </span>
                          )}
                          {v.cwe_id && (
                            <span className="text-xs px-2 py-0.5 rounded bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 font-medium">
                              {v.cwe_id}
                            </span>
                          )}
                          {v.created_at && (
                            <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                              <Clock className="w-3 h-3" />
                              {formatDateTime(v.created_at)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Link
                          href={`/vulnerabilities/${v.id}`}
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Подробнее</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                        <button
                          onClick={() => toggleExpand(v.id)}
                          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="border-t border-gray-100 dark:border-gray-700">
                    <div className="px-5 py-5 space-y-5">
                      {/* Description */}
                      <div>
                        <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                          Описание
                        </h4>
                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                          {v.description}
                        </p>
                      </div>

                      {/* Affected URL + Parameter */}
                      {v.affected_url && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div>
                            <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                              Затронутый URL
                            </h4>
                            <code className="block text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 px-3 py-2 rounded-lg break-all font-mono">
                              {v.affected_url}
                            </code>
                          </div>
                          {v.affected_parameter && (
                            <div>
                              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                                Параметр
                              </h4>
                              <code className="block text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 px-3 py-2 rounded-lg font-mono">
                                {v.affected_parameter}
                              </code>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Evidence */}
                      {v.evidence && (
                        <div>
                          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                            Доказательство
                          </h4>
                          <pre className="text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                            {v.evidence}
                          </pre>
                        </div>
                      )}

                      {/* Remediation */}
                      {v.remediation && (
                        <div className="rounded-xl bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/50 p-4">
                          <h4 className="text-xs font-semibold uppercase tracking-wide text-green-700 dark:text-green-400 mb-2">
                            🛡️ Рекомендация
                          </h4>
                          <p className="text-sm text-green-700 dark:text-green-400 leading-relaxed whitespace-pre-wrap">
                            {v.remediation}
                          </p>
                        </div>
                      )}

                      {/* Standards footer */}
                      {(v.cwe_id || v.nist_control || v.pci_dss_req) && (
                        <div className="flex flex-wrap gap-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                          {v.cwe_id && (
                            <span className="text-xs text-gray-400">
                              CWE:{' '}
                              <span className="text-gray-600 dark:text-gray-300 font-medium">
                                {v.cwe_id}{v.cwe_name ? ` — ${v.cwe_name}` : ''}
                              </span>
                            </span>
                          )}
                          {v.nist_control && (
                            <span className="text-xs text-gray-400">
                              NIST:{' '}
                              <span className="text-gray-600 dark:text-gray-300 font-medium">{v.nist_control}</span>
                            </span>
                          )}
                          {v.pci_dss_req && (
                            <span className="text-xs text-gray-400">
                              PCI-DSS:{' '}
                              <span className="text-gray-600 dark:text-gray-300 font-medium">{v.pci_dss_req}</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
