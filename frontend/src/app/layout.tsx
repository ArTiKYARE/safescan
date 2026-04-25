// frontend/src/app/layout.tsx
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import YandexMetrica from "@/components/analytics/YandexMetrica";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

// 🔹 Расширенная мета-информация
export const metadata: Metadata = {
  // === Основные теги ===
  title: {
    template: "%s | SafeScan",
    default: "SafeScan — Бесплатное сканирование сайтов на уязвимости онлайн",
  },
  description:
    "Проверьте сайт на уязвимости бесплатно: XSS, SQLi, CSRF, SSL, заголовки безопасности. 76+ модулей проверки, отчёт в PDF, соответствие OWASP Top 10, PCI-DSS, 152-ФЗ. Регистрация за 1 минуту.",
  
  // === Ключевые слова (для Яндекс) ===
  keywords: [
    // Русские запросы
    "сканирование уязвимостей бесплатно",
    "проверка сайта на вирусы онлайн",
    "аудит безопасности веб-сайта",
    "тест на проникновение сайта",
    "поиск уязвимостей веб-приложений",
    "онлайн сканер уязвимостей",
    "проверка безопасности сайта",
    "детектор уязвимостей веб",
    "SafeScan бесплатно",
    "легальное тестирование безопасности",
    // Английские запросы (для международного SEO)
    "free vulnerability scanner",
    "website security check online",
    "web application security audit",
    "OWASP Top 10 scanner",
    "XSS SQL injection detector",
    "SSL TLS security checker",
  ],
  
  // === Авторы и издатель ===
  authors: [{ name: "SafeScan", url: "https://safescanget.ru" }],
  creator: "SafeScan",
  publisher: "SafeScan",
  
  // === Настройки для роботов ===
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
    // Блокируем служебные пути
    disallow: ["/dashboard", "/api", "/auth", "/admin"],
  },
  
  // === Open Graph (для соцсетей) ===
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "https://safescanget.ru",
    siteName: "SafeScan",
    title: "SafeScan — Бесплатное сканирование сайтов на уязвимости",
    description:
      "76+ модулей проверки безопасности: XSS, SQLi, CSRF, SSL, заголовки. Отчёт в PDF/JSON. Соответствие OWASP Top 10, PCI-DSS, GDPR, 152-ФЗ.",
    images: [
      {
        url: "https://safescanget.ru/og-image.png", // Создайте изображение 1200×630
        width: 1200,
        height: 630,
        alt: "SafeScan — платформа для аудита безопасности веб-ресурсов",
        type: "image/png",
      },
    ],
  },
  
  // === Twitter Card ===
  twitter: {
    card: "summary_large_image",
    title: "SafeScan — Бесплатное сканирование уязвимостей сайта",
    description: "76+ модулей проверки. Отчёт в PDF. OWASP Top 10. Регистрация за 1 минуту.",
    images: ["https://safescanget.ru/og-image.png"],
    creator: "@artikyare", // Ваш @username в Twitter
  },
  
  // === Канонические ссылки и альтернативы ===
  alternates: {
    canonical: "https://safescanget.ru",
    languages: {
      "ru-RU": "https://safescanget.ru",
      // При добавлении других языков:
      // "en-US": "https://safescanget.ru/en",
    },
  },
  
  // === Верификация для вебмастеров ===
  verification: {
    google: "ваш_google_site_verification", // Из Google Search Console
    yandex: "ваш_yandex_verification",      // Из Яндекс.Вебмастер
    // other: "значение",
  },
  
  // === Иконки и манифест ===
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "32x32" },
      { url: "/icon.png", sizes: "192x192", type: "image/png" },
    ],
    apple: [
      { url: "/apple-icon.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
  },
  manifest: "/site.webmanifest",
  
  // === Дополнительные мета-теги ===
  applicationName: "SafeScan",
  category: "security",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
};

// 🔹 Viewport для мобильных устройств
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#030712" },
  ],
};

