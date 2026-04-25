'use client';

import React, { useEffect, useState } from 'react';
import { apiKeysApi } from '@/lib/api';
import { Key, Trash2, Copy, CheckCircle, Globe, Link2, Eye, EyeOff } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';
import type { APIKey } from '@/types';

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [revealingKey, setRevealingKey] = useState<string | null>(null);

  const fetchKeys = async () => {
    try {
      const resp = await apiKeysApi.list();
      setKeys(resp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKeys(); }, []);

  const handleRevoke = async (id: string) => {
    if (!confirm('Удалить этот API ключ? Он перестанет работать и будет полностью удалён.')) return;
    try {
      await apiKeysApi.revoke(id);
      setRevealedKey(null);
      await fetchKeys();
    } catch (e) {
      console.error(e);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleReveal = (secret: string, id: string) => {
    setRevealedKey(revealedKey === id ? null : id);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API ключи</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Ключи для программного доступа к API</p>
      </div>

      {/* Info banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50 rounded-xl p-5 flex items-start gap-3">
        <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-800 dark:text-blue-300">Автоматическая генерация</p>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            API ключи создаются автоматически при добавлении домена с методом «API Token».
            Скопируйте ключ и добавьте его в <code className="bg-blue-100 dark:bg-blue-800/50 px-1.5 py-0.5 rounded font-mono">.env</code> вашего сайта:
          </p>
          <code className="block text-xs bg-blue-100 dark:bg-blue-800/30 px-3 py-2 rounded-lg mt-2 font-mono text-blue-700 dark:text-blue-300">
            SAFESCAN_API_KEY="sk_example.com_abc123..."
          </code>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
      ) : keys.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
            <Key className="w-7 h-7 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Нет API ключей</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Добавьте домен с методом «API Token» — ключ создастся автоматически
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {keys
              .filter((key) => !key.is_revoked && key.is_active)
              .map((key) => {
                const isRevealed = revealedKey === key.id;

                return (
                  <div key={key.id} className="px-6 py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Link2 className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{key.name}</p>
                        </div>
                        <div className="flex items-center gap-3 mt-2">
                          <code className="text-xs text-gray-500 font-mono bg-gray-50 dark:bg-gray-700/50 px-2 py-1 rounded">
                            {key.key_prefix}...
                          </code>
                          <span className="text-xs text-gray-400">Scopes: {key.scopes}</span>
                          <span className="text-xs text-gray-400">Создан: {formatDateTime(key.created_at)}</span>
                        </div>

                        {/* API Key reveal */}
                        {key.secret && (
                          <div className="mt-3">
                            {isRevealed ? (
                              <div className="flex items-center gap-2 p-2 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                                <code className="text-xs font-mono text-emerald-700 dark:text-emerald-400 flex-1 break-all truncate">
                                  {key.secret}
                                </code>
                                <button
                                  onClick={() => handleCopy(key.secret!, key.id)}
                                  className={`p-1.5 rounded-lg transition-colors flex-shrink-0 ${
                                    copiedId === key.id
                                      ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
                                      : 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/60'
                                  }`}
                                  title="Скопировать"
                                >
                                  {copiedId === key.id ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </button>
                                <button
                                  onClick={() => setRevealedKey(null)}
                                  className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/60 transition-colors flex-shrink-0"
                                  title="Скрыть"
                                >
                                  <EyeOff className="w-4 h-4" />
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => handleReveal(key.secret!, key.id)}
                                className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                Показать ключ
                              </button>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                          Активен
                        </span>
                        <button
                          onClick={() => handleRevoke(key.id)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                          title="Удалить"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
