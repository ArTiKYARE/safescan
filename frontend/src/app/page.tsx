// frontend/src/app/page.tsx
import type { Metadata } from "next";
import Link from "next/link";
import {
  Shield,
  Lock,
  FileText,
  Zap,
  Globe,
  CheckCircle,
  ArrowRight,
  BarChart3,
  Database,
  Key,
  Mail,
  Search,
  Code,
  Server,
  Send,
  ExternalLink,
  ChevronDown,
} from "lucide-react";

// 🔹 Уникальная мета-информация для главной страницы
// Переопределяет значения из layout.tsx только для этой страницы
export const meta Metadata = {
  title: "SafeScan — Бесплатное сканирование сайтов на уязвимости онлайн",
  description:
    "Проверьте сайт на уязвимости бесплатно: XSS, SQLi, CSRF, SSL, заголовки безопасности. 76+ модулей проверки, отчёт в PDF, соответствие OWASP Top 10, PCI-DSS, 152-ФЗ. Регистрация за 1 минуту.",
  keywords: [
    "бесплатный сканер уязвимостей",
    "проверка сайта онлайн бесплатно",
    "аудит безопасности веб-приложений",
    "легальное тестирование на проникновение",
    "онлайн проверка уязвимостей сайта",
    "сканирование безопасности веб",
    "поиск уязвимостей веб-сайта",
    "SafeScan бесплатно",
  ],
  alternates: {
    canonical: "https://safescanget.ru/",
  },
  // Дополнительные теги для главной
  openGraph: {
    title: "SafeScan — Бесплатное сканирование сайтов на уязвимости",
    description:
      "76+ модулей проверки: XSS, SQLi, CSRF, SSL. Отчёт в PDF/JSON. OWASP Top 10. Регистрация за 1 минуту.",
    url: "https://safescanget.ru",
  },
};

