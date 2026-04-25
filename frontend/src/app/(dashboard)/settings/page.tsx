'use client';

import React, { useEffect, useState } from 'react';
import { authApi, settingsApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { useAuthStore } from '@/hooks/useAuth';
import { User, Key, Shield, Bell, CheckCircle, AlertCircle } from 'lucide-react';
import type { UserSettings } from '@/types';

export default function SettingsPage() {
  const { user, loadUser } = useAuthStore();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name || '');
      setLastName(user.last_name || '');
    }
    settingsApi.get().then((r) => setSettings(r.data)).catch(console.error);
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await authApi.updateMe({ first_name: firstName, last_name: lastName });
      setSuccess('Профиль обновлён');
      loadUser();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await authApi.changePassword({ current_password: currentPassword, new_password: newPassword });
      setSuccess('Пароль изменён');
      setCurrentPassword('');
      setNewPassword('');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Настройки</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Управление профилем и параметрами</p>
      </div>

      {success && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
          <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
        </div>
      )}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Profile */}
      <Card title="Профиль">
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Имя" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            <Input label="Фамилия" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Email: <span className="text-gray-900 dark:text-white font-medium">{user?.email}</span></p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Роль: <span className="text-gray-900 dark:text-white font-medium capitalize">{user?.role}</span></p>
          </div>
          <Button type="submit" isLoading={saving}>Сохранить</Button>
        </form>
      </Card>

      {/* Password */}
      <Card title="Смена пароля">
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Текущий пароль"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Input
            label="Новый пароль"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <Button type="submit" isLoading={saving}>Изменить пароль</Button>
        </form>
      </Card>

      {/* Security */}
      <Card title="Безопасность">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Двухфакторная аутентификация (MFA)</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">TOTP через Google Authenticator</p>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${user?.mfa_enabled ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500'}`}>
              {user?.mfa_enabled ? 'Включена' : 'Выключена'}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Email подтверждён</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Статус верификации email</p>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${user?.email_verified ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700'}`}>
              {user?.email_verified ? 'Да' : 'Нет'}
            </span>
          </div>
        </div>
      </Card>

      {/* Notifications */}
      {settings && (
        <Card title="Уведомления">
          <div className="space-y-3">
            {Object.entries(settings.notifications).map(([key, value]) => (
              <label key={key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg cursor-pointer">
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{key}</span>
                <input
                  type="checkbox"
                  checked={value as boolean}
                  readOnly
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </label>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">Настройка уведомлений будет доступна в следующем обновлении</p>
        </Card>
      )}
    </div>
  );
}
