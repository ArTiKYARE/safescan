'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { vulnsApi } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import type { Vulnerability } from '@/types';
import {
  Bug, Filter, ChevronDown, ChevronUp, ArrowUpRight, Clock, Eye,
} from 'lucide-react';

const severityColors: Record<string, { left: string; bg: string; text: string; badge: string; lightBg: string }> = {
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

export default function VulnerabilitiesPage() {
  const [allVulns, setAllVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);

  // Fetch all vulnerabilities once
  useEffect(() => {
    vulnsApi.list({})
      .then((r) => setAllVulns(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Filter locally
  const vulns = severityFilter
    ? allVulns.filter((v) => v.severity === severityFilter)
    : allVulns;

  const toggleExpand = (id: string) => {
    setExpandedVuln(expandedVuln === id ? null : id);
  };

  // Counts per severity — always computed from ALL vulns, not filtered
  const sevCounts = ['critical', 'high', 'medium', 'low', 'info']
    .map((sev) => ({ sev, count: allVulns.filter((v) => v.severity === sev).length }));

  /* ── loading ── */
  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Уязвимости</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Все обнаруженные уязвимости</p>
        </div>
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  /* ── empty state ── */
  if (allVulns.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Уязвимости</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Все обнаруженные уязвимости</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-16 text-center">
          <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
            <Bug className="w-8 h-8 text-green-600 dark:text-green-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Уязвимостей не обнаружено</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Отличный результат! Ваш ресурс в безопасности 🎉</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Уязвимости</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {severityFilter
            ? `${vulns.length} из ${allVulns.length} — показаны «${severityLabel(severityFilter)}»`
            : `${vulns.length} ${vulns.length === 1 ? 'уязвимость' : vulns.length < 5 ? 'уязвимости' : 'уязвимостей'} обнаружено`
          }
        </p>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Total */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{allVulns.length}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">Всего</p>
        </div>
        {sevCounts.map(({ sev, count }) => {
          const c = severityColors[sev] || severityColors.info;
          const isActive = severityFilter === sev;
          if (count === 0 && !isActive) return null;
          return (
            <button
              key={sev}
              onClick={() => setSeverityFilter(isActive ? '' : sev)}
              className={`rounded-xl border p-4 text-center transition-all duration-200 ${
                isActive
                  ? `${c.lightBg} ${c.badge} ring-1 ring-offset-1 ring-current`
                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <p className={`text-3xl font-bold ${c.text}`}>{count}</p>
              <p className={`text-xs font-medium mt-1 ${isActive ? c.text : 'text-gray-500 dark:text-gray-400'}`}>
                {severityLabel(sev)}
              </p>
            </button>
          );
        })}
      </div>

      {/* Active filter indicator */}
      {severityFilter && (
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Фильтр:{' '}
            <span className={`font-medium ${severityColors[severityFilter]?.text || ''}`}>
              {severityLabel(severityFilter)}
            </span>
          </span>
          <button
            onClick={() => setSeverityFilter('')}
            className="ml-2 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 underline"
          >
            Сбросить
          </button>
        </div>
      )}

      {/* Vulnerability cards */}
      <div className="space-y-3">
        {vulns.length === 0 && severityFilter && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              Нет уязвимостей категории «<span className={severityColors[severityFilter]?.text}>{severityLabel(severityFilter)}</span>»
            </p>
            <button
              onClick={() => setSeverityFilter('')}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-2"
            >
              Сбросить фильтр
            </button>
          </div>
        )}
        {vulns.map((v) => {
          const colors = severityColors[v.severity] || severityColors.info;
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
                  {/* Title + tags */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {v.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                        {/* Module */}
                        <span className="text-xs text-gray-400">{v.module}</span>
                        {/* CVSS */}
                        {v.cvss_score != null && (
                          <span className={`text-xs font-bold ${cvssColor(v.cvss_score)}`}>
                            CVSS {v.cvss_score}
                          </span>
                        )}
                        {/* OWASP */}
                        {v.owasp_category && (
                          <span className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 font-medium">
                            {v.owasp_category}
                          </span>
                        )}
                        {/* CWE */}
                        {v.cwe_id && (
                          <span className="text-xs px-2 py-0.5 rounded bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 font-medium">
                            {v.cwe_id}
                          </span>
                        )}
                        {/* Date */}
                        <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                          <Clock className="w-3 h-3" />
                          {formatDateTime(v.created_at)}
                        </span>
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
        })}
      </div>
    </div>
  );
}
