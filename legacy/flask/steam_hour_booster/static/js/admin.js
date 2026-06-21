(function () {
  const SHB = window.SHB;

  function syncStats() {
    const rows = SHB.qsa("[data-user-row]");
    const active = rows.filter((row) => row.dataset.banned !== "1").length;
    const admins = rows.filter((row) => row.dataset.admin === "1").length;
    const subscribed = rows.filter((row) => row.dataset.subscription === "1").length;
    const values = { adminUsersTotal: rows.length, adminUsersActive: active, adminUsersSubscribed: subscribed, adminUsersAdmins: admins };
    Object.entries(values).forEach(([id, value]) => {
      const node = SHB.qs(`#${id}`);
      if (node) node.textContent = value;
    });
  }

  function applyFilters() {
    const query = (SHB.qs("#adminLocalSearch")?.value || "").trim().toLowerCase();
    const role = SHB.qs("#adminRoleFilter")?.value || "all";
    const status = SHB.qs("#adminStatusFilter")?.value || "all";
    SHB.qsa("[data-user-row]").forEach((row) => {
      const matchesQuery = row.dataset.username.includes(query);
      const matchesRole = role === "all" || (role === "admin" ? row.dataset.admin === "1" : row.dataset.admin !== "1");
      const matchesStatus = status === "all" || (status === "banned" ? row.dataset.banned === "1" : row.dataset.banned !== "1");
      row.style.display = matchesQuery && matchesRole && matchesStatus ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    syncStats();
    ["#adminLocalSearch", "#adminRoleFilter", "#adminStatusFilter"].forEach((selector) => {
      const node = SHB.qs(selector);
      if (node) node.addEventListener("input", applyFilters);
    });
  });
})();
