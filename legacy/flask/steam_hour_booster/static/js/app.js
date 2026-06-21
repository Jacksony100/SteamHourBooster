(function () {
  const SHB = (window.SHB = window.SHB || {});

  SHB.qs = (selector, root = document) => root.querySelector(selector);
  SHB.qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  SHB.escapeHTML = function escapeHTML(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  };

  SHB.api = async function api(url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (csrfToken && !headers["X-CSRF-Token"]) {
      headers["X-CSRF-Token"] = csrfToken;
    }
    const response = await fetch(url, {
      headers,
      ...options,
    });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
      const message = typeof payload === "string" ? payload : payload.error || "Ошибка запроса";
      throw new Error(message);
    }
    return payload;
  };

  SHB.toast = function toast(message, title = "Готово", type = "success") {
    let stack = SHB.qs("#toastStack");
    if (!stack) {
      stack = document.createElement("div");
      stack.id = "toastStack";
      stack.className = "toast-stack";
      stack.setAttribute("aria-live", "polite");
      document.body.appendChild(stack);
    }
    const item = document.createElement("div");
    item.className = `toast ${type}`;
    item.innerHTML = `<strong>${SHB.escapeHTML(title)}</strong><p>${SHB.escapeHTML(message)}</p>`;
    stack.appendChild(item);
    setTimeout(() => item.remove(), 4200);
  };

  SHB.setButtonLoading = function setButtonLoading(button, loadingText = "Загрузка...") {
    if (!button) return () => {};
    const previous = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="spinner"></span>${SHB.escapeHTML(loadingText)}`;
    return () => {
      button.disabled = false;
      button.innerHTML = previous;
    };
  };

  SHB.openModal = function openModal(id) {
    const modal = SHB.qs(`#${id}`);
    if (!modal) return;
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    const focusTarget = modal.querySelector("input, select, button");
    if (focusTarget) focusTarget.focus({ preventScroll: true });
  };

  SHB.closeModal = function closeModal(id) {
    const modal = SHB.qs(`#${id}`);
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
  };

  SHB.confirm = function confirm({ title, message, confirmText = "Подтвердить", danger = false }) {
    return new Promise((resolve) => {
      const modal = SHB.qs("#confirmModal");
      if (!modal) {
        resolve(false);
        return;
      }
      SHB.qs("[data-confirm-title]", modal).textContent = title;
      SHB.qs("[data-confirm-message]", modal).textContent = message;
      const confirmButton = SHB.qs("[data-confirm-accept]", modal);
      confirmButton.textContent = confirmText;
      confirmButton.className = danger ? "btn btn-danger" : "btn btn-primary";
      const cleanup = () => {
        confirmButton.onclick = null;
        SHB.qsa("[data-modal-close]", modal).forEach((button) => {
          button.onclick = null;
        });
      };
      confirmButton.onclick = () => {
        cleanup();
        SHB.closeModal("confirmModal");
        resolve(true);
      };
      SHB.qsa("[data-modal-close]", modal).forEach((button) => {
        button.onclick = () => {
          cleanup();
          SHB.closeModal("confirmModal");
          resolve(false);
        };
      });
      SHB.openModal("confirmModal");
    });
  };

  SHB.addActivity = function addActivity(text, meta = "только что") {
    const key = "shb.activity";
    const items = JSON.parse(localStorage.getItem(key) || "[]");
    items.unshift({ text, meta });
    localStorage.setItem(key, JSON.stringify(items.slice(0, 8)));
    document.dispatchEvent(new CustomEvent("shb:activity"));
  };

  SHB.getActivity = function getActivity() {
    return JSON.parse(localStorage.getItem("shb.activity") || "[]");
  };

  document.addEventListener("click", (event) => {
    const close = event.target.closest("[data-modal-close]");
    if (close) SHB.closeModal(close.dataset.modalClose);
    if (event.target.classList.contains("modal-backdrop")) SHB.closeModal(event.target.id);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      SHB.qsa(".modal-backdrop.open").forEach((modal) => SHB.closeModal(modal.id));
    }
  });

  window.addEventListener("error", (event) => {
    SHB.toast(event.message || "Неизвестная ошибка интерфейса", "Ошибка интерфейса", "error");
  });

  window.addEventListener("unhandledrejection", (event) => {
    const message = event.reason && event.reason.message ? event.reason.message : "Не удалось выполнить действие";
    SHB.toast(message, "Ошибка запроса", "error");
  });
})();
