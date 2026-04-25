'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { scansApi, domainsApi } from '@/lib/api';
import { useAuthStore } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ArrowLeft, Shield, AlertTriangle, CheckCircle, Loader2, Wallet, Gift, CreditCard } from 'lucide-react';
import type { Domain } from '@/types';

const FULL_MODULES = [
  { key: 'security_headers', label: 'Security Headers', desc: 'HSTS, CSP, X-Frame-Options и др.' },
  { key: 'ssl_tls', label: 'SSL/TLS', desc: 'Протоколы, шифры, сертификаты' },
  { key: 'xss', label: 'XSS', desc: 'Reflected, Stored, DOM-based' },
  { key: 'injection', label: 'Injection', desc: 'SQLi, NoSQLi, Command, LDAP, SSTI' },
  { key: 'csrf_cors', label: 'CSRF/CORS', desc: 'CSRF-токены, CORS misconfig' },
  { key: 'ssrf_xxe_traversal', label: 'SSRF/XXE/Traversal', desc: 'SSRF, XXE, Path Traversal' },
  { key: 'auth_sessions', label: 'Auth & Sessions', desc: 'Cookies, JWT, MFA, Brute-force' },
  { key: 'server_config', label: 'Server Config', desc: 'Directory listing, Debug endpoints' },
  { key: 'sca', label: 'SCA', desc: 'Уязвимые зависимости, CMS' },
  { key: 'info_leakage', label: 'Info Leakage', desc: '.git, .env, API keys, backup' },
  { key: 'app_logic', label: 'App Logic', desc: 'IDOR, Rate limits, Escalation' },
  { key: 'network', label: 'Network', desc: 'DNS, CDN/WAF, Subdomains' },
];

export default function NewScanPage() {
  const router = useRouter();
  const { user, loadUser } = useAuthStore();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [scanType, setScanType] = useState<'full' | 'quick' | 'custom'>('full');
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUser();
    domainsApi.list().then((r) => {
      setDomains(r.data);
      if (r.data.length > 0) setSelectedDomain(r.data[0].id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (scanType === 'full') {
      setSelectedModules(FULL_MODULES.map((m) => m.key));
    } else if (scanType === 'quick') {
      setSelectedModules(['security_headers', 'ssl_tls', 'server_config', 'info_leakage']);
    }
  }, [scanType]);

  const toggleModule = (key: string) => {
    setSelectedModules((prev) =>
      prev.includes(key) ? prev.filter((m) => m !== key) : [...prev, key]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDomain) return setError('Выберите домен');
    if (!consent) return setError('Подтвердите согласие на сканирование');
    if (scanType === 'custom' && selectedModules.length === 0) return setError('Выберите хотя бы один модуль');

    setSubmitting(true);
    setError('');

    try {
      const resp = await scansApi.create({
        domain_id: selectedDomain,
        scan_type: scanType,
        consent_acknowledged: true,
      });
      router.push(`/scans/${resp.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка запуска скана');
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Новый скан</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Настройка и запуск сканирования уязвимостей</p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {domains.length === 0 ? (
        <Card title="Нет доменов">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Для запуска скана необходимо добавить домен.
          </p>
          <Button onClick={() => router.push('/domains')}>Перейти к доменам</Button>
        </Card>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Domain selection */}
          <Card title="1. Выберите домен">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {domains.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setSelectedDomain(d.id)}
                  className={`p-4 rounded-lg border text-left transition-colors ${
                    selectedDomain === d.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10 dark:border-blue-600'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{d.domain}</p>
                </button>
              ))}
            </div>
          </Card>

          {/* Scan type */}
          <Card title="2. Тип сканирования">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                {
                  key: 'quick' as const,
                  label: 'Быстрый',
                  desc: '4 модуля, ~30 сек',
                  icon: '⚡',
                  price: (user?.free_scans_remaining || 0) > 0 ? 0 : 10,
                  freeRemaining: user?.free_scans_remaining || 0,
                },
                {
                  key: 'full' as const,
                  label: 'Полный',
                  desc: '12 модулей, ~2 мин',
                  icon: '🔍',
                  price: 20,
                  recommended: true,
                },
                {
                  key: 'custom' as const,
                  label: 'Пользовательский',
                  desc: 'Выберите модули',
                  icon: '⚙️',
                  price: 20,
                },
              ].map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setScanType(t.key)}
                  className={`p-4 rounded-lg border text-left transition-colors relative ${
                    scanType === t.key
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10 dark:border-blue-600'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                  }`}
                >
                  {(t as any).recommended && (
                    <span className="absolute top-2 right-2 text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">Рекомендуется</span>
                  )}
                  <p className="text-lg mb-1">{t.icon}</p>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{t.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t.desc}</p>
                  <div className="mt-3 flex items-center gap-1.5">
                    {(t as any).freeRemaining > 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/30 px-2 py-1 rounded-full">
                        <Gift className="w-3 h-3" />
                        {(t as any).freeRemaining} бесплатных сканов
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
                        <CreditCard className="w-3 h-3" />
                        {t.price} ₽
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </Card>

          {/* Custom modules */}
          {scanType === 'custom' && (
            <Card title="3. Выберите модули">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {FULL_MODULES.map((m) => (
                  <label
                    key={m.key}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedModules.includes(m.key)
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10 dark:border-blue-600'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedModules.includes(m.key)}
                      onChange={() => toggleModule(m.key)}
                      className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{m.label}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{m.desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </Card>
          )}

          {/* Consent */}
          <Card>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Подтверждение владения доменом
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Я подтверждаю, что являюсь владельцем или имею письменное согласие владельца
                  домена на проведение сканирования безопасности. Сканирование без согласия
                  является незаконным.
                </p>
              </div>
            </label>
          </Card>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="ghost" onClick={() => router.back()}>Отмена</Button>
            <Button type="submit" isLoading={submitting} size="lg">
              <Shield className="w-4 h-4 mr-2" />
              Запустить скан
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
