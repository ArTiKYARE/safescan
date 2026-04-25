'use client';

import React, { useEffect, useState } from 'react';
import { adminApi, type AdminUser, type AdminDomain } from '@/lib/admin';
import { useAuthStore } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import {
  Users, Shield, Ban, CheckCircle, RefreshCw, Search,
  Crown, Key, AlertTriangle, UserPlus, UserMinus,
  X, Copy, Globe, Calendar, Mail, User, Clock,
  Wallet, DollarSign, Check,
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

const roleLabels: Record<string, string> = {
  viewer: 'Пользователь',
  operator: 'Оператор',
  admin: 'Админ',
  security_auditor: 'Аудитор',
};

const roleConfig: Record<string, { bg: string; text: string }> = {
  viewer: { bg: 'bg-gray-100 dark:bg-gray-700/60', text: 'text-gray-600 dark:text-gray-300' },
  operator: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400' },
  admin: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400' },
  security_auditor: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400' },
};

const avatarColors = [
  'bg-blue-600', 'bg-emerald-600', 'bg-violet-600', 'bg-rose-600',
  'bg-amber-600', 'bg-cyan-600', 'bg-pink-600', 'bg-indigo-600',
];

function getAvatarColor(email: string): string {
  let hash = 0;
  for (let i = 0; i < email.length; i++) hash = email.charCodeAt(i) + ((hash << 5) - hash);
  return avatarColors[Math.abs(hash) % avatarColors.length];
}

export default function AdminPage() {
  const { user: currentUser } = useAuthStore();
  const router = useRouter();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [copiedPwd, setCopiedPwd] = useState<string | null>(null);

  // User detail modal
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [userDomains, setUserDomains] = useState<AdminDomain[]>([]);
  const [loadingDomains, setLoadingDomains] = useState(false);
  const [showAddBalance, setShowAddBalance] = useState(false);
  const [addBalanceAmount, setAddBalanceAmount] = useState('');
  const [addBalanceDesc, setAddBalanceDesc] = useState('');

  useEffect(() => {
    if (currentUser?.role !== 'admin' && currentUser?.role !== 'security_auditor') {
      router.push('/dashboard');
      return;
    }
    fetchUsers();
  }, [currentUser]);

  const fetchUsers = async () => {
    try {
      const resp = await adminApi.listUsers();
      setUsers(resp.data);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    } finally {
      setLoading(false);
    }
  };

  const fetchUserDomains = async (userId: string) => {
    setLoadingDomains(true);
    try {
      const resp = await adminApi.getUserDomains(userId);
      setUserDomains(resp.data);
    } catch {
      setUserDomains([]);
    } finally {
      setLoadingDomains(false);
    }
  };

  const handleOpenUser = async (user: AdminUser) => {
    setSelectedUser(user);
    await fetchUserDomains(user.id);
  };

  const handleAction = async (userId: string, params: Record<string, string | boolean>) => {
    setActionLoading(userId);
    try {
      await adminApi.updateUser(userId, params);
      await fetchUsers();
      if (selectedUser?.id === userId) {
        const resp = await adminApi.getUser(userId);
        setSelectedUser(resp.data);
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    if (!confirm(`Удалить пользователя ${email}?`)) return;
    setActionLoading(userId);
    try {
      await adminApi.deleteUser(userId);
      setMessage({ type: 'success', text: `Пользователь ${email} удалён` });
      setSelectedUser(null);
      await fetchUsers();
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    } finally {
      setActionLoading(null);
      setTimeout(() => setMessage(null), 4000);
    }
  };

  const handleResetPassword = async (u: AdminUser) => {
    const pwd = Math.random().toString(36).slice(-10) + '!A1';
    try {
      await adminApi.updateUser(u.id, { new_password: pwd });
      setCopiedPwd(pwd);
      navigator.clipboard.writeText(pwd).catch(() => {});
      setTimeout(() => setCopiedPwd(null), 15000);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    }
  };

  const handleApproveDomain = async (userId: string, domainId: string) => {
    try {
      await adminApi.approveDomain(userId, domainId);
      await fetchUserDomains(userId);
      setMessage({ type: 'success', text: 'Домен одобрен' });
      setTimeout(() => setMessage(null), 3000);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    }
  };

  const handleAddBalance = async () => {
    const amount = parseFloat(addBalanceAmount);
    if (!amount || amount <= 0) {
      setMessage({ type: 'error', text: 'Введите корректную сумму' });
      return;
    }
    try {
      await adminApi.addBalance(selectedUser!.id, amount, addBalanceDesc || undefined);
      setMessage({ type: 'success', text: `Баланс ${selectedUser!.email} пополнен на ${amount} ₽` });
      setShowAddBalance(false);
      setAddBalanceAmount('');
      setAddBalanceDesc('');
      // Refresh user data
      const resp = await adminApi.getUser(selectedUser!.id);
      setSelectedUser(resp.data);
      setTimeout(() => setMessage(null), 4000);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.detail || e.message });
    }
  };

  const filtered = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.first_name || '').toLowerCase().includes(search.toLowerCase()) ||
      (u.last_name || '').toLowerCase().includes(search.toLowerCase())
  );

  const stats = {
    total: users.length,
    admin: users.filter((u) => u.role === 'admin').length,
    blocked: users.filter((u) => u.is_blocked).length,
    active: users.filter((u) => u.is_active && !u.is_blocked).length,
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
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center">
            <Crown className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Админ-панель</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Управление пользователями и доступом</p>
          </div>
        </div>
        <button
          onClick={fetchUsers}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Обновить
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Всего', value: stats.total, icon: Users, color: 'text-gray-700 dark:text-gray-200', bgIcon: 'bg-gray-100 dark:bg-gray-700' },
          { label: 'Активных', value: stats.active, icon: CheckCircle, color: 'text-emerald-600 dark:text-emerald-400', bgIcon: 'bg-emerald-100 dark:bg-emerald-900/30' },
          { label: 'Админов', value: stats.admin, icon: Crown, color: 'text-amber-600 dark:text-amber-400', bgIcon: 'bg-amber-100 dark:bg-amber-900/30' },
          { label: 'Заблокированных', value: stats.blocked, icon: Ban, color: 'text-red-600 dark:text-red-400', bgIcon: 'bg-red-100 dark:bg-red-900/30' },
        ].map(({ label, value, icon: Icon, color, bgIcon }) => (
          <div key={label} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className={`w-11 h-11 rounded-xl ${bgIcon} flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Toast messages */}
      {copiedPwd && (
        <div className="fixed top-4 right-4 z-[60] bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-xl shadow-2xl p-4 max-w-sm border border-gray-700 dark:border-gray-300">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400 dark:text-green-600" />
                Новый пароль сгенерирован
              </p>
              <div className="flex items-center gap-2 mt-2">
                <code className="text-xs bg-gray-800 dark:bg-gray-200 px-2 py-1 rounded font-mono break-all flex-1">
                  {copiedPwd}
                </code>
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Скопирован в буфер обмена</p>
            </div>
            <button onClick={() => setCopiedPwd(null)} className="text-gray-400 dark:text-gray-500 flex-shrink-0">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {message && (
        <div className={`p-4 rounded-xl flex items-center gap-3 transition-all ${
          message.type === 'success'
            ? 'bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50'
        }`}>
          {message.type === 'success'
            ? <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
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

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск по email или имени..."
          className="w-full pl-11 pr-10 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Users list */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
            Пользователи
            <span className="ml-2 text-xs font-normal text-gray-400">
              {filtered.length} {filtered.length === 1 ? 'пользователь' : filtered.length < 5 ? 'пользователя' : 'пользователей'}
            </span>
          </h2>
        </div>

        {filtered.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
              <Users className="w-7 h-7 text-gray-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">
              {search ? 'Ничего не найдено' : 'Нет пользователей'}
            </h3>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
            {filtered.map((u) => {
              const rc = roleConfig[u.role] || roleConfig.viewer;
              const isMe = u.id === currentUser?.id;
              const avatarLetter = u.first_name?.[0] || u.email[0].toUpperCase();

              return (
                <div
                  key={u.id}
                  onClick={() => !isMe && handleOpenUser(u)}
                  className={`px-6 py-4 flex items-center gap-4 transition-colors cursor-pointer ${
                    selectedUser?.id === u.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500'
                      : isMe ? 'bg-gray-50/50 dark:bg-gray-800/50' : 'hover:bg-gray-50/80 dark:hover:bg-gray-750/50'
                  } ${u.is_blocked ? 'opacity-60' : ''}`}
                >
                  {/* Avatar */}
                  <div className={`w-10 h-10 rounded-xl ${getAvatarColor(u.email)} flex items-center justify-center text-white text-sm font-bold flex-shrink-0`}>
                    {avatarLetter}
                  </div>

                  {/* User info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{u.email}</p>
                      {isMe && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium">Вы</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium ${rc.bg} ${rc.text}`}>
                        {u.role === 'admin' && <Crown className="w-3 h-3" />}
                        {roleLabels[u.role] || u.role}
                      </span>
                      <span className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active && !u.is_blocked ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                        {u.is_active && !u.is_blocked ? 'Активен' : 'Неактивен'}
                      </span>
                      {u.failed_login_attempts > 0 && (
                        <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                          <AlertTriangle className="w-3 h-3" />{u.failed_login_attempts}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions (only for non-current user) */}
                  {!isMe && (
                    <div className="flex items-center gap-1 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleAction(u.id, { role: u.role === 'admin' ? 'viewer' : 'admin' })}
                        disabled={actionLoading === u.id}
                        className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${u.role === 'admin' ? 'text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20' : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'}`}
                        title={u.role === 'admin' ? 'Снять админа' : 'Назначить админом'}
                      >
                        {actionLoading === u.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Crown className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleAction(u.id, { is_blocked: !u.is_blocked, blocked_reason: u.is_blocked ? '' : 'Blocked by admin' })}
                        disabled={actionLoading === u.id}
                        className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${u.is_blocked ? 'text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20' : 'text-gray-400 hover:text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20'}`}
                        title={u.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                      >
                        {actionLoading === u.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : u.is_blocked ? <UserPlus className="w-4 h-4" /> : <UserMinus className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleResetPassword(u)}
                        disabled={actionLoading === u.id}
                        className="p-2 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors disabled:opacity-50"
                        title="Сбросить пароль"
                      >
                        <Key className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(u.id, u.email)}
                        disabled={actionLoading === u.id}
                        className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                        title="Удалить"
                      >
                        {actionLoading === u.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Ban className="w-4 h-4" />}
                      </button>
                    </div>
                  )}
                  {isMe && (
                    <span className="text-xs text-gray-400 italic px-2 flex-shrink-0">Текущий пользователь</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* User Detail Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSelectedUser(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-2xl w-full max-w-2xl mb-8">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl ${getAvatarColor(selectedUser.email)} flex items-center justify-center text-white text-sm font-bold`}>
                  {selectedUser.first_name?.[0] || selectedUser.email[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{selectedUser.email}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Информация о пользователе</p>
                </div>
              </div>
              <button onClick={() => setSelectedUser(null)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal body */}
            <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
              {/* User details grid */}
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: <Mail className="w-4 h-4" />, label: 'Email', value: selectedUser.email },
                  { icon: <User className="w-4 h-4" />, label: 'Имя', value: selectedUser.first_name && selectedUser.last_name ? `${selectedUser.first_name} ${selectedUser.last_name}` : '—' },
                  { icon: <Shield className="w-4 h-4" />, label: 'Роль', value: roleLabels[selectedUser.role] || selectedUser.role },
                  { icon: <Calendar className="w-4 h-4" />, label: 'Дата регистрации', value: formatDateTime(selectedUser.created_at) },
                  { icon: <Clock className="w-4 h-4" />, label: 'Последний вход', value: selectedUser.last_login ? formatDateTime(selectedUser.last_login) : '—' },
                  { icon: <Globe className="w-4 h-4" />, label: 'Домены', value: `${selectedUser.domain_count || 0}` },
                ].map(({ icon, label, value }) => (
                  <div key={label} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="text-gray-400 mt-0.5">{icon}</div>
                    <div className="min-w-0">
                      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{value}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Balance card */}
              <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl p-4 text-white flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-xs font-medium">Баланс пользователя</p>
                  <p className="text-2xl font-bold mt-1">
                    {(selectedUser.balance ?? 0).toFixed(2)} ₽
                  </p>
                </div>
                <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-emerald-200" />
                </div>
              </div>

              {/* Status badges */}
              <div className="flex flex-wrap gap-2">
                {selectedUser.is_active && !selectedUser.is_blocked && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-medium">
                    <CheckCircle className="w-3.5 h-3.5" /> Активен
                  </span>
                )}
                {selectedUser.is_blocked && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-medium">
                    <Ban className="w-3.5 h-3.5" /> Заблокирован
                  </span>
                )}
                {selectedUser.failed_login_attempts > 0 && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium">
                    <AlertTriangle className="w-3.5 h-3.5" /> {selectedUser.failed_login_attempts} неудачных входов
                  </span>
                )}
              </div>

              {/* Quick actions */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setShowAddBalance(!showAddBalance)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/50 transition-colors"
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  Пополнить баланс
                </button>
                <button
                  onClick={() => handleAction(selectedUser.id, { role: selectedUser.role === 'admin' ? 'viewer' : 'admin' })}
                  disabled={actionLoading === selectedUser.id}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-colors disabled:opacity-50"
                >
                  <Crown className="w-3.5 h-3.5" />
                  {selectedUser.role === 'admin' ? 'Снять админа' : 'Назначить админом'}
                </button>
                <button
                  onClick={() => handleAction(selectedUser.id, { is_blocked: !selectedUser.is_blocked, blocked_reason: selectedUser.is_blocked ? '' : 'Blocked by admin' })}
                  disabled={actionLoading === selectedUser.id}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  {selectedUser.is_blocked ? <UserPlus className="w-3.5 h-3.5" /> : <UserMinus className="w-3.5 h-3.5" />}
                  {selectedUser.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                </button>
                <button
                  onClick={() => handleResetPassword(selectedUser)}
                  disabled={actionLoading === selectedUser.id}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50"
                >
                  <Key className="w-3.5 h-3.5" />
                  Сбросить пароль
                </button>
              </div>

              {/* Add balance form */}
              {showAddBalance && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-500" />
                    Пополнить баланс
                  </h4>
                  <div className="grid grid-cols-3 gap-2">
                    {[100, 500, 1000, 2500, 5000, 10000].map((amt) => (
                      <button
                        key={amt}
                        onClick={() => setAddBalanceAmount(String(amt))}
                        className={`py-2 rounded-lg text-xs font-medium border transition-all ${
                          addBalanceAmount === String(amt)
                            ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
                            : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-gray-300'
                        }`}
                      >
                        {amt} ₽
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type="number"
                        value={addBalanceAmount}
                        onChange={(e) => setAddBalanceAmount(e.target.value)}
                        placeholder="Сумма"
                        min="1"
                        className="w-full pl-3 pr-8 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs">₽</span>
                    </div>
                    <button
                      onClick={handleAddBalance}
                      disabled={!addBalanceAmount}
                      className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                    >
                      Пополнить
                    </button>
                  </div>
                  <input
                    type="text"
                    value={addBalanceDesc}
                    onChange={(e) => setAddBalanceDesc(e.target.value)}
                    placeholder="Описание (необязательно)"
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-xs text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>
              )}

              {/* User domains */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Домены ({userDomains.length})
                </h4>
                {loadingDomains ? (
                  <div className="flex justify-center py-6">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
                  </div>
                ) : userDomains.length === 0 ? (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400 text-sm">
                    Нет добавленных доменов
                  </div>
                ) : (
                  <div className="space-y-2">
                    {userDomains.map((d) => (
                      <div
                        key={d.id}
                        className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                          d.is_verified
                            ? 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-200 dark:border-emerald-800/30'
                            : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <Globe className={`w-4 h-4 flex-shrink-0 ${d.is_verified ? 'text-emerald-500' : 'text-gray-400'}`} />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{d.domain}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {d.is_verified ? 'Верифицирован' : 'Не верифицирован'} · {formatDateTime(d.created_at)}
                            </p>
                          </div>
                        </div>
                        {d.is_verified ? (
                          <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium flex-shrink-0 ml-3">
                            <CheckCircle className="w-3.5 h-3.5" />
                            Одобрен
                          </span>
                        ) : (
                          <button
                            onClick={() => handleApproveDomain(selectedUser.id, d.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors flex-shrink-0 ml-3"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            Одобрить
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
