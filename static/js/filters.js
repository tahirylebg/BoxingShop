// Filtrage dynamique du catalogue (amélioration progressive).
// Sans JS : le formulaire GET classique fonctionne. Avec JS : fetch + history.pushState, URL partageable.
const form = document.querySelector("[data-filter-form]");
const results = document.querySelector("[data-results]");

if (form && results) {
  const details = form.querySelector("[data-filter-details]");
  const mobile = window.matchMedia("(max-width: 63.99em)");
  if (details && mobile.matches) details.open = false;
  form.querySelector("[data-filter-submit]")?.setAttribute("hidden", "");

  let controller = null;

  const buildUrl = () => {
    const data = new FormData(form);
    data.delete("page");
    data.delete("tri");
    const sort = results.querySelector("[data-sort-select]");
    if (sort && sort.value !== "pertinence") data.set("tri", sort.value);
    const qs = new URLSearchParams(data).toString();
    return form.action + (qs ? `?${qs}` : "");
  };

  const syncForm = (url) => {
    const params = new URL(url, window.location.href).searchParams;
    form.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = params.getAll(cb.name).includes(cb.value);
    });
  };

  const bindResults = () => {
    results.querySelector("[data-sort-submit]")?.setAttribute("hidden", "");
  };

  const load = async (url, push = true) => {
    controller?.abort();
    controller = new AbortController();
    results.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "fetch" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      // Fragment HTML rendu et échappé côté serveur par les templates Django.
      const doc = new DOMParser().parseFromString(await response.text(), "text/html");
      results.replaceChildren(...doc.body.childNodes);
      if (push) window.history.pushState({ filters: true }, "", url);
      syncForm(url);
      bindResults();
    } catch (error) {
      if (error.name !== "AbortError") window.location.href = url; // repli : navigation classique
    } finally {
      results.removeAttribute("aria-busy");
    }
  };

  form.addEventListener("change", () => load(buildUrl()));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    load(buildUrl());
  });

  results.addEventListener("change", (event) => {
    if (event.target.matches("[data-sort-select]")) load(buildUrl());
  });
  results.addEventListener("submit", (event) => {
    if (event.target.matches("[data-sort-form]")) {
      event.preventDefault();
      load(buildUrl());
    }
  });
  results.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-filter-link]");
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    load(link.href);
    if (link.closest(".pagination")) results.scrollIntoView({ block: "start" });
  });

  window.addEventListener("popstate", () => load(window.location.href, false));
  bindResults();
}
