# === BUILD STAGE ===
FROM node:20-slim AS builder

WORKDIR /app

# 👇 ДОБАВИТЬ: Объявляем аргумент сборки
ARG NEXT_PUBLIC_API_URL
# 👇 ДОБАВИТЬ: Делаем его доступным для Next.js во время build
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

COPY package*.json ./
RUN npm ci && find node_modules/.bin -type f -exec chmod +x {} \;

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# 👇 Теперь next build увидит переменную
RUN node node_modules/next/dist/bin/next build

# === PRODUCTION STAGE ===
FROM node:20-slim AS production

WORKDIR /app

# Создаём пользователя
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Копируем standalone-сервер
COPY --from=builder --chown=nextjs:nodejs /app/package*.json ./
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/next.config.js ./

EXPOSE 3000
USER nextjs

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]