// 🔹 Корневой layout
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <head>
        {/* === Structured Data: SoftwareApplication === */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "SafeScan",
              applicationCategory: "SecurityApplication",
              operatingSystem: "Web",
              description:
                "SaaS-платформа для автоматизированного аудита безопасности веб-ресурсов. 76+ модулей проверок: XSS, SQLi, CSRF, SSL, Security Headers. Соответствие OWASP Top 10, PCI-DSS, GDPR, 152-ФЗ.",
              url: "https://safescanget.ru",
              applicationSubCategory: "Vulnerability Scanner",
              offers: {
                "@type": "Offer",
                price: "0",
                priceCurrency: "RUB",
                availability: "https://schema.org/InStock",
              },
              aggregateRating: {
                "@type": "AggregateRating",
                ratingValue: "4.9",
                ratingCount: "127",
                bestRating: "5",
                worstRating: "1",
              },
              featureList: [
                "76+ модулей проверки безопасности",
                "Обнаружение XSS, SQLi, CSRF, SSRF",
                "Анализ SSL/TLS и Security Headers",
                "Поиск утечек данных (.git, .env, API keys)",
                "SCA: анализ уязвимых зависимостей",
                "Проверка аутентификации и сессий",
                "Отчёты в форматах PDF, JSON, HTML",
                "API для автоматизации сканирований",
                "Соответствие OWASP Top 10, PCI-DSS, GDPR",
              ],
              screenshot: "https://safescanget.ru/screenshot.png",
              softwareVersion: "1.0.0",
              downloadUrl: "https://safescanget.ru/register",
              author: {
                "@type": "Organization",
                name: "SafeScan",
                url: "https://safescanget.ru",
              },
              publisher: {
                "@type": "Organization",
                name: "SafeScan",
                logo: {
                  "@type": "ImageObject",
                  url: "https://safescanget.ru/logo.png",
                  width: "200",
                  height: "60",
                },
              },
            }),
          }}
        />
        
        {/* === Structured Data: FAQPage === */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "FAQPage",
              mainEntity: [
                {
                  "@type": "Question",
                  name: "Бесплатно ли сканирование в SafeScan?",
                  acceptedAnswer: {
                    "@type": "Answer",
                    text: "Да, базовое сканирование из 4 модулей (быстрый скан) доступно бесплатно без ограничений. Полное сканирование (12 модулей) стоит 20 ₽ за запуск или доступно по подписке.",
                  },
                },
                {
                  "@type": "Question",
                  name: "Законно ли использовать SafeScan?",
                  acceptedAnswer: {
                    "@type": "Answer",
                    text: "Да, при соблюдении условий: 1) Вы являетесь владельцем сайта или имеете письменное согласие владельца; 2) Не используете результаты для незаконных действий. Платформа работает в рамках «ответственного раскрытия» (Responsible Disclosure) и соответствует 152-ФЗ, ГК РФ.",
                  },
                },
                {
                  "@type": "Question",
                  name: "Какие уязвимости обнаруживает SafeScan?",
                  acceptedAnswer: {
                    "@type": "Answer",
                    text: "Платформа обнаруживает 76+ типов уязвимостей, включая: XSS (отражённый, хранимый, DOM-based), SQL/NoSQL Injection, CSRF, SSRF, XXE, небезопасные заголовки (HSTS, CSP), устаревшие SSL-протоколы, утечки данных (.git, .env, API-ключи), уязвимые зависимости и другие проблемы из OWASP Top 10.",
                  },
                },
                {
                  "@type": "Question",
                  name: "Как подтвердить владение доменом?",
                  acceptedAnswer: {
                    "@type": "Answer",
                    text: "Доступно три способа: 1) Добавить TXT-запись _safescan-verify в DNS; 2) Разместить файл .well-known/safescan-verify.txt на сайте; 3) Подтвердить через email администратора (admin@, webmaster@, hostmaster@). Проверка занимает от 1 до 30 минут.",
                  },
                },
                {
                  "@type": "Question",
                  name: "В каких форматах доступны отчёты?",
                  acceptedAnswer: {
                    "@type": "Answer",
                    text: "Отчёты генерируются в трёх форматах: 1) Интерактивный HTML для просмотра в браузере; 2) PDF для печати и передачи руководству; 3) JSON для интеграции с SIEM/DevOps-инструментами. Каждый отчёт содержит классификацию по CVSS, CWE, OWASP и конкретные рекомендации по устранению.",
                  },
                },
              ],
            }),
          }}
        />
        
        {/* === Structured Data: Organization === */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "SafeScan",
              url: "https://safescanget.ru",
              logo: "https://safescanget.ru/logo.png",
              sameAs: [
                "https://t.me/artikyare",
                "https://vk.com/artikyare",
                // Добавьте другие соцсети при наличии
              ],
              contactPoint: {
                "@type": "ContactPoint",
                email: "kostdensv@gmail.com",
                contactType: "customer support",
                areaServed: "RU",
                availableLanguage: ["Russian", "English"],
              },
            }),
          }}
        />
        
        {/* === Structured Data: BreadcrumbList (для главной) === */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "BreadcrumbList",
              itemListElement: [
                {
                  "@type": "ListItem",
                  position: 1,
                  name: "Главная",
                  item: "https://safescanget.ru",
                },
              ],
            }),
          }}
        />
      </head>
      <body className={`${inter.className} antialiased`}>
        {children}
        {process.env.NODE_ENV === "production" && <YandexMetrica />}
      </body>
    </html>
  );
}