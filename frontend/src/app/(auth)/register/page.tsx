'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Mail, Lock, User, AlertCircle, CheckCircle } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [success, setSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  const validatePassword = (pwd: string): string => {
    if (pwd.length < 8) return 'Минимум 8 символов';
    if (!/[A-Z]/.test(pwd)) return 'Нужна заглавная буква';
    if (!/[a-z]/.test(pwd)) return 'Нужна строчная буква';
    if (!/[0-9]/.test(pwd)) return 'Нужна цифра';
    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    const pwdErr = validatePassword(password);
    if (pwdErr) {
      setPasswordError(pwdErr);
      return;
    }
    setPasswordError('');

    try {
      await register(email, password, firstName || undefined, lastName || undefined);
      setSuccess(true);
      setTimeout(() => router.push('/login'), 2000);
    } catch {
      // Error handled by store
    }
  };

  if (success) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Регистрация успешна!</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">Перенаправляем на страницу входа...</p>
        <Link href="/login">
          <Button variant="primary">Перейти ко входу</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Создать аккаунт</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Имя"
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Иван"
            icon={<User className="w-4 h-4" />}
          />
          <Input
            label="Фамилия"
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Иванов"
          />
        </div>

        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          icon={<Mail className="w-4 h-4" />}
          required
        />

        <div>
          <Input
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setPasswordError(''); }}
            placeholder="Минимум 8 символов"
            icon={<Lock className="w-4 h-4" />}
            required
          />
          {passwordError && <p className="text-sm text-red-500 mt-1">{passwordError}</p>}
          {password && !passwordError && (
            <div className="mt-2 flex gap-1">
              {password.length >= 8 && <span className="text-xs text-green-500">✓ Длина</span>}
              {/[A-Z]/.test(password) && <span className="text-xs text-green-500">✓ Заглавная</span>}
              {/[a-z]/.test(password) && <span className="text-xs text-green-500">✓ Строчная</span>}
              {/[0-9]/.test(password) && <span className="text-xs text-green-500">✓ Цифра</span>}
            </div>
          )}
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          isLoading={isLoading}
          className="w-full"
        >
          Зарегистрироваться
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Уже есть аккаунт?{' '}
        <Link href="/login" className="text-blue-600 hover:text-blue-500 font-medium">
          Войти
        </Link>
      </p>
    </div>
  );
}
