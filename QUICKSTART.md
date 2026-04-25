# SafeScan — Быстрый старт

## Предварительные требования

- **Docker Desktop** (https://www.docker.com/products/docker-desktop/) — для Windows
- **Git** (опционально)

## Запуск (3 команды)

### 1. Запустить все сервисы

```powershell
docker compose up -d
```

Это запустит:
- **PostgreSQL** — база данных
- **Redis** — очередь задач и кэш
- **MinIO** — хранилище отчётов
- **Mailhog** — тестовый email сервер
- **Backend API** — FastAPI (порт 8000)
- **Celery Worker** — сканирующие воркеры
- **Celery Beat** — периодические задачи
- **Flower** — мониторинг воркеров (порт 5555)
- **Frontend** — Next.js (порт 3000)

### 2. Дождаться готовности (30-60 секунд)

Проверить что backend готов:
```powershell
curl http://localhost:8000/health
```

Должен вернуться `{"status":"healthy","service":"safescan-api"}`

### 3. Открыть приложение

| Сервис | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Flower (воркеры)** | http://localhost:5555 |
| **Mailhog (email)** | http://localhost:8025 |
| **MinIO Console** | http://localhost:9001 |

## Первый вход

1. Откройте http://localhost:3000
2. Нажмите **"Зарегистрироваться"**
3. Создайте аккаунт (email автоматически верифицируется в dev-режиме)
4. Добавьте домен → верифицируйте → запустите скан

## Остановка

```powershell
docker compose down
```

## Остановка с удалением данных

```powershell
docker compose down -v
```

## Частые проблемы

### Порт 8000 или 3000 уже занят
Освободите порты или измените маппинг в `docker-compose.yml`.

### Backend не запускается
```powershell
docker compose logs backend
```

### Frontend не запускается
```powershell
docker compose logs frontend
```

### Воркеры не работают
```powershell
docker compose logs celery-worker
```

### Пересобрать контейнеры
```powershell
docker compose build --no-cache
docker compose up -d
```
