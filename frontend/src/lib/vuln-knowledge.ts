/**
 * База знаний по типам уязвимостей.
 * Содержит описания, риски, рекомендации и ссылки на стандарты
 * для каждого типа проблем безопасности.
 */

export interface VulnKnowledge {
  /** Ключ: module или module + title pattern */
  key: string;
  /** Название уязвимости */
  name: string;
  /** Подробное описание — что это и чем опасно */
  description: string;
  /** Как эксплуатируется (атакующий может...) */
  exploitation: string;
  /** Как исправить (подробная рекомендация) */
  remediation: string;
  /** Пример безопасной конфигурации/кода */
  example?: string;
  /** Полезные ссылки */
  links: { label: string; url: string }[];
}

/**
 * Получить запись из базы знаний по module и title.
 * Ищет по точному совпадению module, затем по подстроке title.
 */
export function getVulnKnowledge(module: string, title?: string): VulnKnowledge | null {
  // Сначала ищем по точному совпадению module
  const byModule = knowledgeBase.find((k) => k.key === module);
  if (byModule && !title) return byModule;

  // Если есть title — ищем более специфичную запись
  if (title) {
    const byTitle = knowledgeBase.find((k) => {
      if (k.key.startsWith(`${module}:`)) {
        const pattern = k.key.split(':')[1].toLowerCase();
        return title.toLowerCase().includes(pattern);
      }
      return false;
    });
    if (byTitle) return byTitle;
  }

  return byModule || null;
}

