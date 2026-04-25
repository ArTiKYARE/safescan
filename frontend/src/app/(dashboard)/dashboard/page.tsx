'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { scansApi, vulnsApi, domainsApi } from '@/lib/api';
import { StatCard } from '@/components/ui/card';
import { SeverityBadge, ScanStatusBadge, GradeBadge } from '@/components/ui/badge';
import { Shield, Globe, ScanLine, Bug, AlertTriangle, TrendingUp, ArrowRight, Plus } from 'lucide-react';
import { formatDateTime, timeAgo, severityColor, gradeColor } from '@/lib/utils';
import type { ScanSummary, VulnerabilitySummary, Domain } from '@/types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [vulnSummary, setVulnSummary] = useState<VulnerabilitySummary | null>(null);
  const [domains, setDomains] = useState<Domain[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [scansResp, vulnsResp, domainsResp] = await Promise.all([
          scansApi.list().catch(() => ({ data: [] })),
          vulnsApi.summary().catch(() => ({ data: null })),
          domainsApi.list().catch(() => ({ data: [] })),
        ]);
        setScans(scansResp.data || []);
        setVulnSummary(vulnsResp.data);
        setDomains(domainsResp.data || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const verifiedDomains = domains.filter((d) => d.is_verified);
  const activeScans = scans.filter((s) => s.status === 'running' || s.status === 'queued');

  const chartData = vulnSummary
    ? [
        { name: 'Critical', value: vulnSummary.critical, fill: '#dc2626' },
        { name: 'High', value: vulnSummary.high, fill: '#ea580c' },
        { name: 'Medium', value: vulnSummary.medium, fill: '#d97706' },
        { name: 'Low', value: vulnSummary.low, fill: '#2563eb' },
        { name: 'Info', value: vulnSummary.info, fill: '#6b7280' },
      ]
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Обзор безопасности ваших ресурсов</p>
        </div>
        <Link href="/scans/new">
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
            <Plus className="w-4 h-4" />
            Новый скан
          </button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Всего сканов"
          value={scans.length}
          icon={<ScanLine className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Активных сканов"
          value={activeScans.length}
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          title="Доменов"
          value={`${verifiedDomains.length} / ${domains.length}`}
          icon={<Globe className="w-5 h-5" />}
          color="purple"
        />
        <StatCard
          title="Уязвимостей"
          value={vulnSummary?.total || 0}
          icon={<Bug className="w-5 h-5" />}
          color={vulnSummary && vulnSummary.critical > 0 ? 'red' : 'yellow'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Chart */}
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Распределение по критичности</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              <Shield className="w-12 h-12 mb-2" />
              <p>Нет данных</p>
            </div>
          )}
        </div>

        {/* Recent Scans */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Последние сканы</h3>
            <Link href="/scans" className="text-sm text-blue-600 hover:text-blue-500 flex items-center gap-1">
              Все сканы <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {scans.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <ScanLine className="w-10 h-10 mx-auto mb-2 opacity-50" />
                <p>Сканов пока нет</p>
                <Link href="/scans/new" className="text-blue-600 text-sm mt-2 inline-block">
                  Запустить первый скан →
                </Link>
              </div>
            ) : (
              scans.slice(0, 5).map((scan) => (
                <div key={scan.id} className="px-6 py-3 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{scan.domain}</p>
                      <GradeBadge grade={scan.grade} />
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {scan.completed_at ? formatDateTime(scan.completed_at) : 'В процессе...'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {scan.critical_count > 0 && (
                      <span className="text-xs text-red-600 font-medium">{scan.critical_count} crit</span>
                    )}
                    <span className="text-xs text-gray-500">{scan.total_findings} findings</span>
                    <ScanStatusBadge status={scan.status} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Domains overview */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Домены</h3>
          <Link href="/domains" className="text-sm text-blue-600 hover:text-blue-500 flex items-center gap-1">
            Управление <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        {domains.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <Globe className="w-10 h-10 mx-auto mb-2 opacity-50" />
            <p>Нет добавленных доменов</p>
            <Link href="/domains" className="text-blue-600 text-sm mt-2 inline-block">
              Добавить домен →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {domains.slice(0, 5).map((domain) => (
              <div key={domain.id} className="px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{domain.domain}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${domain.is_verified ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'}`}>
                  {domain.is_verified ? 'Верифицирован' : 'Не верифицирован'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
