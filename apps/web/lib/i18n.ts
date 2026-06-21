export const languages = [
  { code: "en", label: "ENG", name: "English" },
  { code: "ru", label: "RUS", name: "Русский" },
  { code: "de", label: "DEU", name: "Deutsch" },
  { code: "zh", label: "中文", name: "中文" }
] as const;

export type LanguageCode = (typeof languages)[number]["code"];

export const defaultLanguage: LanguageCode = "en";
export const languageStorageKey = "deckpilot-language";

export const messages = {
  en: {
    nav: {
      dashboard: "Dashboard",
      accounts: "Accounts",
      sessions: "Sessions",
      games: "Games",
      billing: "Billing",
      logs: "Logs",
      support: "Support",
      admin: "Admin",
      settings: "Settings"
    },
    shell: {
      command: "Command",
      logout: "Logout",
      signedOut: "Signed out",
      language: "Language",
      lightTheme: "Light",
      darkTheme: "Dark",
      fullDarkTheme: "Full dark"
    },
    landing: {
      eyebrow: "Modern Steam workspace",
      headline: "Manage your owned Steam accounts from one clean console.",
      body: "DeckPilot brings account status, selected games, transparent demo sessions, billing, and admin oversight into a fast SaaS dashboard.",
      primaryCta: "Open dashboard",
      secondaryCta: "Create account",
      demoCta: "View pricing",
      metrics: ["Guided setup", "Visible status", "Plan limits", "Audit trail"],
      offerTitle: "Built for daily operations",
      offerBody: "Less table chaos, more signal: account status, session health, billing state, and recent actions stay visible at a glance.",
      features: [
        "Encrypted account vault",
        "Session timeline and logs",
        "Game picker with search",
        "Plan limits and billing",
        "Admin control center",
        "Responsive dashboard"
      ],
      pricingTitle: "Start small, scale when needed",
      pricingBody: "Trial for demos, Starter for personal use, Pro and Ultra for larger workspaces."
    },
    auth: {
      loginEyebrow: "Welcome back",
      registerEyebrow: "Create workspace",
      loginHeadline: "Sign in to DeckPilot.",
      registerHeadline: "Set up your account console.",
      loginBody: "Return to your dashboard for accounts, sessions, billing, settings, and activity history.",
      registerBody: "Create secure access and start with a guided dashboard built for accounts you own.",
      noAccount: "No account yet? Create access",
      hasAccount: "Already have an account? Sign in",
      formLoginTitle: "Sign in",
      formRegisterTitle: "Create account",
      formLoginHelp: "Use your local account credentials.",
      formRegisterHelp: "Choose a username, optional email, and a strong password.",
      username: "Username",
      password: "Password",
      submitLogin: "Sign in",
      submitRegister: "Create account",
      registerNotice: "Only add accounts you own. Sensitive data stays encrypted and important actions are logged."
    },
    settings: {
      title: "Settings",
      body: "Tune language, appearance, account recovery, active sessions, data export, and deletion controls.",
      theme: "Theme",
      language: "Language"
    }
  },
  ru: {
    nav: {
      dashboard: "Дашборд",
      accounts: "Аккаунты",
      sessions: "Сессии",
      games: "Игры",
      billing: "Оплата",
      logs: "Журнал",
      support: "Поддержка",
      admin: "Админ-панель",
      settings: "Настройки"
    },
    shell: {
      command: "Команды",
      logout: "Выйти",
      signedOut: "Вы вышли",
      language: "Язык",
      lightTheme: "Светлая",
      darkTheme: "Темная",
      fullDarkTheme: "Полная темная"
    },
    landing: {
      eyebrow: "Современная Steam-консоль",
      headline: "Управляйте личными Steam-аккаунтами из одной аккуратной панели.",
      body: "DeckPilot объединяет статусы аккаунтов, выбранные игры, прозрачные демо-сессии, оплату и админ-контроль в быстрый SaaS-дашборд.",
      primaryCta: "Открыть дашборд",
      secondaryCta: "Создать аккаунт",
      demoCta: "Посмотреть тарифы",
      metrics: ["Быстрый старт", "Понятные статусы", "Лимиты тарифа", "Журнал действий"],
      offerTitle: "Сделано для ежедневной работы",
      offerBody: "Меньше хаоса в таблицах, больше сигнала: статус аккаунтов, здоровье сессий, подписка и последние действия видны сразу.",
      features: [
        "Зашифрованное хранилище",
        "Таймлайн сессий и логи",
        "Выбор игр с поиском",
        "Лимиты тарифов и оплата",
        "Админ-панель",
        "Адаптивный дашборд"
      ],
      pricingTitle: "Начните компактно, расширяйтесь по мере роста",
      pricingBody: "Trial для демо, Starter для личного использования, Pro и Ultra для больших рабочих пространств."
    },
    auth: {
      loginEyebrow: "С возвращением",
      registerEyebrow: "Новое пространство",
      loginHeadline: "Войдите в DeckPilot.",
      registerHeadline: "Создайте рабочую консоль.",
      loginBody: "Вернитесь в дашборд аккаунтов, сессий, оплаты, настроек и истории действий.",
      registerBody: "Создайте безопасный доступ и начните с понятной панели для аккаунтов, которыми владеете.",
      noAccount: "Нет аккаунта? Создать доступ",
      hasAccount: "Уже есть аккаунт? Войти",
      formLoginTitle: "Вход",
      formRegisterTitle: "Регистрация",
      formLoginHelp: "Используйте локальные учетные данные.",
      formRegisterHelp: "Выберите логин, добавьте email при желании и задайте сильный пароль.",
      username: "Логин",
      password: "Пароль",
      submitLogin: "Войти",
      submitRegister: "Создать аккаунт",
      registerNotice: "Добавляйте только аккаунты, которыми владеете. Чувствительные данные шифруются, важные действия пишутся в журнал."
    },
    settings: {
      title: "Настройки",
      body: "Настройте язык, тему, восстановление доступа, активные сессии, экспорт и удаление данных.",
      theme: "Тема",
      language: "Язык"
    }
  },
  de: {
    nav: {
      dashboard: "Dashboard",
      accounts: "Konten",
      sessions: "Sitzungen",
      games: "Spiele",
      billing: "Abrechnung",
      logs: "Protokoll",
      support: "Support",
      admin: "Admin",
      settings: "Einstellungen"
    },
    shell: {
      command: "Befehle",
      logout: "Abmelden",
      signedOut: "Abgemeldet",
      language: "Sprache",
      lightTheme: "Hell",
      darkTheme: "Dunkel",
      fullDarkTheme: "Voll dunkel"
    },
    landing: {
      eyebrow: "Moderner Steam-Arbeitsbereich",
      headline: "Verwalte eigene Steam-Konten über eine klare Konsole.",
      body: "DeckPilot bündelt Kontostatus, ausgewählte Spiele, transparente Demo-Sitzungen, Abrechnung und Admin-Übersicht in einem schnellen SaaS-Dashboard.",
      primaryCta: "Dashboard öffnen",
      secondaryCta: "Konto erstellen",
      demoCta: "Preise ansehen",
      metrics: ["Geführtes Setup", "Klare Status", "Planlimits", "Audit-Trail"],
      offerTitle: "Für tägliche Abläufe gebaut",
      offerBody: "Weniger Tabellenchaos, mehr Überblick: Kontostatus, Sitzungszustand, Abo und letzte Aktionen sind sofort sichtbar.",
      features: [
        "Verschlüsselter Konto-Tresor",
        "Sitzungs-Timeline und Logs",
        "Spielauswahl mit Suche",
        "Planlimits und Abrechnung",
        "Admin-Konsole",
        "Responsives Dashboard"
      ],
      pricingTitle: "Klein starten, später skalieren",
      pricingBody: "Trial für Demos, Starter für persönliche Nutzung, Pro und Ultra für größere Workspaces."
    },
    auth: {
      loginEyebrow: "Willkommen zurück",
      registerEyebrow: "Workspace erstellen",
      loginHeadline: "Bei DeckPilot anmelden.",
      registerHeadline: "Deine Kontokonsole einrichten.",
      loginBody: "Zurück zu Konten, Sitzungen, Abrechnung, Einstellungen und Aktivitätsverlauf.",
      registerBody: "Sicheren Zugriff erstellen und mit einem klaren Dashboard für eigene Konten starten.",
      noAccount: "Noch kein Konto? Zugriff erstellen",
      hasAccount: "Schon ein Konto? Anmelden",
      formLoginTitle: "Anmelden",
      formRegisterTitle: "Konto erstellen",
      formLoginHelp: "Lokale Zugangsdaten verwenden.",
      formRegisterHelp: "Benutzername, optionale E-Mail und starkes Passwort wählen.",
      username: "Benutzername",
      password: "Passwort",
      submitLogin: "Anmelden",
      submitRegister: "Konto erstellen",
      registerNotice: "Nur eigene Konten hinzufügen. Sensible Daten bleiben verschlüsselt und wichtige Aktionen werden protokolliert."
    },
    settings: {
      title: "Einstellungen",
      body: "Sprache, Darstellung, Wiederherstellung, aktive Sitzungen, Export und Löschung verwalten.",
      theme: "Theme",
      language: "Sprache"
    }
  },
  zh: {
    nav: {
      dashboard: "仪表盘",
      accounts: "账号",
      sessions: "会话",
      games: "游戏",
      billing: "订阅",
      logs: "日志",
      support: "支持",
      admin: "管理",
      settings: "设置"
    },
    shell: {
      command: "命令",
      logout: "退出",
      signedOut: "已退出",
      language: "语言",
      lightTheme: "浅色",
      darkTheme: "深色",
      fullDarkTheme: "全黑"
    },
    landing: {
      eyebrow: "现代 Steam 工作台",
      headline: "用一个清晰的控制台管理你拥有的 Steam 账号。",
      body: "DeckPilot 将账号状态、已选游戏、透明演示会话、订阅和管理审计集中到一个快速 SaaS 仪表盘。",
      primaryCta: "打开仪表盘",
      secondaryCta: "创建账号",
      demoCta: "查看价格",
      metrics: ["引导设置", "清晰状态", "套餐限制", "审计记录"],
      offerTitle: "为日常运营而设计",
      offerBody: "减少表格混乱，突出关键信号：账号状态、会话健康、订阅状态和最近操作一目了然。",
      features: [
        "加密账号库",
        "会话时间线和日志",
        "带搜索的游戏选择器",
        "套餐限制和订阅",
        "管理控制中心",
        "响应式仪表盘"
      ],
      pricingTitle: "从小规模开始，按需扩展",
      pricingBody: "Trial 适合演示，Starter 适合个人使用，Pro 和 Ultra 适合更大的工作空间。"
    },
    auth: {
      loginEyebrow: "欢迎回来",
      registerEyebrow: "创建工作区",
      loginHeadline: "登录 DeckPilot。",
      registerHeadline: "设置你的账号控制台。",
      loginBody: "返回账号、会话、订阅、设置和活动历史。",
      registerBody: "创建安全访问，并从适合自有账号的清晰仪表盘开始。",
      noAccount: "还没有账号？创建访问",
      hasAccount: "已有账号？登录",
      formLoginTitle: "登录",
      formRegisterTitle: "创建账号",
      formLoginHelp: "使用本地账号凭据。",
      formRegisterHelp: "选择用户名、可选邮箱和强密码。",
      username: "用户名",
      password: "密码",
      submitLogin: "登录",
      submitRegister: "创建账号",
      registerNotice: "只添加你拥有的账号。敏感数据会被加密，重要操作会写入日志。"
    },
    settings: {
      title: "设置",
      body: "调整语言、主题、账号恢复、活动会话、数据导出和删除控制。",
      theme: "主题",
      language: "语言"
    }
  }
};

export function getInitialLanguage(value: string | null | undefined): LanguageCode {
  if (value === "ru" || value === "en" || value === "de" || value === "zh") return value;
  return defaultLanguage;
}
