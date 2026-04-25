'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/hooks/useAuth';
import {
  Shield, LayoutDashboard, Globe, ScanLine, Bug, FileText,
  Settings, LogOut, Menu, X, Key, Crown, UserCog, Wallet, DollarSign
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/domains', label: 'Домены', icon: Globe },
  { href: '/scans', label: 'Сканы', icon: ScanLine },
  { href: '/vulnerabilities', label: 'Уязвимости', icon: Bug },
  { href: '/reports', label: 'Отчёты', icon: FileText },
  { href: '/account', label: 'Кабинет', icon: Wallet },
  { href: '/api-keys', label: 'API ключи', icon: Key },
  { href: '/settings', label: 'Настройки', icon: Settings },
];

const adminItems = [
  { href: '/admin', label: 'Админ-панель', icon: UserCog },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, loadUser, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = React.useState(true);

  useEffect(() => {
    loadUser().then(() => setIsCheckingAuth(false));
  }, []);

  useEffect(() => {
    if (!isCheckingAuth && !isAuthenticated) {
      router.push('/login');
    }
  }, [isCheckingAuth, isAuthenticated, router]);

  if (isCheckingAuth || !user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    // Small delay to ensure state is cleared before redirect
    setTimeout(() => router.push('/'), 50);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        'fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-200 ease-in-out lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-200 dark:border-gray-700">
          <Shield className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">SafeScan</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">Security Platform</p>
          </div>
          <button
            className="ml-auto lg:hidden text-gray-400"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}

          {/* Admin section */}
          {user?.role === 'admin' && (
            <>
              <div className="pt-3 pb-1">
                <p className="px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                  Управление
                </p>
              </div>
              {adminItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.label}
                  </Link>
                );
              })}
            </>
          )}
        </nav>

        {/* User */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
              {user?.first_name?.[0] || user?.email?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user?.first_name || user?.email}
                </p>
                {user?.role === 'admin' && (
                  <span className="flex-shrink-0 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                    <Crown className="w-2.5 h-2.5" />
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
            </div>
          </div>

          {/* Balance */}
          <Link
            href="/account"
            className="flex items-center justify-between p-3 mb-3 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800/50 rounded-xl hover:shadow-md transition-all group"
          >
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                <DollarSign className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium uppercase tracking-wider">Баланс</p>
                <p className="text-sm font-bold text-emerald-700 dark:text-emerald-300">
                  {(user.balance ?? 0).toFixed(2)} ₽
                </p>
              </div>
            </div>
          </Link>

          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Выйти
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              className="lg:hidden text-gray-600 dark:text-gray-400"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-4 ml-auto">
              {user?.role === 'admin' && (
                <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 font-medium">
                  <Crown className="w-3 h-3" />
                  Admin
                </span>
              )}
              <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                🛡️ Defensive Security Platform
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
