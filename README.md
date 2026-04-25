# SafeScan — Платформа для легального автоматизированного сканирования сайтов на уязвимости

> **Defensive Security Platform** — обнаружение, а не эксплуатация.

## 📖 Полная документация

Полная документация доступна в файле **[docs/DOCUMENTATION.md](./docs/DOCUMENTATION.md)**.

Там вы найдёте:
- 🏗️ Подробную архитектуру
- 🚀 Быстрый старт
- 🔍 Описание всех 12 модулей сканирования
- 📡 API документацию с примерами запросов
- 🎨 Frontend руководство
- ⚙️ Конфигурацию и настройки
- 🔧 Поиск и устранение неисправностей
- 🛡️ Безопасность и Compliance
- 📋 Полезные команды

## 🔒 О проекте

SafeScan — это SaaS-платформа для автоматизированного аудита безопасности веб-ресурсов, работающая исключительно на основании предварительного письменного согласия владельцев доменов.

### Возможности

- 🔍 **76+ модулей проверок** — от Security Headers до Business Logic
- 🛡️ **Обязательная верификация домена** — DNS TXT, File, Email
- 📊 **Детальные отчёты** — PDF, HTML, JSON с CVSS классификацией
- 🔐 **Полная безопасность** — изолированные workers, audit log, RBAC
- 📋 **Compliance** — OWASP Top 10, NIST SP 800-53, PCI-DSS, 152-ФЗ, GDPR
- 🔗 **Интеграции** — SIEM, Jira, Slack, Webhooks

## 📋 Содержание

- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Модули проверок](#модули-проверок)
- [API документация](#api-документация)
- [Развёртывание](#развёртывание)
- [Лицензия](#лицензия)

## 🏗️ Архитектура

```
Frontend (Next.js) → API Gateway (FastAPI) → Task Queue (Celery/Redis)
                                                      ↓
                                            Isolated Workers (Docker)
                                                      ↓
                                         PostgreSQL + MinIO (S3)
```

## 🛠️ Технологический стек

| Слой | Технология |
|---|---|
| **Frontend** | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| **Backend** | Python 3.12 + FastAPI + SQLAlchemy |
| **Queue** | Celery + Redis |
| **Database** | PostgreSQL 16 |
| **Storage** | MinIO (S3-compatible) |
| **Workers** | Docker-изолированные процессы |
| **Monitoring** | Flower (Celery), Prometheus, Grafana |

## 🚀 Быстрый старт

### Предварительные требования

- Docker & Docker Compose
- Python 3.12+ (для локальной разработки)
- Node.js 20+ (для локальной разработки)

### Запуск

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd safescan

# 2. Настроить окружение
cp .env.example .env
# Отредактируйте .env при необходимости

# 3. Запустить все сервисы
docker-compose up -d

# 4. Применить миграции БД
docker-compose exec backend alembic upgrade head

# 5. Открыть приложение
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Flower (Celery UI): http://localhost:5555
# Mailhog (Test Email): http://localhost:8025
# MinIO Console: http://localhost:9001
```

## 📁 Структура проекта

```
safescan/
├── backend/
│   ├── app/
│   │   ├── api/              # API эндпоинты (Router)
│   │   ├── core/             # Конфигурация, безопасность
│   │   ├── models/           # SQLAlchemy модели
│   │   ├── schemas/          # Pydantic схемы
│   │   ├── services/         # Бизнес-логика
│   │   ├── workers/          # Celery workers & scanning modules
│   │   │   ├── modules/      # Модули проверок (12 модулей)
│   │   │   └── celery_app.py
│   │   ├── utils/            # Утилиты
│   │   └── main.py           # Точка входа
│   ├── alembic/              # Миграции БД
│   ├── tests/                # Тесты
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/       # React компоненты
│   │   ├── lib/              # Утилиты, API клиент
│   │   └── types/            # TypeScript типы
│   ├── Dockerfile
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔍 Модули проверок

| Модуль | Кол-во проверок | Описание |
|---|---|---|
| Security Headers | 10 | HSTS, CSP, X-Frame-Options, и др. |
| SSL/TLS | 8 | Протоколы, шифры, сертификаты |
| XSS | 5 | Reflected, Stored, DOM-based, CSP bypass |
| Injection | 7 | SQLi, NoSQLi, Command, LDAP, XXE, SSTI |
| CSRF/CORS | 4 | CSRF-токены, SameSite, CORS misconfig |
| SSRF/XXE/Traversal | 5 | SSRF, Blind SSRF, XXE, Path Traversal |
| Auth & Sessions | 7 | Cookies, JWT, MFA, Brute-force |
| Server Config | 6 | Directory listing, Debug endpoints |
| SCA | 5 | Уязвимые зависимости, CMS detection |
| Info Leakage | 8 | .git, .env, API keys, backup files |
| App Logic | 5 | IDOR, Rate limits, Privilege escalation |
| Network | 6 | DNS, CDN/WAF, Subdomains, IPv6 |

## 📖 API документация

После запуска документация доступна по адресу:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚢 Развёртывание

### Development

```bash
docker-compose up -d
```

### Production

См. [DEPLOYMENT.md](./docs/DEPLOYMENT.md) для инструкций по развёртыванию в Kubernetes.

## ⚖️ Лицензия

MIT License. См. [LICENSE](LICENSE) файл.

## ⚠️ Дисклеймер

Данная платформа предназначена **исключительно** для легального тестирования безопасности с письменного согласия владельцев ресурсов. Использование без разрешения является нарушением закона.