export const knowledgeBase: VulnKnowledge[] = [
  // ===================== SECURITY HEADERS =====================
  {
    key: "security_headers",
    name: "Некорректные HTTP Security Headers",
    description:
      "HTTP-заголовки безопасности instruct браузер о том, как обрабатывать контент, " +
      "какие ресурсы разрешать загружать и как защищаться от атак вроде XSS, кликджекинга " +
      "и MIME-sniffing. Отсутствие или неправильная настройка этих заголовков снижает " +
      "уровень защиты на стороне клиента.",
    exploitation:
      "Злоумышленник может провести XSS-атаку, кликджекинг, MIME-sniffing атаки, " +
      "так как браузер не получает инструкций о блокировке опасного поведения.",
    remediation:
      "Настройте все security headers на уровне веб-сервера (Nginx, Apache) или в коде приложения. " +
      "Минимальный набор: HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy.",
    example: `Nginx конфигурация:
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;`,
    links: [
      { label: "OWASP Secure Headers Project", url: "https://owasp.org/www-project-secure-headers/" },
      { label: "MDN HTTP Security Headers", url: "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security" },
    ],
  },

  // ===================== SSL/TLS =====================
  {
    key: "ssl_tls",
    name: "Проблемы SSL/TLS конфигурации",
    description:
      "SSL/TLS обеспечивает шифрование данных между клиентом и сервером. " +
      "Проблемы в SSL-сертификатах (истёкший, самоподписанный, отсутствие) или " +
      "слабая TLS-конфигурация позволяют перехватывать трафик через MITM-атаки.",
    exploitation:
      "Атакующий в позиции «man-in-the-middle» может перехватывать и читать трафик, " +
      "подменять ответы сервера, красть сессии и конфиденциальные данные.",
    remediation:
      "Используйте бесплатные сертификаты Let's Encrypt с автоматическим продлением. " +
      "Настройте TLS 1.2+ с современными cipher suites. Перенаправляйте весь HTTP на HTTPS.",
    example: `Nginx TLS конфигурация:
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;`,
    links: [
      { label: "Mozilla SSL Configuration Generator", url: "https://ssl-config.mozilla.org/" },
      { label: "SSL Labs Test", url: "https://www.ssllabs.com/ssltest/" },
      { label: "OWASP TLS Cheat Sheet", url: "https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html" },
    ],
  },

  // ===================== XSS =====================
  {
    key: "xss",
    name: "Cross-Site Scripting (XSS)",
    description:
      "XSS позволяет внедрить вредоносный JavaScript в страницу, которую просматривает " +
      "другой пользователь. Существует три типа: Reflected (отражённый), Stored (хранимый) " +
      "и DOM-based (на стороне клиента). XSS — одна из самых распространённых веб-уязвимостей.",
    exploitation:
      "Атакующий может: украсть cookies и сессии, выполнить действия от имени пользователя, " +
      "перенаправить на фишинговый сайт, запустить кейлоггер, изменить содержимое страницы.",
    remediation:
      "Экранируйте выводимые данные (HTML entity encoding), используйте Content-Security-Policy, " +
      "санитизируйте HTML (например, через DOMPurify), избегайте innerHTML/eval(). " +
      "В современных фреймворках (React, Vue) используйте встроенное экранирование.",
    example: `// ❌ Опасно:
element.innerHTML = userInput;

// ✅ Безопасно:
element.textContent = userInput;
// Или через фреймворк:
<div>{userInput}</div>  // React автоматически экранирует`,
    links: [
      { label: "OWASP XSS Prevention Cheat Sheet", url: "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html" },
      { label: "DOMPurify", url: "https://github.com/cure53/DOMPurify" },
      { label: "PortSwigger XSS Cheat Sheet", url: "https://portswigger.net/web-security/cross-site-scripting/cheat-sheet" },
    ],
  },

  // ===================== INJECTION =====================
  {
    key: "injection",
    name: "Инъекции (SQLi, NoSQLi, Command Injection, SSTI)",
    description:
      "Инъекции возникают, когда недоверенные данные передааются интерпретатору без " +
      "должной валидации и санитизации. Включает SQL-инъекции, NoSQL-инъекции, " +
      "инъекции ОС-команд, Server-Side Template Injection (SSTI) и другие.",
    exploitation:
      "SQLi: чтение/изменение/удаление данных в БД, обход аутентификации. " +
      "Command Injection: выполнение произвольных команд на сервере. " +
      "SSTI: выполнение произвольного кода на сервере через шаблонизатор.",
    remediation:
      "SQLi: используйте параметризованные запросы (prepared statements) или ORM. " +
      "Command Injection: избегайте системных вызовов, используйте whitelist валидацию. " +
      "SSTI: не рендерите пользовательский ввод как код шаблона. " +
      "NoSQLi: валидируйте типы, избегайте прямой передачи объектов.",
    example: `# ❌ SQL-инъекция (Python):
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ Параметризованный запрос:
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ Command Injection:
os.system(f"ping {user_input}")

# ✅ Безопасно:
subprocess.run(["ping", "-c", "1", user_input], check=True)`,
    links: [
      { label: "OWASP Injection Prevention Cheat Sheet", url: "https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html" },
      { label: "OWASP SQL Injection", url: "https://owasp.org/www-community/attacks/SQL_Injection" },
    ],
  },

  // ===================== CSRF/CORS =====================
  {
    key: "csrf_cors",
    name: "CSRF и CORS проблемы",
    description:
      "CSRF (Cross-Site Request Forgery) позволяет выполнить запрос от имени авторизованного " +
      "пользователя без его ведома. CORS (Cross-Origin Resource Sharing) misconfiguration " +
      "позволяет другим доменам читать данные вашего API.",
    exploitation:
      "CSRF: атакующий может заставить пользователя выполнить действие (перевод денег, смена пароля) " +
      "через поддельный запрос. CORS wildcard (*) позволяет любому сайту читать данные API.",
    remediation:
      "CSRF: используйте CSRF-токены, SameSite=Strict/Lax для cookies. " +
      "CORS: укажите конкретные разрешённые origins, избегайте wildcard (*). " +
      "Для API с авторизацией всегда используйте withCredentials и конкретный origin.",
    example: `// CORS настройка (FastAPI):
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Не "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)`,
    links: [
      { label: "OWASP CSRF Prevention", url: "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html" },
      { label: "MDN CORS", url: "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS" },
    ],
  },

  // ===================== SSRF/XXE/TRAVERSAL =====================
  {
    key: "ssrf_xxe_traversal",
    name: "SSRF, XXE и Path Traversal",
    description:
      "SSRF (Server-Side Request Forgery) позволяет атакующему заставить сервер " +
      "выполнить запрос к внутренним ресурсам. XXE (XML External Entity) позволяет " +
      "читать файлы сервера через XML-парсер. Path Traversal — доступ к файлам " +
      "за пределы разрешённой директории через ../",
    exploitation:
      "SSRF: доступ к внутренним сервисам (metadata AWS, Redis, MySQL). " +
      "XXE: чтение /etc/passwd, SSRF через external entities. " +
      "Path Traversal: чтение произвольных файлов (конфиги, ключи, базы данных).",
    remediation:
      "SSRF: whitelist разрешённых доменов/IP, блокируйте внутренние IP-диапазоны. " +
      "XXE: отключите external entities в XML-парсере. " +
      "Path Traversal: используйте whitelist, нормализуйте пути, не подставляйте " +
      "пользовательский ввод в файловые пути.",
    example: `# ✅ Безопасное чтение файла:
import os
BASE_DIR = "/var/app/uploads"
filename = os.path.basename(user_input)  # Убираем все пути
filepath = os.path.join(BASE_DIR, filename)
if not os.path.realpath(filepath).startswith(os.path.realpath(BASE_DIR)):
    raise ValueError("Access denied")`,
    links: [
      { label: "OWASP SSRF Prevention", url: "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html" },
      { label: "OWASP XXE Prevention", url: "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html" },
    ],
  },

  // ===================== AUTH & SESSIONS =====================
  {
    key: "auth_sessions",
    name: "Проблемы аутентификации и сессий",
    description:
      "Небезопасная конфигурация аутентификации и управления сессиями позволяет " +
      "злоумышленнику перехватить сессию, подобрать пароль или обойти проверку прав. " +
      "Включает проблемы с cookie-флагами, JWT, brute-force защитой.",
    exploitation:
      "Перехват сессии через отсутствие Secure/HttpOnly, подбор пароля без rate limiting, " +
      "подделка JWT с алгоритмом 'none', фиксация сессии.",
    remediation:
      "Установите флаги Secure, HttpOnly, SameSite для cookies. " +
      "Используйте стойкие JWT-секреты (HS256+), не допускайте 'none' алгоритм. " +
      "Реализуйте rate limiting на логин, блокировку после нескольких неудачных попыток.",
    example: `// ✅ Безопасные cookie:
Set-Cookie: session_id=xyz; Secure; HttpOnly; SameSite=Strict; Path=/

// ✅ JWT с проверкой алгоритма:
jwt.decode(token, secret, algorithms=["HS256"])  # Только HS256, не допускаем "none"`,
    links: [
      { label: "OWASP Authentication Cheat Sheet", url: "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html" },
      { label: "OWASP Session Management", url: "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html" },
    ],
  },

  // ===================== SERVER CONFIG =====================
  {
    key: "server_config",
    name: "Небезопасная конфигурация сервера",
    description:
      "Сервер настроен с отключёнными мерами безопасности: раскрытие версии ПО, " +
      "доступные debug-эндпоинты, включённый directory listing, разрешённые опасные " +
      "HTTP-методы. Это даёт атакующему информацию для дальнейшей атаки.",
    exploitation:
      "Зная версию сервера, атакующий ищет специфичные CVE. Debug-эндпоинты могут " +
      "раскрыть внутреннее состояние, переменные окружения, ключи. Directory listing " +
      "позволяет enumerировать файлы.",
    remediation:
      "Скройте Server и X-Powered-By заголовки. Отключите directory listing. " +
      "Удалите debug-эндпоинты из production. Разрешите только GET/POST/HEAD методы.",
    example: `Nginx — скрыть версию:
server_tokens off;

Apache — отключить listing:
Options -Indexes`,
    links: [
      { label: "OWASP Web Server Security", url: "https://owasp.org/www-project-web-security-testing-guide/" },
    ],
  },

  // ===================== SCA =====================
  {
    key: "sca",
    name: "Уязвимые зависимости (SCA)",
    description:
      "Software Composition Analysis выявляет использование библиотек и фреймворков " +
      "с известными уязвимостями (CVE). Устаревшие версии популярных библиотек (jQuery, " +
      "React, OpenSSL и др.) часто содержат публичные эксплойты.",
    exploitation:
      "Атакующий использует публичный эксплойт для известной CVE в вашей библиотеке. " +
      "Например, jQuery 3.4.1 имеет XSS-уязвимость, Log4j — RCE.",
    remediation:
      "Регулярно обновляйте зависимости. Используйте Dependabot/Renovate для авто-обновлений. " +
      "Мониторьте NVD и advisories. Используйте SCA-инструменты (Snyk, Dependabot).",
    example: `# GitHub Dependabot (.github/dependabot.yml):
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"`,
    links: [
      { label: "NVD — National Vulnerability Database", url: "https://nvd.nist.gov/" },
      { label: "OWASP Dependency Check", url: "https://owasp.org/www-project-dependency-check/" },
    ],
  },

  // ===================== INFO LEAKAGE =====================
  {
    key: "info_leakage",
    name: "Утечка информации",
    description:
      "Публичный доступ к файлам, которые не должны быть доступны: .git, .env, " +
      "backup-файлы, API-ключи в коде, метаданные файлов, конфигурации облачных хранилищ. " +
      "Эта информация используется для дальнейших атак.",
    exploitation:
      ".git — полный исходный код. .env — пароли БД, API-ключи. " +
      "API-ключи в JS — несанкционированный доступ к сервисам. " +
      "Backup-файлы — дампы БД, старая логика с уязвимостями.",
    remediation:
      "Добавьте чувствительные файлы в .gitignore. Настройте блокировку доступа к " +
      "скрытым файлам на веб-сервере. Не храните секреты в клиентском коде. " +
      "Регулярно сканируйте репозиторий на утечки (git-secrets, truffleHog).",
    example: `# Nginx — блокировка скрытых файлов:
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

# .gitignore:
.env
*.bak
*.sql
*.key
config.php`,
    links: [
      { label: "OWASP Information Leakage", url: "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/" },
    ],
  },

  // ===================== APP LOGIC =====================
  {
    key: "app_logic",
    name: "Уязвимости бизнес-логики",
    description:
      "Уязвимости в бизнес-логике приложения — ошибки в проектировании, которые позволяют " +
      "обходить бизнес-правила: IDOR (доступ к чужим объектам), эскалация привилегий, " +
      "обход rate limiting, манипуляции с пагинацией.",
    exploitation:
      "IDOR: изменить ID в URL и получить чужие данные. " +
      "Эскалация: изменить роль в запросе. " +
      "Обход лимитов: манипуляция параметрами для неограниченного доступа.",
    remediation:
      "Всегда проверяйте права доступа на сервере (не только в UI). " +
      "Используйте авторизацию на уровне объектов (owns resource?). " +
      "Реализуйте серверный rate limiting. Валидируйте все параметры.",
    example: `# ✅ Проверка владения ресурсом (Python):
async def get_order(order_id: str, current_user: User, db: AsyncSession):
    order = await db.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return order`,
    links: [
      { label: "OWASP Insecure Direct Object Reference", url: "https://owasp.org/www-community/vulnerabilities/Insecure_Direct_Object_Reference" },
      { label: "OWASP Authorization Cheat Sheet", url: "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html" },
    ],
  },

  // ===================== NETWORK =====================
  {
    key: "network",
    name: "Сетевые и инфраструктурные проблемы",
    description:
      "Проблемы в сетевой конфигурации инфраструктуры: отсутствие SPF/DKIM/DMARC, " +
      "открытые нестандартные порты, отсутствие WAF, DNS-мисконфигурация. " +
      "Эти проблемы могут привести к спуфингу email, прямому доступу к сервисам.",
    exploitation:
      "Отсутствие SPF/DKIM/DMARC позволяет отправлять email от имени домена. " +
      "Открытые порты — прямой доступ к сервисам (Redis, MongoDB, Elasticsearch).",
    remediation:
      "Настройте SPF, DKIM, DMARC DNS-записи. Закройте все ненужные порты. " +
      "Используйте WAF. Настройте мониторинг открытых портов.",
    example: `DNS записи для email:
TXT @ "v=spf1 include:_spf.google.com ~all"
TXT _dmarc "v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com"
TXT google "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4..."`,
    links: [
      { label: "MXToolbox — DNS Check", url: "https://mxtoolbox.com/" },
      { label: "OWASP DNS Security", url: "https://cheatsheetseries.owasp.org/cheatsheets/DNS_Security_Cheat_Sheet.html" },
    ],
  },
];