// 🔹 Компонент главной страницы (клиентский, т.к. использует хуки)
// 'use client' обязателен для useEffect, useState, useRouter
export default function Home() {
  // Хуки и логика компонента...
  // (оставляем существующую логику без изменений)

  return (
    // 🔹 Семантическая разметка: <main> вместо <div> для основного контента
    <main 
      className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white"
      itemScope 
      itemType="https://schema.org/WebPage"
    >
      {/* Скрытый заголовок для скринридеров и поисковиков */}
      <h1 className="sr-only" itemProp="name">
        SafeScan — Бесплатное сканирование сайтов на уязвимости онлайн
      </h1>
      <meta itemProp="description" content="SaaS-платформа для автоматизированного аудита безопасности веб-ресурсов. 76+ модулей проверок, соответствие стандартам безопасности." />

      {/* === Navigation === */}
      <nav 
        className="border-b border-gray-800/50 backdrop-blur-sm bg-gray-950/80 sticky top-0 z-50"
        itemScope 
        itemType="https://schema.org/SiteNavigationElement"
        aria-label="Главная навигация"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-18">
            {/* Логотип с микроразметкой */}
            <Link 
              href="/" 
              className="flex items-center gap-3"
              itemProp="url"
              aria-label="SafeScan — на главную"
            >
              <Shield className="w-8 h-8 text-blue-500" aria-hidden="true" />
              <span 
                className="text-xl font-bold tracking-wide"
                itemProp="name"
              >
                SafeScan
              </span>
            </Link>
            
            {/* Навигационные ссылки */}
            <div className="flex items-center gap-6">
              <Link
                href="/login"
                className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm"
                itemProp="potentialAction"
                itemScope
                itemType="https://schema.org/SearchAction"
              >
                <span itemProp="target" content="/login">Войти</span>
              </Link>
              <Link
                href="/register"
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-600/20"
                itemProp="potentialAction"
              >
                Регистрация
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* === Hero Section === */}
      <section 
        id="hero"
        className="relative overflow-hidden"
        aria-labelledby="hero-heading"
      >
        {/* Декоративные элементы (скрыты для скринридеров) */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-600/5 rounded-full blur-3xl" aria-hidden="true" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-cyan-600/5 rounded-full blur-3xl" aria-hidden="true" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/15 via-gray-950 to-gray-950" aria-hidden="true" />
        
        <div className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-32 sm:py-40 lg:py-48">
          <div className="text-center max-w-4xl mx-auto" itemScope itemType="https://schema.org/WebApplication">
            {/* Бейдж */}
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-5 py-2 mb-10">
              <Lock className="w-4 h-4 text-blue-400" aria-hidden="true" />
              <span className="text-sm text-blue-300 tracking-wide">Defensive Security Platform</span>
            </div>
            
            {/* Заголовок */}
            <h2 
              id="hero-heading"
              className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight mb-8 leading-tight"
              itemProp="applicationCategory"
            >
              Легальное сканирование
              <br />
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                на уязвимости
              </span>
            </h2>
            
            {/* Описание */}
            <p 
              className="max-w-2xl mx-auto text-lg sm:text-xl text-gray-400 mb-14 leading-relaxed"
              itemProp="description"
            >
              SafeScan — SaaS-платформа для автоматизированного аудита безопасности веб-ресурсов.
              Обнаружение, а не эксплуатация. Только с письменного согласия владельцев.
            </p>
            
            {/* Кнопки */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-9 py-4 rounded-xl font-medium transition-colors text-lg shadow-lg shadow-blue-600/25"
                itemProp="downloadUrl"
              >
                Начать бесплатно
                <ArrowRight className="w-5 h-5" aria-hidden="true" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white px-9 py-4 rounded-xl font-medium transition-colors text-lg"
                aria-label="Узнать больше о возможностях платформы"
              >
                Узнать больше
                <ChevronDown className="w-4 h-4 ml-1" aria-hidden="true" />
              </a>
            </div>
            
            {/* Скрытые метаданные для поисковиков */}
            <meta itemProp="operatingSystem" content="Web" />
            <meta itemProp="offers" content="https://schema.org/Offer" />
            <meta itemProp="price" content="0" />
            <meta itemProp="priceCurrency" content="RUB" />
          </div>
        </div>
      </section>

      {/* === Stats Section === */}
      <section 
        id="stats"
        className="border-y border-gray-800/50 bg-gray-900/50"
        aria-labelledby="stats-heading"
      >
        <h3 id="stats-heading" className="sr-only">Статистика платформы</h3>
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-16">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-12">
            {[
              { value: '76+', label: 'Модулей проверок' },
              { value: '12', label: 'Категорий сканирования' },
              { value: 'OWASP', label: 'Соответствие Top 10' },
              { value: 'PDF/JSON', label: 'Форматы отчётов' },
            ].map((stat, i) => (
              <div key={i} className="text-center" itemScope itemType="https://schema.org/PropertyValue">
                <div 
                  className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2"
                  itemProp="value"
                >
                  {stat.value}
                </div>
                <div 
                  className="text-sm text-gray-400 tracking-wide"
                  itemProp="name"
                >
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* === Divider === */}
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12" role="separator" aria-hidden="true">
        <div className="h-px bg-gradient-to-r from-transparent via-gray-800 to-transparent" />
      </div>

      {/* === Features Section === */}
      <section 
        id="features"
        className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-28 sm:py-32"
        aria-labelledby="features-heading"
      >
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl pointer-events-none" aria-hidden="true" />
        
        <div className="relative text-center mb-20">
          <h2 
            id="features-heading"
            className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 tracking-tight"
          >
            Возможности платформы
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg sm:text-xl leading-relaxed">
            Комплексное сканирование с детектированием уязвимостей и рекомендациями по устранению
          </p>
        </div>
        
        {/* Список возможностей с микроразметкой */}
        <div 
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
          itemScope 
          itemType="https://schema.org/ItemList"
        >
          {[
            {
              icon: <Shield className="w-6 h-6" aria-hidden="true" />,
              title: 'Security Headers',
              desc: 'Проверка HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy и других заголовков безопасности',
              schemaName: 'SecurityHeadersCheck',
            },
            {
              icon: <Lock className="w-6 h-6" aria-hidden="true" />,
              title: 'SSL/TLS',
              desc: 'Анализ протоколов, шифров, сертификатов, OCSP Stapling, Perfect Forward Secrecy',
              schemaName: 'SSLTLSAnalysis',
            },
            {
              icon: <Code className="w-6 h-6" aria-hidden="true" />,
              title: 'XSS & Injection',
              desc: 'Обнаружение XSS, SQLi, NoSQLi, Command Injection, SSTI с дифференциальным анализом',
              schemaName: 'InjectionDetection',
            },
            {
              icon: <Server className="w-6 h-6" aria-hidden="true" />,
              title: 'SSRF / XXE / Path Traversal',
              desc: 'Детектирование SSRF, Blind SSRF, XXE, обхода путей с безопасными payload',
              schemaName: 'ServerSideVulnerabilities',
            },
            {
              icon: <Key className="w-6 h-6" aria-hidden="true" />,
              title: 'Auth & Sessions',
              desc: 'Проверка cookie, JWT, session fixation, политики паролей, MFA, защита от перебора',
              schemaName: 'AuthenticationSecurity',
            },
            {
              icon: <Globe className="w-6 h-6" aria-hidden="true" />,
              title: 'Network & Infrastructure',
              desc: 'DNS, SPF/DKIM/DMARC, CDN/WAF detection, субдомены, IPv6, subdomain takeover',
              schemaName: 'InfrastructureAnalysis',
            },
            {
              icon: <Search className="w-6 h-6" aria-hidden="true" />,
              title: 'Info Leakage',
              desc: 'Обнаружение .git, .env, backup файлов, API ключей, email в коде, метаданных',
              schemaName: 'DataLeakageDetection',
            },
            {
              icon: <BarChart3 className="w-6 h-6" aria-hidden="true" />,
              title: 'SCA',
              desc: 'Анализ зависимостей: уязвимые JS-библиотеки, CMS detection, technology fingerprinting',
              schemaName: 'SoftwareCompositionAnalysis',
            },
            {
              icon: <Database className="w-6 h-6" aria-hidden="true" />,
              title: 'CSRF / CORS',
              desc: 'Проверка CSRF-токенов, SameSite, CORS misconfiguration, wildcard origin',
              schemaName: 'CSRFCORSCheck',
            },
          ].map((feature, i) => (
            <article
              key={i}
              className="group border border-gray-800/80 hover:border-blue-500/40 rounded-2xl p-8 bg-gray-900/20 hover:bg-gray-900/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-blue-500/5"
              itemScope
              itemType="https://schema.org/ListItem"
            >
              <meta itemProp="position" content={String(i + 1)} />
              
              <div className="w-14 h-14 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400 mb-5 group-hover:bg-blue-500/20 transition-colors">
                {feature.icon}
              </div>
              
              <h3 
                className="text-lg font-semibold mb-3"
                itemProp="name"
              >
                {feature.title}
              </h3>
              
              <p 
                className="text-gray-400 text-sm leading-relaxed"
                itemProp="description"
              >
                {feature.desc}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* === Divider === */}
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12" role="separator" aria-hidden="true">
        <div className="h-px bg-gradient-to-r from-transparent via-gray-800 to-transparent" />
      </div>

      {/* === How It Works Section === */}
      <section 
        id="how-it-works"
        className="border-t border-gray-800/50 bg-gray-900/30"
        aria-labelledby="howitworks-heading"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-28 sm:py-32">
          <div className="text-center mb-20">
            <h2 
              id="howitworks-heading"
              className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 tracking-tight"
            >
              Как это работает
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto text-lg sm:text-xl leading-relaxed">
              Три простых шага от регистрации до полного отчёта безопасности
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-12 lg:gap-16">
            {[
              {
                step: '01',
                icon: <Mail className="w-8 h-8" aria-hidden="true" />,
                title: 'Регистрация и верификация',
                desc: 'Создайте аккаунт, добавьте домен и подтвердите владение через DNS TXT запись, файл или email',
              },
              {
                step: '02',
                icon: <Zap className="w-8 h-8" aria-hidden="true" />,
                title: 'Запуск сканирования',
                desc: 'Выберите тип скана (быстрый или полный) и запустите проверку. 12 модулей работают параллельно',
              },
              {
                step: '03',
                icon: <FileText className="w-8 h-8" aria-hidden="true" />,
                title: 'Отчёт и рекомендации',
                desc: 'Получите детальный отчёт с CVSS классификацией, приоритетами и конкретными рекомендациями по устранению',
              },
            ].map((item, i) => (
              <article key={i} className="relative">
                <div 
                  className="text-8xl font-black text-gray-800/80 absolute -top-6 -left-3 select-none"
                  aria-hidden="true"
                >
                  {item.step}
                </div>
                <div className="relative">
                  <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center mb-8 shadow-lg shadow-blue-600/20">
                    {item.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-4">{item.title}</h3>
                  <p className="text-gray-400 leading-relaxed text-base">{item.desc}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* === Divider === */}
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12" role="separator" aria-hidden="true">
        <div className="h-px bg-gradient-to-r from-transparent via-gray-800 to-transparent" />
      </div>

      {/* === Compliance Section === */}
      <section 
        id="compliance"
        className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-28 sm:py-32"
        aria-labelledby="compliance-heading"
      >
        <div className="text-center mb-16">
          <h2 
            id="compliance-heading"
            className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 tracking-tight"
          >
            Соответствие стандартам
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg sm:text-xl leading-relaxed">
            Платформа соответствует ведущим стандартам безопасности
          </p>
        </div>
        
        <div 
          className="flex flex-wrap justify-center gap-5"
          itemScope 
          itemType="https://schema.org/ItemList"
        >
          {['OWASP Top 10', 'ASVS', 'NIST SP 800-53', 'PCI-DSS', '152-ФЗ', 'GDPR', 'CWE', 'OWASP API Top 10'].map(
            (std, i) => (
              <div
                key={i}
                className="flex items-center gap-3 border border-gray-700 rounded-xl px-6 py-4 bg-gray-900/50 hover:border-gray-600 transition-colors"
                itemScope
                itemType="https://schema.org/ListItem"
              >
                <meta itemProp="position" content={String(i + 1)} />
                <CheckCircle className="w-5 h-5 text-green-500" aria-hidden="true" />
                <span className="text-sm font-medium" itemProp="name">{std}</span>
              </div>
            )
          )}
        </div>
      </section>

      {/* === CTA Section === */}
      <section 
        id="cta"
        className="border-t border-gray-800/50"
        aria-labelledby="cta-heading"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-28 sm:py-32">
          <div 
            className="text-center bg-gradient-to-br from-blue-600/15 to-cyan-600/15 border border-blue-500/20 rounded-3xl p-14 sm:p-16 lg:p-20"
            itemScope 
            itemType="https://schema.org/Offer"
          >
            <h2 
              id="cta-heading"
              className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 tracking-tight"
            >
              Готовы проверить безопасность?
            </h2>
            <p className="text-gray-300 max-w-xl mx-auto mb-10 text-lg sm:text-xl leading-relaxed">
              Начните бесплатное сканирование и узнайте, какие уязвимости есть на вашем сайте
            </p>
            
            <Link
              href="/register"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 rounded-xl font-medium transition-colors text-lg shadow-lg shadow-blue-600/25"
              itemProp="url"
            >
              Зарегистрироваться
              <ArrowRight className="w-5 h-5" aria-hidden="true" />
            </Link>
            
            {/* Скрытые метаданные для предложения */}
            <meta itemProp="price" content="0" />
            <meta itemProp="priceCurrency" content="RUB" />
            <meta itemProp="availability" content="https://schema.org/InStock" />
            <meta itemProp="itemOffered" content="SafeScan Vulnerability Scanner" />
          </div>
        </div>
      </section>

      {/* === Footer === */}
      <footer 
        className="border-t border-gray-800/50 bg-gray-950"
        itemScope 
        itemType="https://schema.org/WPFooter"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-14">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
            {/* Brand */}
            <div itemScope itemType="https://schema.org/Organization">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-7 h-7 text-blue-500" aria-hidden="true" />
                <span className="text-lg font-bold tracking-wide" itemProp="name">SafeScan</span>
                <span className="text-gray-500 text-xs" itemProp="softwareVersion">v1.0.0</span>
              </div>
              <p className="text-gray-500 text-sm leading-relaxed" itemProp="description">
                Defensive Security Platform — обнаружение, а не эксплуатация.
                Предназначена исключительно для легального тестирования с письменного согласия.
              </p>
              <meta itemProp="url" content="https://safescanget.ru" />
              <meta itemProp="logo" content="https://safescanget.ru/logo.png" />
            </div>

            {/* Quick links */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Навигация</h3>
              <ul className="space-y-2">
                <li>
                  <Link href="/register" className="text-gray-400 hover:text-white text-sm transition-colors">
                    Регистрация
                  </Link>
                </li>
                <li>
                  <Link href="/login" className="text-gray-400 hover:text-white text-sm transition-colors">
                    Войти
                  </Link>
                </li>
              </ul>
            </div>

            {/* Contacts */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Контакты</h3>
              <ul className="space-y-3">
                <li>
                  <a
                    href="https://t.me/artikyare"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-gray-400 hover:text-blue-400 text-sm transition-colors"
                  >
                    <Send className="w-4 h-4" aria-hidden="true" />
                    <span>Telegram: @artikyare</span>
                    <ExternalLink className="w-3 h-3 opacity-50" aria-hidden="true" />
                  </a>
                </li>
                <li>
                  <a
                    href="https://vk.com/artikyare"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-gray-400 hover:text-blue-400 text-sm transition-colors"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M12.785 16.241s.288-.032.436-.194c.136-.148.132-.427.132-.427s-.02-1.304.587-1.496c.598-.19 1.367 1.259 2.182 1.815.616.42 1.084.328 1.084.328l2.178-.03s1.14-.07.599-.964c-.044-.073-.314-.661-1.618-1.869-1.366-1.265-1.183-1.06.462-3.246.999-1.33 1.398-2.142 1.273-2.489-.12-.331-.857-.244-.857-.244l-2.45.015s-.182-.025-.317.056c-.131.079-.216.263-.216.263s-.387 1.028-.903 1.903c-1.089 1.85-1.524 1.948-1.702 1.834-.414-.267-.31-1.075-.31-1.649 0-1.792.271-2.539-.529-2.732-.266-.064-.461-.106-1.14-.113-.87-.009-1.605.003-2.023.207-.278.136-.492.439-.362.456.161.021.527.099.72.363.25.341.241 1.11.241 1.11s.143 2.11-.334 2.372c-.328.18-.778-.187-1.745-1.865-.494-.858-.868-1.808-.868-1.808s-.072-.176-.2-.271c-.155-.115-.372-.151-.372-.151l-2.328.015s-.35.01-.478.162c-.114.135-.009.414-.009.414s1.82 4.258 3.88 6.403c1.889 1.966 4.032 1.836 4.032 1.836h.972z"/>
                    </svg>
                    <span>VK: @artikyar</span>
                    <ExternalLink className="w-3 h-3 opacity-50" aria-hidden="true" />
                  </a>
                </li>
                <li>
                  <a
                    href="mailto:kostdensv@gmail.com"
                    className="flex items-center gap-2 text-gray-400 hover:text-blue-400 text-sm transition-colors"
                  >
                    <Mail className="w-4 h-4" aria-hidden="true" />
                    <span>kostdensv@gmail.com</span>
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-gray-800 pt-8 flex flex-col items-center gap-3">
            <p className="text-gray-600 text-xs text-center max-w-lg">
              © {new Date().getFullYear()} SafeScan. Все права защищены.
              Платформа предназначена исключительно для легального тестирования безопасности.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}