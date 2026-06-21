(function () {
  const SHB = window.SHB;
  let accounts = [];
  let selectedAccountId = null;
  let gameAccountId = null;
  let steamGuardAccountId = null;
  const farmingSessions = new Set(JSON.parse(localStorage.getItem("shb.sessions") || "[]"));

  function saveSessions() {
    localStorage.setItem("shb.sessions", JSON.stringify(Array.from(farmingSessions)));
  }

  function accountStatus(account) {
    if (farmingSessions.has(account.id)) return "farming";
    return account.status || "offline";
  }

  function statusLabel(status) {
    const map = {
      online: SHB.t("status_online"),
      offline: SHB.t("status_offline"),
      farming: SHB.t("status_farming"),
      error: SHB.t("status_error"),
    };
    return map[status] || status;
  }

  function gamesHTML(account) {
    const games = account.active_games || [];
    if (!games.length) return `<span class="game-pill">${SHB.t("empty_games")}</span>`;
    return games
      .slice(0, 4)
      .map((game) => `<span class="game-pill">${SHB.escapeHTML(game.game_name)}</span>`)
      .join("");
  }

  function renderSkeleton() {
    const root = SHB.qs("#accountsList");
    if (!root) return;
    root.innerHTML = `<div class="skeleton-list"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>`;
  }

  function renderMetrics() {
    const total = accounts.length;
    const online = accounts.filter((account) => account.status === "online").length;
    const active = accounts.filter((account) => farmingSessions.has(account.id)).length;
    const games = accounts.reduce((sum, account) => sum + (account.active_games || []).length, 0);
    const values = { totalAccounts: total, onlineAccounts: online, activeSessions: active, selectedGames: games };
    Object.entries(values).forEach(([id, value]) => {
      const node = SHB.qs(`#${id}`);
      if (node) node.textContent = value;
    });
  }

  function renderAccounts() {
    const root = SHB.qs("#accountsList");
    if (!root) return;
    if (!accounts.length) {
      root.innerHTML = `
        <div class="empty-state">
          <div class="brand-mark" aria-hidden="true">${icon("plus")}</div>
          <h3>Добавьте первый аккаунт</h3>
          <p>Подключайте только собственные аккаунты. Сессии видны, управляемы и могут быть остановлены вручную в любой момент.</p>
        </div>`;
      renderSelected();
      renderSessions();
      renderMetrics();
      return;
    }

    root.innerHTML = accounts
      .map((account) => {
        const status = accountStatus(account);
        const selected = account.id === selectedAccountId ? " selected" : "";
        return `
          <article class="account-card${selected}" data-account-id="${account.id}">
            <div class="account-main">
              <div class="account-title-row">
                <button class="btn btn-ghost btn-icon" data-select-account="${account.id}" aria-label="Открыть аккаунт">${icon("user")}</button>
                <div class="account-name">${SHB.escapeHTML(account.username)}</div>
                <span class="badge ${status}">${statusLabel(status)}</span>
              </div>
              <div class="account-meta">SteamID64: ${SHB.escapeHTML(account.steamid64 || "ожидает входа")}</div>
              <div class="game-list">${gamesHTML(account)}</div>
            </div>
            <div class="actions">
              <button class="btn btn-ghost" data-login-account="${account.id}" aria-label="Войти в Steam">${icon("login")}<span>${SHB.t("login")}</span></button>
              <button class="btn btn-ghost" data-games-account="${account.id}" aria-label="Выбрать игры">${icon("grid")}<span>${SHB.t("games")}</span></button>
              <button class="btn btn-success" data-start-account="${account.id}" aria-label="Запустить сессию">${icon("play")}<span>${SHB.t("start")}</span></button>
              <button class="btn btn-warning" data-stop-account="${account.id}" aria-label="Остановить сессию">${icon("pause")}<span>${SHB.t("stop")}</span></button>
              <button class="btn btn-ghost" data-bans-account="${account.id}" aria-label="Проверить ограничения">${icon("shield")}<span>${SHB.t("bans")}</span></button>
              <button class="btn btn-danger" data-delete-account="${account.id}" aria-label="Удалить аккаунт">${icon("trash")}<span>${SHB.t("delete")}</span></button>
            </div>
          </article>`;
      })
      .join("");
    bindAccountActions();
    renderSelected();
    renderSessions();
    renderMetrics();
  }

  function renderSelected() {
    const panel = SHB.qs("#selectedAccountPanel");
    if (!panel) return;
    const account = accounts.find((item) => item.id === selectedAccountId) || accounts[0];
    if (!account) {
      panel.innerHTML = `<div class="empty-state"><h3>Аккаунт не выбран</h3><p>После добавления аккаунта здесь появится статус, список игр и быстрые действия.</p></div>`;
      return;
    }
    selectedAccountId = account.id;
    const status = accountStatus(account);
    panel.innerHTML = `
      <div class="section-head">
        <div>
          <h3>${SHB.escapeHTML(account.username)}</h3>
          <p>Панель выбранного аккаунта</p>
        </div>
        <span class="badge ${status}">${statusLabel(status)}</span>
      </div>
      <div class="ban-grid">
        <div class="ban-metric"><span class="muted">SteamID64</span><strong>${SHB.escapeHTML(account.steamid64 || "не получен")}</strong></div>
        <div class="ban-metric"><span class="muted">Игры</span><strong>${(account.active_games || []).length}</strong></div>
      </div>
      <div class="game-list mt-12">${gamesHTML(account)}</div>`;
  }

  function renderSessions() {
    const root = SHB.qs("#sessionsList");
    if (!root) return;
    const active = accounts.filter((account) => farmingSessions.has(account.id));
    if (!active.length) {
      root.innerHTML = `<div class="empty-state"><h3>Нет активных сессий</h3><p>Запускайте активность только вручную и следите за статусом аккаунта.</p></div>`;
      return;
    }
    root.innerHTML = active
      .map(
        (account) => `
          <div class="session-item">
            <div class="account-title-row">
              <span class="badge farming">Сессия</span>
              <strong>${SHB.escapeHTML(account.username)}</strong>
            </div>
            <div class="activity-meta">${(account.active_games || []).length} игр выбрано</div>
          </div>`
      )
      .join("");
  }

  function renderActivity() {
    const root = SHB.qs("#activityList");
    if (!root) return;
    const items = SHB.getActivity();
    if (!items.length) {
      root.innerHTML = `<div class="empty-state"><h3>Журнал пуст</h3><p>Действия с аккаунтами будут появляться здесь.</p></div>`;
      return;
    }
    root.innerHTML = items
      .map((item) => `<div class="activity-item"><div class="activity-title">${SHB.escapeHTML(item.text)}</div><div class="activity-meta">${SHB.escapeHTML(item.meta)}</div></div>`)
      .join("");
  }

  async function fetchAccounts() {
    renderSkeleton();
    try {
      accounts = await SHB.api("/get_accounts");
      if (!selectedAccountId && accounts[0]) selectedAccountId = accounts[0].id;
      renderAccounts();
    } catch (error) {
      SHB.qs("#accountsList").innerHTML = `<div class="empty-state"><h3>Не удалось загрузить аккаунты</h3><p>${SHB.escapeHTML(error.message)}</p></div>`;
    }
  }

  function bindAccountActions() {
    SHB.qsa("[data-select-account]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedAccountId = Number(button.dataset.selectAccount);
        renderAccounts();
      });
    });
    SHB.qsa("[data-login-account]").forEach((button) => button.addEventListener("click", () => loginAccount(Number(button.dataset.loginAccount))));
    SHB.qsa("[data-games-account]").forEach((button) => button.addEventListener("click", () => openGames(Number(button.dataset.gamesAccount))));
    SHB.qsa("[data-start-account]").forEach((button) => button.addEventListener("click", () => startSession(Number(button.dataset.startAccount))));
    SHB.qsa("[data-stop-account]").forEach((button) => button.addEventListener("click", () => stopSession(Number(button.dataset.stopAccount))));
    SHB.qsa("[data-bans-account]").forEach((button) => button.addEventListener("click", () => checkBans(Number(button.dataset.bansAccount))));
    SHB.qsa("[data-delete-account]").forEach((button) => button.addEventListener("click", () => deleteAccount(Number(button.dataset.deleteAccount))));
  }

  async function addAccount(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const restore = SHB.setButtonLoading(form.querySelector("button[type='submit']"), "Добавляем");
    try {
      const payload = {
        username: SHB.qs("#username").value.trim(),
        password: SHB.qs("#password").value,
      };
      const data = await SHB.api("/add_account", { method: "POST", body: JSON.stringify(payload) });
      if (!data.success) throw new Error(data.error || "Аккаунт не добавлен");
      SHB.toast("Аккаунт добавлен и готов к входу", "Аккаунт");
      SHB.addActivity(`Добавлен аккаунт ${payload.username}`);
      form.reset();
      await fetchAccounts();
    } finally {
      restore();
    }
  }

  async function loginAccount(accountId, steamGuardCode = null) {
    const payload = { id: accountId };
    if (steamGuardCode) payload.steam_guard_code = steamGuardCode;
    const data = await SHB.api("/login_account", { method: "POST", body: JSON.stringify(payload) });
    if (data.success) {
      SHB.toast("Steam-сессия подключена", "Вход выполнен");
      SHB.addActivity("Steam-сессия подключена");
      await fetchAccounts();
      return;
    }
    if (data.need_steam_guard) {
      steamGuardAccountId = accountId;
      SHB.openModal("steamGuardModal");
      return;
    }
    throw new Error(data.error || "Не удалось войти");
  }

  async function deleteAccount(accountId) {
    const account = accounts.find((item) => item.id === accountId);
    const ok = await SHB.confirm({
      title: "Удалить аккаунт?",
      message: `Аккаунт ${account ? account.username : accountId} будет отключён от панели. Это действие нельзя отменить.`,
      confirmText: "Удалить",
      danger: true,
    });
    if (!ok) return;
    const data = await SHB.api("/delete_account", { method: "POST", body: JSON.stringify({ id: accountId }) });
    if (!data.success) throw new Error(data.error || "Аккаунт не удалён");
    farmingSessions.delete(accountId);
    saveSessions();
    SHB.toast("Аккаунт удалён", "Готово");
    SHB.addActivity("Аккаунт удалён");
    await fetchAccounts();
  }

  async function startSession(accountId) {
    const data = await SHB.api("/start_farming", { method: "POST", body: JSON.stringify({ account_id: accountId }) });
    if (!data.success) throw new Error(data.error || "Сессия не запущена");
    farmingSessions.add(accountId);
    saveSessions();
    SHB.toast("Сессия активности запущена", "Активность");
    SHB.addActivity("Запущена сессия активности");
    renderAccounts();
  }

  async function stopSession(accountId) {
    const data = await SHB.api("/stop_farming", { method: "POST", body: JSON.stringify({ account_id: accountId }) });
    if (!data.success) throw new Error(data.error || "Сессия не остановлена");
    farmingSessions.delete(accountId);
    saveSessions();
    SHB.toast("Сессия остановлена", "Активность");
    SHB.addActivity("Остановлена сессия активности");
    renderAccounts();
  }

  async function openGames(accountId) {
    gameAccountId = accountId;
    const root = SHB.qs("#gamesList");
    root.innerHTML = `<div class="skeleton-list"><div class="skeleton"></div><div class="skeleton"></div></div>`;
    SHB.openModal("gamesModal");
    const data = await SHB.api("/fetch_owned_games", { method: "POST", body: JSON.stringify({ account_id: accountId }) });
    if (!data.success) throw new Error(data.error || "Не удалось загрузить игры");
    renderGames(data.games || []);
  }

  function renderGames(games) {
    const root = SHB.qs("#gamesList");
    const selected = new Set((accounts.find((item) => item.id === gameAccountId)?.active_games || []).map((game) => String(game.game_id)));
    if (!games.length) {
      root.innerHTML = `<div class="empty-state"><h3>Игры не найдены</h3><p>Проверьте вход в Steam и доступность библиотеки.</p></div>`;
      return;
    }
    root.innerHTML = games
      .map(
        (game) => `
          <label class="game-option" data-game-name="${SHB.escapeHTML(game.name).toLowerCase()}">
            <input type="checkbox" value="${SHB.escapeHTML(game.app_id)}" data-game-title="${SHB.escapeHTML(game.name)}" ${selected.has(String(game.app_id)) ? "checked" : ""}>
            <span>${SHB.escapeHTML(game.name)}</span>
          </label>`
      )
      .join("");
  }

  async function saveGames() {
    const selected = SHB.qsa("#gamesList input:checked").map((input) => ({
      app_id: input.value,
      name: input.dataset.gameTitle || `App ${input.value}`,
    }));
    const data = await SHB.api("/update_account_games", {
      method: "POST",
      body: JSON.stringify({ account_id: gameAccountId, games: selected }),
    });
    if (!data.success) throw new Error(data.error || "Игры не сохранены");
    SHB.closeModal("gamesModal");
    SHB.toast(`Сохранено игр: ${data.count}`, "Игры");
    SHB.addActivity(`Обновлён список игр: ${data.count}`);
    await fetchAccounts();
  }

  async function checkBans(accountId) {
    const data = await SHB.api("/ban_info", { method: "POST", body: JSON.stringify({ account_id: accountId }) });
    if (!data.success) throw new Error(data.error || "Не удалось проверить ограничения");
    const bans = data.bans || {};
    const root = SHB.qs("#banStatus");
    root.innerHTML = `
      <div class="ban-grid">
        <div class="ban-metric"><span class="muted">VAC</span><strong>${bans.VACBanned ? "Есть" : "Нет"}</strong></div>
        <div class="ban-metric"><span class="muted">Community</span><strong>${bans.CommunityBanned ? "Есть" : "Нет"}</strong></div>
        <div class="ban-metric"><span class="muted">VAC-банов</span><strong>${bans.NumberOfVACBans ?? 0}</strong></div>
        <div class="ban-metric"><span class="muted">Дней с последнего</span><strong>${bans.DaysSinceLastBan ?? "нет"}</strong></div>
      </div>`;
    SHB.toast("Статус ограничений обновлён", "Проверка");
    SHB.addActivity("Выполнена проверка ограничений");
  }

  function icon(name) {
    const icons = {
      plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
      user: '<svg viewBox="0 0 24 24"><path d="M20 21a8 8 0 0 0-16 0"/><path d="M12 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z"/></svg>',
      login: '<svg viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/></svg>',
      grid: '<svg viewBox="0 0 24 24"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></svg>',
      play: '<svg viewBox="0 0 24 24"><path d="m8 5 12 7-12 7Z"/></svg>',
      pause: '<svg viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></svg>',
      shield: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/></svg>',
      trash: '<svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15"/></svg>',
    };
    return `<span class="icon" aria-hidden="true">${icons[name] || ""}</span>`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = SHB.qs("#addAccountForm");
    if (!form) return;
    form.addEventListener("submit", addAccount);
    SHB.qs("#saveGamesBtn").addEventListener("click", saveGames);
    SHB.qs("#confirmSteamGuardBtn").addEventListener("click", async () => {
      const code = SHB.qs("#steamGuardCode").value.trim();
      if (!code || !steamGuardAccountId) {
        SHB.toast("Введите код Steam Guard", "Нужен код", "error");
        return;
      }
      await loginAccount(steamGuardAccountId, code);
      SHB.qs("#steamGuardCode").value = "";
      steamGuardAccountId = null;
      SHB.closeModal("steamGuardModal");
    });
    SHB.qs("#gameSearch").addEventListener("input", (event) => {
      const query = event.target.value.trim().toLowerCase();
      SHB.qsa(".game-option").forEach((option) => {
        option.style.display = option.dataset.gameName.includes(query) ? "" : "none";
      });
    });
    document.addEventListener("shb:activity", renderActivity);
    fetchAccounts();
    renderActivity();
  });
})();
