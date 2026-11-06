(function () {
  "use strict";

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  window.TaskFlow = {
    csrfToken: getCsrfToken,

    async apiRequest(method, url, body) {
      const options = {
        method,
        credentials: "same-origin",
        headers: { "Accept": "application/json", "X-CSRFToken": getCsrfToken() },
      };
      if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
      }
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = (data.error && data.error.message) || `Request failed (${response.status})`;
        throw new Error(message);
      }
      return data;
    },

    toast(message, type) {
      const el = document.createElement("div");
      el.className = "board-toast" + (type === "error" ? " error" : "");
      el.setAttribute("role", "status");
      el.dataset.testid = "toast";
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 3000);
    },
  };

  document.addEventListener("click", function (event) {
    const dismiss = event.target.closest('[data-action="dismiss-flash"]');
    if (dismiss) {
      dismiss.closest(".flash").remove();
      return;
    }

    if (event.target.closest('[data-action="toggle-sidebar"]')) {
      document.body.classList.toggle("sidebar-open");
      return;
    }

    const toggle = event.target.closest("[data-dropdown-toggle]");
    document.querySelectorAll("[data-dropdown]").forEach(function (dropdown) {
      const menu = dropdown.querySelector("[data-dropdown-menu]");
      const button = dropdown.querySelector("[data-dropdown-toggle]");
      const isThis = toggle && dropdown.contains(toggle);
      const shouldOpen = isThis && menu.hidden;
      if (!isThis && dropdown.contains(event.target)) return;
      menu.hidden = !shouldOpen;
      button.setAttribute("aria-expanded", String(shouldOpen));
    });
  });

  document.addEventListener("submit", function (event) {
    const message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      document.querySelectorAll("[data-dropdown-menu]").forEach((menu) => (menu.hidden = true));
      document.body.classList.remove("sidebar-open");
    }
  });
})();
