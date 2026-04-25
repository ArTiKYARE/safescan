'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import {
  Wallet, Plus, ArrowUpRight, ArrowDownLeft, Clock, AlertTriangle,
  ExternalLink, Copy, Check, Info, Shield, CreditCard, DollarSign,
  BookOpen, X, Gift,
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

interface BalanceData {
  balance: number;
  currency: string;
}

interface Transaction {
  id: string;
  amount: number;
  currency: string;
  type: string;
  status: string;
  payment_method: string | null;
  description: string | null;
  confirmation_url: string | null;
  created_at: string;
}

const typeLabels: Record<string, string> = {
  deposit: 'Пополнение',
  yookassa: 'ЮKassa',
  scan_cost: 'Оплата скана',
  admin_adjustment: 'Корректировка',
  refund: 'Возврат',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  refunded: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400',
};

const presetAmounts = [100, 250, 500, 1000, 2500, 5000];

export default function AccountPage() {
  const { user, loadUser } = useAuthStore();
  const router = useRouter();
  const [balance, setBalance] = useState<BalanceData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [topUpAmount, setTopUpAmount] = useState('');
  const [topUpLoading, setTopUpLoading] = useState(false);
  const [topUpUrl, setTopUpUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showYookassaInfo, setShowYookassaInfo] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchData = async () => {
    try {
      const [balResp, txnResp] = await Promise.all([
        api.get<BalanceData>('/billing/balance'),
        api.get<Transaction[]>('/billing/transactions'),
      ]);
      setBalance(balResp.data);
      setTransactions(txnResp.data);
    } catch (e: any) {
      // API may not have billing endpoints yet
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
    fetchData();
  }, []);

  const handleTopUp = async () => {
    const amount = parseFloat(topUpAmount);
    if (!amount || amount < 1) {
      setMessage({ type: 'error', text: 'Минимальная сумма пополнения: 1 RUB' });
      return;
    }
    setTopUpLoading(true);
    try {
      const resp = await api.post('/billing/topup', { amount });
      if (resp.data.confirmation_url) {
        setTopUpUrl(resp.data.confirmation_url);
        setMessage({ type: 'success', text: 'Перейдите по ссылке для оплаты' });
      } else {
        setMessage({ type: 'success', text: resp.data.message || 'Заявка на пополнение создана' });
        setTopUpAmount('');
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Ошибка при создании платежа' });
    } finally {
      setTopUpLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (topUpUrl) {
      navigator.clipboard.writeText(topUpUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-600 flex items-center justify-center">
            <Wallet className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Личный кабинет</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Баланс и история операций</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className={`p-4 rounded-xl flex items-center gap-3 ${
          message.type === 'success'
            ? 'bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50'
        }`}>
          {message.type === 'success'
            ? <Check className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            : <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
          }
          <p className={`text-sm flex-1 ${message.type === 'success' ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'}`}>
            {message.text}
          </p>
          <button onClick={() => setMessage(null)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Payment link */}
      {topUpUrl && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50 rounded-xl p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 flex items-center gap-2">
                <ExternalLink className="w-4 h-4" />
                Ссылка на оплату
              </h3>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                Перейдите по ссылке для завершения оплаты через ЮKassa
              </p>
              <div className="flex items-center gap-2 mt-3">
                <code className="text-xs bg-white dark:bg-gray-800 px-3 py-2 rounded-lg font-mono break-all flex-1 border border-blue-200 dark:border-blue-700">
                  {topUpUrl}
                </code>
                <button
                  onClick={handleCopyLink}
                  className="p-2 rounded-lg bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-gray-500" />}
                </button>
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <a
                href={topUpUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Оплатить
              </a>
              <button
                onClick={() => setTopUpUrl(null)}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Balance card */}
      <div className="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-emerald-100 text-sm font-medium">Текущий баланс</p>
            <p className="text-4xl font-bold mt-2">
              {balance ? `${balance.balance.toFixed(2)}` : '0.00'}
              <span className="text-lg text-emerald-200 ml-2">{balance?.currency || 'RUB'}</span>
            </p>
            <p className="text-emerald-200 text-xs mt-2">
              {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : user?.email}
            </p>
            {user && (user.free_scans_remaining || 0) > 0 && (
              <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium bg-white/10 px-3 py-1.5 rounded-full">
                <Gift className="w-3.5 h-3.5" />
                {user.free_scans_remaining} бесплатных быстрых сканов осталось
              </div>
            )}
          </div>
          <div className="w-14 h-14 bg-white/10 rounded-xl flex items-center justify-center">
            <DollarSign className="w-7 h-7 text-emerald-200" />
          </div>
        </div>
      </div>

      {/* Pricing info */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm p-5">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <Wallet className="w-4 h-4 text-gray-400" />
          Тарифы
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Быстрый скан</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">4 модуля, ~30 сек</p>
            </div>
            {(user?.free_scans_remaining || 0) > 0 ? (
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/30 px-2 py-1 rounded-full">
                Бесплатно ({user?.free_scans_remaining} осталось)
              </span>
            ) : (
              <span className="text-sm font-bold text-gray-900 dark:text-white">10 ₽</span>
            )}
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Полный скан</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">12 модулей, ~2 мин</p>
            </div>
            <span className="text-sm font-bold text-gray-900 dark:text-white">20 ₽</span>
          </div>
        </div>
      </div>

      {/* Top up */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-emerald-500" />
          Пополнить баланс
        </h2>

        {/* Preset amounts */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4">
          {presetAmounts.map((amt) => (
            <button
              key={amt}
              onClick={() => setTopUpAmount(String(amt))}
              className={`py-2.5 rounded-xl text-sm font-medium border transition-all ${
                topUpAmount === String(amt)
                  ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
            >
              {amt} ₽
            </button>
          ))}
        </div>

        {/* Custom amount */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="number"
              value={topUpAmount}
              onChange={(e) => setTopUpAmount(e.target.value)}
              placeholder="Сумма в рублях"
              min="1"
              className="w-full pl-4 pr-10 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">₽</span>
          </div>
          <button
            onClick={handleTopUp}
            disabled={topUpLoading || !topUpAmount}
            className="flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {topUpLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            ) : (
              <ArrowUpRight className="w-4 h-4" />
            )}
            Пополнить
          </button>
        </div>

        {/* YooKassa info toggle */}
        <div className="mt-4">
          <button
            onClick={() => setShowYookassaInfo(!showYookassaInfo)}
            className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
            Как работает оплата через ЮKassa?
          </button>
          {showYookassaInfo && (
            <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl text-xs text-gray-600 dark:text-gray-300 leading-relaxed space-y-2">
              <p className="font-semibold text-sm text-gray-900 dark:text-white">Настройка ЮKassa для владельца платформы:</p>
              <ol className="list-decimal list-inside space-y-1.5">
                <li>Зарегистрируйтесь на <a href="https://yookassa.ru" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">yookassa.ru</a></li>
                <li>Создайте магазин и получите <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">shopId</code> и <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">secretKey</code></li>
                <li>Установите их в <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">.env</code> файле:
                  <ul className="list-disc list-inside ml-4 mt-1">
                    <li><code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">YOOKASSA_SHOP_ID=ваш_shop_id</code></li>
                    <li><code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">YOOKASSA_SECRET_KEY=ваш_secret_key</code></li>
                    <li><code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">YOOKASSA_RETURN_URL=http://localhost:3000/account</code></li>
                  </ul>
                </li>
                <li>В личном кабинете ЮKassa настройте HTTP-уведомления (webhook):
                  <ul className="list-disc list-inside ml-4 mt-1">
                    <li>URL: <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">http://localhost:8000/api/v1/billing/webhook/yookassa</code></li>
                    <li>События: <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">payment.succeeded</code>, <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">payment.canceled</code></li>
                  </ul>
                </li>
                <li>Перезапустите backend: <code className="bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded">docker compose restart backend</code></li>
              </ol>
              <p className="text-gray-400 mt-2">Без настройки ЮKassa пополнение будет обрабатываться в ручном режиме через админ-панель.</p>
            </div>
          )}
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            История операций
            <span className="text-xs font-normal text-gray-400">({transactions.length})</span>
          </h2>
        </div>
        {transactions.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-14 h-14 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
              <ArrowDownLeft className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">Нет операций</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Здесь будет история ваших платежей</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
            {transactions.map((t) => (
              <div key={t.id} className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50/50 dark:hover:bg-gray-750/50 transition-colors">
                {/* Icon */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  t.type === 'yookassa' || t.type === 'deposit' || t.type === 'admin_adjustment'
                    ? 'bg-emerald-100 dark:bg-emerald-900/30'
                    : 'bg-gray-100 dark:bg-gray-700'
                }`}>
                  {t.type === 'yookassa' || t.type === 'deposit' ? (
                    <ArrowDownLeft className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  ) : t.type === 'scan_cost' ? (
                    <CreditCard className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  ) : (
                    <Shield className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  )}
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {typeLabels[t.type] || t.type}
                    </p>
                    <p className={`text-sm font-bold flex-shrink-0 ${
                      t.type === 'yookassa' || t.type === 'deposit' || t.type === 'admin_adjustment' || t.type === 'refund'
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-gray-900 dark:text-white'
                    }`}>
                      {t.type === 'scan_cost' ? '−' : '+'}{t.amount.toFixed(2)} ₽
                    </p>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${statusColors[t.status] || statusColors.pending}`}>
                      {t.status === 'completed' ? 'Выполнено' : t.status === 'pending' ? 'Ожидание' : t.status === 'failed' ? 'Ошибка' : 'Возврат'}
                    </span>
                    <span className="text-xs text-gray-400">{formatDateTime(t.created_at)}</span>
                  </div>
                  {t.description && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{t.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
