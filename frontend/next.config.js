// /opt/safescan/frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

// Проверка: падать с ошибкой, если переменная не задана
if (!process.env.NEXT_PUBLIC_API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is required. Set it in .env or docker-compose.yml",
  );
}

module.exports = nextConfig;
