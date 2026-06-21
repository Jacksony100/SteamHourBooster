(function () {
  const SHB = (window.SHB = window.SHB || {});
  const dictionary = {
    ru: {
      lang_label: "Русский",
      theme_dark: "Тёмная",
      theme_light: "Светлая",
      start: "Запустить",
      stop: "Остановить",
      login: "Войти",
      logout: "Выйти",
      games: "Игры",
      bans: "Проверка",
      delete: "Удалить",
      selected_games: "Выбранные игры",
      empty_games: "Игры не выбраны",
      status_online: "Онлайн",
      status_offline: "Офлайн",
      status_farming: "Сессия",
      status_error: "Ошибка",
    },
    en: {
      lang_label: "English",
      theme_dark: "Dark",
      theme_light: "Light",
      start: "Start",
      stop: "Stop",
      login: "Login",
      logout: "Logout",
      games: "Games",
      bans: "Check",
      delete: "Delete",
      selected_games: "Selected games",
      empty_games: "No games selected",
      status_online: "Online",
      status_offline: "Offline",
      status_farming: "Session",
      status_error: "Error",
    },
  };

  SHB.lang = localStorage.getItem("shb.lang") || "ru";
  SHB.t = function t(key) {
    return (dictionary[SHB.lang] && dictionary[SHB.lang][key]) || dictionary.ru[key] || key;
  };

  function applyTranslations() {
    document.documentElement.lang = SHB.lang;
    SHB.qsa("[data-i18n]").forEach((node) => {
      node.textContent = SHB.t(node.dataset.i18n);
    });
    SHB.qsa("[data-i18n-placeholder]").forEach((node) => {
      node.placeholder = SHB.t(node.dataset.i18nPlaceholder);
    });
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("shb.theme", theme);
    SHB.qsa("[data-theme-label]").forEach((node) => {
      node.textContent = theme === "light" ? "Светлая" : "Тёмная";
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(localStorage.getItem("shb.theme") || "dark");
    applyTranslations();

    SHB.qsa("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
        applyTheme(next);
      });
    });

    SHB.qsa("[data-lang-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        SHB.lang = SHB.lang === "ru" ? "en" : "ru";
        localStorage.setItem("shb.lang", SHB.lang);
        applyTranslations();
      });
    });
  });
})();
