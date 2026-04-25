# SafeScan — Полная документация

> **Версия:** 2.1 | **Дата:** Апрель 2026 | **Статус:** Development

## Оглавление

- [1. Обзор](#1-обзор)
- [2. Архитектура](#2-архитектура)
- [3. Технологический стек](#3-технологический-стек)
- [4. Быстрый старт](#4-быстрый-старт)
- [5. Структура проекта](#5-структура-проекта)
- [6. Модули сканирования](#6-модули-сканирования)
- [7. API документация](#7-api-документация)
- [8. Frontend руководство](#8-frontend-руководство)
- [9. Конфигурация](#9-конфигурация)
- [10. Развёртывание](#10-развёртывание)
- [11. Поиск и устранение неисправностей](#11-поиск-и-устранение-неисправностей)
- [12. Разработка](#12-разработка)
- [13. Безопасность и Compliance](#13-безопасность-и-compliance)
- [14. Полезные команды](#14-полезные-команды)

---

## 1. Обзор

SafeScan — это платформа для автоматизированного аудита безопасности веб-ресурсов, работающая исключительно на основании согласия владельцев доменов. Платформа обнаруживает уязвимости и предоставляет детальные рекомендации по их устранению.

### Возможности

- 🔍 **12 модулей проверок** — от Security Headers до Network Infrastructure
- 📊 **Детальные отчёты** — оценка рисков, классификация по CVSS, рекомендации
- 🔐 **Безопасность** — изолированные Celery workers, audit log, JWT аутентификация
- 📋 **Compliance** — OWASP Top 10, NIST SP 800-53, PCI-DSS, 152-ФЗ, GDPR
- 📝 **Логи сканирования в реальном времени** — отслеживание прогресса через UI
- 🗄️ **Хранение артефактов** — MinIO (S3-compatible) для отчётов

### Что НЕ делает SafeScan

- ❌ Не эксплуатирует уязвимости — только обнаружение
- ❌ Не выполняет DoS/нагрузочное тестирование
- ❌ Не сканирует без подтверждения владения доменом
- ❌ Не собирает и не хранит персональные данные без необходимости

---

## 2. Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Auth    │  │Dashboard │  │  Scans   │  │    Reports       │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       └──────────────┴──────────────┴────────────────┘           │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTPS (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   Auth   │  │  Domain  │  │  Scan    │  │   Vulnerability  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       └──────────────┴──────────────┴────────────────┘           │
│  Middleware: JWT Auth, CORS, Security Headers                    │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Message Queue (Celery + Redis)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Task Queue  │  │ Result      │  │  Scheduler (Beat)       │  │
│  │ (scans)     │  │ Backend     │  │  cleanup, reverify      │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │
└─────────┼────────────────┼───────────────────────────────────────┘
          │                │
          ▼                ▼
┌────────────────┐ ┌────────────────┐
│ ISOLATED       │ │ DATA LAYER     │
│ WORKERS        │ │ PostgreSQL 16  │
│                │ │ Redis 7        │
│ • Scan Tasks   │ │ MinIO (S3)     │
│ • Module exec  │ │ Mailhog (test) │
└────────┬───────┘ └────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SCANNING MODULES (12)                          │
│  Security Headers │ SSL/TLS │ XSS │ Injection │ CSRF/CORS       │
│  SSRF/XXE/Traversal │ Auth & Sessions │ Server Config │ SCA     │
│  Info Leakage │ App Logic │ Network & Infrastructure           │
└─────────────────────────────────────────────────────────────────┘
```

### Компоненты

| Компонент | Технология | Назначение |
|---|---|---|
| **Frontend** | Next.js 14 + TypeScript + Tailwind | UI/UX, dashboard, управление сканами |
| **Backend API** | FastAPI (Python 3.12) | REST API, аутентификация, маршрутизация |
| **Database** | PostgreSQL 16 | Хранение пользователей, сканов, уязвимостей |
| **Cache/Queue** | Redis 7 | Очередь задач Celery, кэш, сессии, логи сканов |
| **Task Queue** | Celery + Redis | Асинхронное выполнение сканов |
| **Workers** | Docker-контейнеры (prefork, 4 concurrency) | Изолированное выполнение модулей сканирования |
| **Scheduler** | Celery Beat | Периодические задачи (очистка данных) |
| **Storage** | MinIO (S3-compatible) | Хранение отчётов и доказательств |
| **Monitoring** | Flower | UI для мониторинга Celery workers |
| **Email** | Mailhog | Тестовый SMTP сервер (development) |

---

## 3. Технологический стек

### Backend

| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.12 | Язык выполнения |
| FastAPI | 0.115.6 | Веб-фреймворк (async) |
| SQLAlchemy | 2.0.36 | ORM для работы с БД |
| asyncpg | 0.30.0 | Асинхронный драйвер PostgreSQL |
| Alembic | 1.14.1 | Миграции базы данных |
| Celery | 5.4.0 | Очередь задач |
| Pydantic | 2.10.4 | Валидация и сериализация данных |
| httpx | 0.28.1 | HTTP-клиент для сканирования |
| python-jose | 3.3.0 | JWT токены |
| passlib + bcrypt | 1.7.4 / 4.0.1 | Хэширование паролей |
| pyopenssl | 24.3.0 | SSL/TLS проверки |
| weasyprint | 63.1 | Генерация PDF-отчётов |
| aioboto3 | 13.2.0 | Работа с S3 (MinIO) |

### Frontend

| Технология | Версия | Назначение |
|---|---|---|
| Next.js | 14.2 | React-фреймворк (App Router) |
| TypeScript | 5.x | Типобезопасность |
| Tailwind CSS | 3.x | Стилизация |
| shadcn/ui | — | Компоненты UI |
| Axios | — | HTTP-клиент |
| Zustand | — | Управление состоянием |
| Lucide React | — | Иконки |

### Инфраструктура

| Технология | Версия | Назначение |
|---|---|---|
| Docker | — | Контейнеризация |
| Docker Compose | — | Оркестрация development |
| PostgreSQL | 16-alpine | Основная база данных |
| Redis | 7-alpine | Очередь, кэш, логи сканов |
| MinIO | latest | S3-хранилище |
| Mailhog | latest | Тестовый SMTP |
| Flower | latest | Мониторинг Celery |

---

## 4. Быстрый старт

### Предварительные требования

- **Docker Desktop** — [скачать](https://www.docker.com/products/docker-desktop/)
- Минимум 4 ГБ свободной оперативной памяти
- Свободные порты: `3000`, `5432`, `6379`, `8000`, `5555`, `8025`, `9000`, `9001`

### Запуск

**Windows (через `start.bat`):**
```powershell
.\start.bat
```

**Вручную:**
```bash
# 1. Настроить окружение (при первом запуске)
cp .env.example .env

# 2. Запустить все сервисы
docker compose up -d

# 3. Подождать 30-60 секунд

# 4. Проверить готовность
curl http://localhost:8000/health
# Ожидается: {"status":"healthy","service":"safescan-api"}
```

### Доступные сервисы

| Сервис | URL | Описание |
|---|---|---|
| **Frontend** | http://localhost:3000 | Основное приложение |
| **API Docs** | http://localhost:8000/docs | Swagger UI (интерактивная документация) |
| **API ReDoc** | http://localhost:8000/redoc | ReDoc документация |
| **Flower** | http://localhost:5555 | Мониторинг Celery workers |
| **Mailhog** | http://localhost:8025 | Тестовые email |
| **MinIO Console** | http://localhost:9001 | Управление хранилищем |

### Первый запуск

1. Откройте http://localhost:3000
2. Нажмите **«Зарегистрироваться»**
3. Создайте аккаунт (email автоматически верифицируется в dev-режиме)
4. Добавьте домен → запустите скан

### Остановка

```bash
# Остановить все сервисы
docker compose down

# Остановить и удалить все данные (volumes)
docker compose down -v
```

---

## 5. Структура проекта

```
SAFETEST/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # API эндпоинты
│   │   │   ├── auth.py           # Регистрация, логин, MFA
│   │   │   ├── scans.py          # CRUD сканов + логи
│   │   │   ├── domains.py        # Управление доменами
│   │   │   ├── vulnerabilities.py # Уязвимости
│   │   │   ├── reports.py        # Генерация отчётов
│   │   │   └── ...
│   │   ├── core/                 # Ядро приложения
│   │   │   ├── config.py         # Настройки из .env
│   │   │   ├── database.py       # Подключение к БД
│   │   │   └── security.py       # JWT, хэширование, middleware
│   │   ├── models/               # SQLAlchemy модели
│   │   │   ├── user.py           # Пользователи
│   │   │   ├── domain.py         # Домены
│   │   │   ├── scan.py           # Сканы
│   │   │   ├── vulnerability.py  # Уязвимости
│   │   │   ├── audit_log.py      # Audit log
│   │   │   ├── organization.py   # Организации
│   │   │   ├── api_key.py        # API ключи
│   │   │   └── notification.py   # Уведомления
│   │   ├── schemas/              # Pydantic схемы валидации
│   │   │   ├── user.py           # Схемы пользователей
│   │   │   ├── scan.py           # Схемы сканов
│   │   │   ├── domain.py         # Схемы доменов
│   │   │   ├── vulnerability.py  # Схемы уязвимостей
│   │   │   ├── api_key.py        # Схемы API ключей
│   │   │   └── base.py           # BaseSchema (UUID сериализация)
│   │   ├── workers/              # Celery workers и сканирование
│   │   │   ├── celery_app.py     # Конфигурация Celery
│   │   │   ├── tasks.py          # Celery задачи
│   │   │   ├── scanner.py        # Оркестратор сканирования
│   │   │   ├── scan_logger.py    # Логирование сканов в Redis
│   │   │   └── modules/          # Модули сканирования (12 шт.)
│   │   │       ├── base.py       # Базовый класс ScanModule
│   │   │       ├── security_headers.py
│   │   │       ├── ssl_tls.py
│   │   │       ├── xss.py
│   │   │       ├── injection.py
│   │   │       ├── csrf_cors.py
│   │   │       ├── ssrf_xxe_traversal.py
│   │   │       ├── auth_sessions.py
│   │   │       ├── server_config.py
│   │   │       ├── sca.py
│   │   │       ├── info_leakage.py
│   │   │       ├── app_logic.py
│   │   │       └── network.py
│   │   ├── services/             # Бизнес-логика
│   │   │   └── audit.py          # Audit log сервис
│   │   ├── utils/                # Утилиты
│   │   └── main.py               # Точка входа FastAPI
│   ├── db/init/                  # Init скрипты БД
│   ├── Dockerfile                # Образ backend
│   ├── requirements.txt          # Python зависимости
│   └── pyproject.toml            # Конфигурация проекта
│
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   │   ├── (auth)/           # Страницы авторизации
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/      # Основные страницы
│   │   │   │   ├── scans/
│   │   │   │   │   ├── page.tsx          # Список сканов
│   │   │   │   │   ├── new/page.tsx      # Создание скана
│   │   │   │   │   └── [id]/page.tsx     # Детали скана + логи
│   │   │   │   ├── domains/
│   │   │   │   └── vulnerabilities/
│   │   │   ├── layout.tsx        # Корневой layout
│   │   │   └── globals.css       # Глобальные стили
│   │   ├── components/           # React компоненты
│   │   │   └── ui/               # UI компоненты
│   │   │       ├── input.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── badge.tsx     # ScanStatusBadge, SeverityBadge
│   │   │       └── modal.tsx
│   │   ├── lib/
│   │   │   ├── api.ts            # API клиент (Axios)
│   │   │   └── utils.ts          # Утилиты форматирования
│   │   ├── hooks/
│   │   │   └── useAuth.ts        # Zustand store авторизации
│   │   └── types/
│   │       └── index.ts          # TypeScript типы
│   ├── Dockerfile                # Образ frontend
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.js
│
├── docker-compose.yml            # Оркестрация всех сервисов
├── .env                          # Переменные окружения
├── .env.example                  # Шаблон переменных
├── start.bat                     # Скрипт запуска (Windows)
├── stop.bat                      # Скрипт остановки (Windows)
├── QUICKSTART.md                 # Краткое руководство
├── README.md                     # README проекта
└── TECHNICAL_SPECIFICATION.md    # Техническое задание
```

---

## 6. Модули сканирования

### Обзор

Каждый модуль наследуется от `ScanModule` и реализует метод `execute() -> ScanResult`. Модули выполняются последовательно внутри Celery worker.

### Базовый класс

```python
# backend/app/workers/modules/base.py
class ScanModule(ABC):
    def __init__(self, domain: str, scan_id: str, config):
        self.domain = domain
        self.scan_id = scan_id
        self.config = config
        self.base_url = f"https://{domain}"
        self.timeout = config.SCAN_TIMEOUT_SECONDS      # 60 сек
        self.max_crawl_depth = config.SCAN_MAX_CRAWL_DEPTH  # 2
        self.max_pages = config.SCAN_MAX_PAGES          # 50
        self.rate_limit = config.SCAN_REQUESTS_PER_SECOND  # 20 req/s

    @abstractmethod
    async def execute(self) -> ScanResult:
        pass

    async def _make_request(self, method="GET", path="", headers=None, ...) -> httpx.Response:
        """HTTP-запрос с rate limiting и таймаутами."""
```

### Таблица модулей

| # | Модуль | Файл | Что проверяет |
|---|---|---|---|
| 1 | **Security Headers** | `security_headers.py` | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| 2 | **SSL/TLS** | `ssl_tls.py` | Протоколы TLS, шифры, сертификат, HSTS на HTTPS |
| 3 | **XSS** | `xss.py` | Reflected, Stored, DOM-based XSS через безопасные payload'ы |
| 4 | **Injection** | `injection.py` | SQLi, NoSQLi, Command Injection, SSTI |
| 5 | **CSRF/CORS** | `csrf_cors.py` | CSRF-токены, CORS misconfig (wildcard/null origin), cookie security |
| 6 | **SSRF/XXE/Traversal** | `ssrf_xxe_traversal.py` | SSRF (AWS metadata, localhost), XXE, Path Traversal |
| 7 | **Auth & Sessions** | `auth_sessions.py` | Cookie flags, JWT endpoints, password policy, brute-force protection |
| 8 | **Server Config** | `server_config.py` | Directory listing, debug endpoints (26 путей), dangerous HTTP methods |
| 9 | **SCA** | `sca.py` | Уязвимые JS библиотеки, CMS detection, server fingerprinting |
| 10 | **Info Leakage** | `info_leakage.py` | `.git`, `.env`, backup files, API keys в JS, PII, metadata |
| 11 | **App Logic** | `app_logic.py` | Rate limiting, CAPTCHA, IDOR indicators, privilege escalation |
| 12 | **Network** | `network.py` | DNS, SPF/DMARC, CDN/WAF detection, IPv6, subdomain takeover |

### Типы сканов

| Тип | Модули | Время (примерно) |
|---|---|---|
| **Quick** | security_headers, ssl_tls, server_config, info_leakage | ~30 сек |
| **Full** | Все 12 модулей | ~2-5 мин |
| **Custom** | Выбранные модули | Зависит от выбора |

### Настройки сканирования

| Параметр | Значение по умолчанию | Описание |
|---|---|---|
| `SCAN_MAX_CONCURRENT` | 10 | Макс. одновременных сканов |
| `SCAN_MAX_CRAWL_DEPTH` | 2 | Макс. глубина обхода страниц |
| `SCAN_MAX_PAGES` | 50 | Макс. страниц за скан |
| `SCAN_REQUESTS_PER_SECOND` | 20 | Rate limit к целевому ресурсу |
| `SCAN_TIMEOUT_SECONDS` | 60 | Таймаут на один модуль |
| `SCAN_USER_AGENT` | `SafeScan/1.0 (+https://safescan.io)` | User-Agent запросов |
| `DATA_RETENTION_DAYS` | 90 | Срок хранения данных сканов |

### Добавление нового модуля

1. Создайте файл `backend/app/workers/modules/my_module.py`:

```python
import asyncio
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity

class MyModule(ScanModule):
    async def execute(self) -> ScanResult:
        self.start_time = asyncio.get_event_loop().time()

        # Логика проверки
        response = await self._make_request(path="/")
        if response and not response.headers.get("x-my-header"):
            self._log_finding(self._create_finding(
                title="Missing X-My-Header",
                description="Сервер не возвращает заголовок X-My-Header",
                severity=Severity.MEDIUM,
                remediation="Добавьте X-My-Header в ответы сервера",
                cwe_id="CWE-693",
                owasp_category="A05:2021",
            ))

        duration = asyncio.get_event_loop().time() - self.start_time
        return ScanResult(
            module="my_module",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )
```

2. Зарегистрируйте модуль в `backend/app/workers/scanner.py` — добавьте в `module_registry` и импорты.

---

## 7. API документация

### Базовый URL

```
http://localhost:8000/api/v1
```

### Аутентификация

Все защищённые эндпоинты требуют заголовок:
```
Authorization: Bearer <access_token>
```

Токен получается через `POST /api/v1/auth/login`.

### Основные эндпоинты

#### Auth

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация нового пользователя |
| POST | `/auth/login` | Вход (возвращает access + refresh токены) |
| GET | `/users/me` | Получение текущего пользователя |
| PUT | `/users/me` | Обновление профиля |
| POST | `/users/change-password` | Смена пароля |

#### Domains

| Метод | Путь | Описание |
|---|---|---|
| GET | `/domains/` | Список доменов пользователя |
| POST | `/domains/` | Добавить домен |
| GET | `/domains/{id}` | Детали домена |
| DELETE | `/domains/{id}` | Удалить домен |
| POST | `/domains/{id}/verify` | Проверить верификацию |

#### Scans

| Метод | Путь | Описание |
|---|---|---|
| GET | `/scans/` | Список сканов (фильтры: status, scan_type) |
| POST | `/scans/` | Создать и запустить скан |
| GET | `/scans/{id}` | Детали скана |
| GET | `/scans/{id}/status` | Статус сканирования в реальном времени |
| GET | `/scans/{id}/logs` | **Логи сканирования** |
| POST | `/scans/{id}/cancel` | Отменить скан |

#### Vulnerabilities

| Метод | Путь | Описание |
|---|---|---|
| GET | `/vulnerabilities/` | Список уязвимостей (фильтр: scan_id, severity) |
| GET | `/vulnerabilities/{id}` | Детали уязвимости |

#### Reports

| Метод | Путь | Описание |
|---|---|---|
| GET | `/reports/{scan_id}/json` | Отчёт в формате JSON |
| GET | `/reports/{scan_id}/pdf` | PDF-отчёт (blob) |
| GET | `/reports/{scan_id}/html` | HTML-отчёт |

### Примеры запросов

**Регистрация:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"MyPass123!","first_name":"John","last_name":"Doe"}'
```

**Вход:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"MyPass123!"}'
```

**Создание скана:**
```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"domain_id":"<uuid>","scan_type":"quick","consent_acknowledged":true}'
```

**Получение логов скана:**
```bash
curl "http://localhost:8000/api/v1/scans/<scan_id>/logs?offset=0&limit=200" \
  -H "Authorization: Bearer <token>"
```

Ответ:
```json
{
  "logs": [
    {
      "timestamp": "2026-04-10T20:48:32.093063+00:00",
      "level": "INFO",
      "module": "security_headers",
      "message": "Starting module 1/4: security_headers"
    },
    {
      "timestamp": "2026-04-10T20:48:33.655327+00:00",
      "level": "WARN",
      "module": "ssl_tls",
      "message": "[MEDIUM] HSTS Missing on HTTPS"
    }
  ],
  "total": 13,
  "has_more": false
}
```

---

## 8. Frontend руководство

### Структура страниц

| Путь | Описание |
|---|---|
| `/login` | Страница входа |
| `/register` | Страница регистрации |
| `/dashboard` | Главная панель (статистика, последние сканы) |
| `/scans` | Список всех сканов |
| `/scans/new` | Создание нового скана |
| `/scans/[id]` | Детали скана + уязвимости + **логи** |
| `/domains` | Управление доменами |
| `/vulnerabilities` | Список всех уязвимостей |
| `/vulnerabilities/[id]` | Детали уязвимости |

### API клиент

API клиент находится в `frontend/src/lib/api.ts` и использует Axios с автоматической подстановкой JWT токена и refresh при 401.

```typescript
import { scansApi, domainsApi, vulnsApi } from '@/lib/api';

// Получить список сканов
const scans = await scansApi.list({ status: 'completed' });

// Создать скан
const scan = await scansApi.create({
  domain_id: 'uuid',
  scan_type: 'quick',
  consent_acknowledged: true,
});

// Получить логи скана
const logs = await scansApi.getLogs(scanId, 0, 200);
```

### Логи сканирования (UI)

На странице деталей скана (`/scans/[id]`) при активном сканировании (`running` или `queued`) отображается секция **«Логи сканирования»**:

- 🔽 Сворачиваемая панель с счётчиком записей
- 📝 Терминал-подобный вывод с цветовой кодировкой:
  - 🟢 `[INFO]` — зелёный
  - 🟡 `[WARN]` — жёлтый
  - 🔴 `[ERROR]` — красный
- 🔵 Модуль указывается в синих скобках: `[security_headers]`
- 🔄 Автопрокрутка (вкл/выкл)
- ⏱ Автообновление каждые 5 секунд
- 🔄 Ручное обновление кнопкой

---

## 9. Конфигурация

### Файл `.env`

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
```

### Ключевые переменные

#### Приложение
| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_NAME` | SafeScan | Название приложения |
| `APP_ENV` | development | Окружение: `development`, `staging`, `production` |
| `APP_DEBUG` | true | Режим отладки |
| `APP_SECRET_KEY` | (обязательно) | Секретный ключ приложения |
| `APP_CORS_ORIGINS` | http://localhost:3000 | Разрешённые CORS origins (через запятую) |

#### База данных
| Переменная | По умолчанию | Описание |
|---|---|---|
| `POSTGRES_USER` | safescan | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | changeme_password | Пароль PostgreSQL |
| `POSTGRES_DB` | safescan | Имя базы данных |
| `DATABASE_URL` | postgresql+asyncpg://... | Строка подключения (async) |

#### Redis
| Переменная | По умолчанию | Описание |
|---|---|---|
| `REDIS_URL` | redis://localhost:6379/0 | URL Redis |

#### JWT
| Переменная | По умолчанию | Описание |
|---|---|---|
| `JWT_SECRET_KEY` | (обязательно) | Секретный ключ JWT |
| `JWT_ALGORITHM` | HS256 | Алгоритм подписи |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Время жизни access токена |

#### Сканирование
| Переменная | По умолч. | Описание |
|---|---|---|
| `SCAN_MAX_CONCURRENT` | 10 | Макс. параллельных сканов |
| `SCAN_MAX_CRAWL_DEPTH` | 2 | Макс. глубина обхода |
| `SCAN_MAX_PAGES` | 50 | Макс. страниц за скан |
| `SCAN_REQUESTS_PER_SECOND` | 20 | Rate limit (req/s) |
| `SCAN_TIMEOUT_SECONDS` | 60 | Таймаут модуля (сек) |

#### S3 / MinIO
| Переменная | По умолчанию | Описание |
|---|---|---|
| `S3_ENDPOINT_URL` | http://minio:9000 | URL S3-совместимого хранилища |
| `S3_ACCESS_KEY` | minioadmin | Ключ доступа |
| `S3_SECRET_KEY` | minioadmin | Секретный ключ |
| `S3_BUCKET` | safescan-reports | Имя бакета |

### Генерация безопасных ключей

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 10. Развёртывание

### Development (текущее)

```bash
docker compose up -d
```

Все сервисы запускаются через Docker Compose. Фронтенд работает в режиме `next dev` с hot-reload.

### Staging

Рекомендуется:
- **Kubernetes** (minikube / k3s)
- **PostgreSQL** с репликацией
- **MinIO** или реальный S3
- **Prometheus + Grafana** для мониторинга
- **Let's Encrypt** (cert-manager) для SSL

### Production

| Компонент | Рекомендация |
|---|---|
| **Cloud** | AWS (EKS) / GCP (GKE) / Yandex Cloud |
| **Ingress/WAF** | NGINX Ingress + ModSecurity |
| **Database** | Managed PostgreSQL (RDS / Cloud SQL) |
| **Redis** | Managed Redis (ElastiCache / Memorystore) |
| **Storage** | S3 / GCS |
| **Secrets** | HashiCorp Vault / AWS Secrets Manager |
| **CI/CD** | GitHub Actions + ArgoCD |
| **Monitoring** | Prometheus + Grafana + PagerDuty |

---

## 11. Поиск и устранение неисправностей

### Контейнеры не запускаются

```bash
# Проверить статус
docker compose ps

# Посмотреть логи конкретного сервиса
docker compose logs backend
docker compose logs frontend
docker compose logs celery-worker

# Пересобрать с нуля
docker compose build --no-cache
docker compose down -v
docker compose up -d
```

### Backend не отвечает

```bash
# Проверить health
curl http://localhost:8000/health

# Посмотреть логи
docker compose logs backend

# Перезапустить
docker compose restart backend
```

### Сканы зависают или падают

```bash
# Логи Celery worker
docker compose logs celery-worker

# Проверить Redis
docker exec safescan-redis redis-cli -a redis_password_dev ping

# Проверить очередь задач
docker exec safescan-redis redis-cli -a redis_password_dev llen celery
```

### Фронтенд не загружается

```bash
# Очистить кэш Next.js
docker exec safescan-frontend rm -rf .next
docker compose restart frontend
```

### Порт занят

```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Освободить порт или изменить маппинг в docker-compose.yml
```

### Ошибки CORS

Убедитесь что `APP_CORS_ORIGINS` в `.env` содержит правильный URL фронтенда:
```
APP_CORS_ORIGINS=http://localhost:3000
```

---

## 12. Разработка

### Запуск backend локально (без Docker)

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Запуск frontend локально

```bash
cd frontend
npm install
npm run dev
```

### Тестирование

```bash
# Backend тесты
cd backend
pytest

# Линтинг
ruff check app/

# Типы
mypy app/
```

### Как добавить новый эндпоинт API

1. Создайте файл в `backend/app/api/v1/endpoints/my_feature.py`
2. Зарегистрируйте роутер в `backend/app/api/v1/router.py`

```python
# backend/app/api/v1/endpoints/my_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_items():
    return {"items": []}
```

```python
# backend/app/api/v1/router.py
from app.api.v1.endpoints import my_feature

api_router.include_router(my_feature.router, prefix="/my-feature", tags=["My Feature"])
```

### Как добавить новую страницу Frontend

1. Создайте файл в `frontend/src/app/my-page/page.tsx`
2. Используйте `'use client'` для клиентских компонентов

---

## 13. Безопасность и Compliance

### Механизмы защиты платформы

| Механизм | Описание |
|---|---|
| **JWT Authentication** | Access + Refresh токены, автоматический refresh |
| **CORS** | Строгий контроль разрешённых origins |
| **Security Headers** | HSTS, X-Frame-Options, X-Content-Type-Options, CSP |
| **Password Hashing** | bcrypt с автоматической солью |
| **SQL Injection Protection** | SQLAlchemy ORM + параметризованные запросы |
| **Audit Log** | Все действия логируются (кто, что, когда) |
| **Rate Limiting** | Сканирование ограничено 20 req/s к цели |
| **Isolated Workers** | Celery workers в отдельных контейнерах |
| **Data Retention** | Автоматическая очистка через 90 дней |

### Безопасность сканирования

| Механизм | Значение |
|---|---|
| **User-Agent** | `SafeScan/1.0 (+https://safescan.io)` — идентифицирует сканер |
| **Rate Limiting** | 20 запросов в секунду к целевому ресурсу |
| **Таймауты** | 5 сек на запрос, 60 сек на модуль |
| **Max Pages** | 50 страниц за скан |
| **Max Crawl Depth** | 2 уровня вложенности |
| **Safe Payloads** | `SLEEP(0)`, `echo SXSCANX` — без эксплуатации |
| **SSL Verify** | `verify=True` для всех outbound-запросов |

### Compliance

| Стандарт | Покрытие |
|---|---|
| **OWASP Top 10 2021** | Все 10 категорий покрыты модулями |
| **NIST SP 800-53** | SC-8, SC-12, SC-13, CM-7 |
| **PCI-DSS** | Requirement 6.5, 11.3 |
| **152-ФЗ** | Локализация данных, минимизация PII |
| **GDPR** | Art. 32 (безопасность обработки), право на удаление |

---

## 14. Полезные команды

### Управление сервисами

```bash
# Запустить все
docker compose up -d

# Остановить все
docker compose down

# Перезапустить конкретный сервис
docker compose restart backend
docker compose restart frontend
docker compose restart celery-worker

# Остановить и удалить данные
docker compose down -v
```

### Логи

```bash
# Все логи в реальном времени
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f frontend

# Последние 50 строк
docker compose logs --tail=50 backend
```

### Docker

```bash
# Список контейнеров
docker compose ps

# Список образов
docker images | grep safetest

# Очистить неиспользуемые образы
docker system prune -a

# Зайти в контейнер
docker exec -it safescan-backend bash
docker exec -it safescan-frontend sh
docker exec -it safescan-redis redis-cli -a redis_password_dev
```

### База данных

```bash
# Подключиться к PostgreSQL
docker exec -it safescan-postgres psql -U safescan -d safescan

# Посмотреть таблицы
\dt

# Посмотреть сканы
SELECT id, domain_id, status, scan_type, total_findings, grade FROM scans ORDER BY created_at DESC LIMIT 10;

# Посмотреть уязвимости
SELECT id, scan_id, module, title, severity FROM vulnerabilities ORDER BY created_at DESC LIMIT 20;
```

### Redis

```bash
# Подключиться
docker exec -it safescan-redis redis-cli -a redis_password_dev

# Посмотреть все ключи
KEYS *

# Посмотреть ключи сканов
KEYS scan:logs:*

# Посмотреть длину очереди
LLEN celery

# Посмотреть логи скана
LRANGE scan:logs:<scan_id> 0 -1

# Удалить логи скана
DEL scan:logs:<scan_id>
```

### API тестирование

```bash
# Health check
curl http://localhost:8000/health

# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"MyPass123!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Список сканов
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/scans/

# Создать скан
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"<uuid>","scan_type":"quick","consent_acknowledged":true}'

# Логи скана
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/scans/<scan_id>/logs?offset=0&limit=100"
```

---

## Приложение: Модель данных

### Таблицы базы данных

| Таблица | Описание | Ключевые поля |
|---|---|---|
| `users` | Пользователи | id, email, password_hash, role, mfa_enabled, email_verified |
| `organizations` | Организации | id, name, slug, max_domains, max_concurrent_scans |
| `domains` | Домены для сканирования | id, domain, is_verified, verification_method, user_id |
| `scans` | Сканы | id, domain_id, user_id, scan_type, status, modules_enabled, risk_score, grade |
| `vulnerabilities` | Найденные уязвимости | id, scan_id, module, title, severity, cvss_score, remediation |
| `audit_log` | Журнал действий | id, user_id, action, resource_type, resource_id, details (JSONB) |
| `api_keys` | API ключи | id, user_id, name, key_prefix, key_hash, scopes, is_active |
| `notifications` | Настройки уведомлений | id, user_id, notification_type, channel, is_enabled, config (JSONB) |

### Статусы скана

| Статус | Описание |
|---|---|
| `queued` | Скан в очереди, ожидает worker |
| `running` | Сканирование выполняется |
| `completed` | Сканирование завершено успешно |
| `failed` | Сканирование завершилось с ошибкой |
| `cancelled` | Сканирование отменено пользователем |

### Уровни серьёзности уязвимостей

| Уровень | Цвет | Описание |
|---|---|---|
| `critical` | 🔴 Красный | Критическая уязвимость, требует немедленного устранения |
| `high` | 🟠 Оранжевый | Высокая серьёзность |
| `medium` | 🟡 Жёлтый | Средняя серьёзность |
| `low` | 🔵 Синий | Низкая серьёзность |
| `info` | ⚪ Серый | Информационное сообщение |

### Расчёт Risk Score и Grade

**Risk Score** (0–10):
```
risk_score = min(10.0, log10(total_weight + 1) * 3.5)

where total_weight = Σ(severity_weight × count)
  critical = 10.0, high = 7.5, medium = 4.0, low = 1.0, info = 0.0
```

**Grade**:
| Score | Grade |
|---|---|
| 0.0 | A+ |
| < 1.5 | A |
| < 3.0 | B |
| < 5.0 | C |
| < 7.0 | D |
| ≥ 7.0 | F |
