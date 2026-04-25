'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { vulnsApi } from '@/lib/api';
import { getVulnKnowledge } from '@/lib/vuln-knowledge';
import { SeverityBadge } from '@/components/ui/badge';
import { cvssLabel, formatDateTime } from '@/lib/utils';
import type { Vulnerability } from '@/types';
import {
  ArrowLeft, ExternalLink, Shield, AlertTriangle, Info,
  BookOpen, Code, Link as LinkIcon, Calendar, Scan,
  CheckCircle, XCircle, Flag, Copy, Check,
} from 'lucide-react';

// CVSS color mapping
function cvssColor(score: number): string {
  if (score >= 9.0) return 'text-red-600 dark:text-red-400';
  if (score >= 7.0) return 'text-orange-600 dark:text-orange-400';
  if (score >= 4.0) return 'text-yellow-600 dark:text-yellow-400';
  if (score > 0) return 'text-blue-600 dark:text-blue-400';
  return 'text-gray-500';
}

function remediationPriorityLabel(priority: string | null): string {
  const labels: Record<string, string> = {
    immediate: 'Немедленно',
    short_term: 'В краткосрочной перспективе',
    long_term: 'В долгосрочной перспективе',
  };
  return labels[priority || ''] || priority || '';
}

function remediationPriorityColor(priority: string | null): string {
  const colors: Record<string, string> = {
    immediate: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    short_term: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    long_term: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  };
  return colors[priority || ''] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300';
}

export default function VulnerabilityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vulnId = params.id as string;

  const [vuln, setVuln] = useState<Vulnerability | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(true);

  useEffect(() => {
    vulnsApi
      .get(vulnId)
      .then((resp) => setVuln(resp.data))
      .catch(() => router.push('/vulnerabilities'))
      .finally(() => setLoading(false));
  }, [vulnId]);

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!vuln) return null;

  const knowledge = getVulnKnowledge(vuln.module, vuln.title);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/vulnerabilities"
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <SeverityBadge severity={vuln.severity} />
            {vuln.cvss_score && (
              <span className={`text-sm font-bold ${cvssColor(vuln.cvss_score)}`}>
                CVSS {vuln.cvss_score}
              </span>
            )}
            {vuln.false_positive && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                <Flag className="w-3 h-3" /> False Positive
              </span>
            )}
            {vuln.is_resolved && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                <CheckCircle className="w-3 h-3" /> Resolved
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{vuln.title}</h1>
        </div>
      </div>

      {/* Standards mapping */}
      {(vuln.owasp_category || vuln.cwe_id || vuln.nist_control || vuln.pci_dss_req) && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4" /> Стандарты и классификации
          </h2>
          <div className="flex flex-wrap gap-3">
            {vuln.owasp_category && (
              <div className="px-3 py-1.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <span className="text-xs font-medium text-red-700 dark:text-red-300">
                  OWASP {vuln.owasp_category}
                </span>
                {vuln.owasp_name && (
                  <span className="block text-xs text-red-600 dark:text-red-400 mt-0.5">
                    {vuln.owasp_name}
                  </span>
                )}
              </div>
            )}
            {vuln.cwe_id && (
              <a
                href={`https://cwe.mitre.org/data/definitions/${vuln.cwe_id.replace('CWE-', '')}.html`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors inline-flex items-center gap-1"
              >
                <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                  {vuln.cwe_id}
                </span>
                {vuln.cwe_name && (
                  <span className="text-xs text-yellow-600 dark:text-yellow-400"> — {vuln.cwe_name}</span>
                )}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {vuln.nist_control && (
              <div className="px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                  NIST {vuln.nist_control}
                </span>
              </div>
            )}
            {vuln.pci_dss_req && (
              <div className="px-3 py-1.5 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                  PCI-DSS {vuln.pci_dss_req}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main content: 2 columns — details + knowledge base */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Finding details */}
        <div className="space-y-4">
          {/* Description */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4" /> Описание проблемы
            </h2>
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{vuln.description}</p>
          </div>

          {/* Affected URL */}
          {vuln.affected_url && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Затронутый URL
              </h2>
              <div className="flex items-start gap-2">
                <code className="flex-1 text-xs bg-gray-50 dark:bg-gray-900 px-3 py-2 rounded-lg break-all font-mono">
                  {vuln.affected_url}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(vuln.affected_url!);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  title="Скопировать"
                >
                  {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              {vuln.affected_parameter && (
                <p className="text-xs text-gray-500 mt-2">
                  Параметр: <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{vuln.affected_parameter}</code>
                </p>
              )}
            </div>
          )}

          {/* Evidence */}
          {vuln.evidence && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Доказательство
              </h2>
              <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                {vuln.evidence}
              </pre>
            </div>
          )}

          {/* Meta info */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Calendar className="w-4 h-4" /> Информация
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Модуль</span>
                <span className="text-gray-900 dark:text-white font-mono">{vuln.module}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Скан</span>
                <Link href={`/scans/${vuln.scan_id}`} className="text-blue-600 hover:underline inline-flex items-center gap-1">
                  <Scan className="w-3 h-3" /> {vuln.scan_id.slice(0, 8)}...
                </Link>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Обнаружена</span>
                <span className="text-gray-900 dark:text-white">{formatDateTime(vuln.created_at)}</span>
              </div>
              {vuln.remediation_priority && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Приоритет исправления</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${remediationPriorityColor(vuln.remediation_priority)}`}>
                    {remediationPriorityLabel(vuln.remediation_priority)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Knowledge base + Remediation */}
        <div className="space-y-4">
          {/* Remediation */}
          {vuln.remediation && (
            <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" /> Рекомендация по устранению
              </h2>
              <p className="text-sm text-green-700 dark:text-green-400 leading-relaxed whitespace-pre-wrap">
                {vuln.remediation}
              </p>
            </div>
          )}

          {/* Knowledge Base */}
          {knowledge && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setShowKnowledge(!showKnowledge)}
                className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
              >
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                  <BookOpen className="w-4 h-4" /> База знаний: {knowledge.name}
                </h2>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${showKnowledge ? 'rotate-180' : ''}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showKnowledge && (
                <div className="px-5 pb-5 space-y-5 border-t border-gray-100 dark:border-gray-700 pt-4">
                  {/* What is it */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                      Что это
                    </h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {knowledge.description}
                    </p>
                  </div>

                  {/* How exploited */}
                  <div>
                    <h3 className="text-xs font-semibold text-red-500 dark:text-red-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" /> Чем опасно / Как эксплуатируется
                    </h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {knowledge.exploitation}
                    </p>
                  </div>

                  {/* How to fix */}
                  <div>
                    <h3 className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5" /> Как исправить
                    </h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {knowledge.remediation}
                    </p>
                  </div>

                  {/* Code example */}
                  {knowledge.example && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                        <Code className="w-3.5 h-3.5" /> Пример
                      </h3>
                      <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed border border-gray-200 dark:border-gray-700">
                        {knowledge.example}
                      </pre>
                    </div>
                  )}

                  {/* Links */}
                  {knowledge.links.length > 0 && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                        <LinkIcon className="w-3.5 h-3.5" /> Полезные ссылки
                      </h3>
                      <ul className="space-y-2">
                        {knowledge.links.map((link, i) => (
                          <li key={i}>
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                            >
                              {link.label}
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* No knowledge base entry */}
          {!knowledge && (
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 p-8 text-center">
              <BookOpen className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Запись базы знаний для данного типа уязвимости пока не добавлена.
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Используйте описание и рекомендации выше.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
