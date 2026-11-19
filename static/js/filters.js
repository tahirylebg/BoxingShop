// Filtrage dynamique du catalogue (amélioration progressive).
// Sans JS : le formulaire GET classique fonctionne. Avec JS : fetch + history.pushState, URL partageable.
const form = document.querySelector("[data-filter-form]");
const results = document.querySelector("[data-results]");

if (form && results) {
  const aside = document.querySelector("[data-filters]");
  const slot = aside?.querySelector("[data-active-slot]");
  const fab = document.querySelector("[data-filters-open]");
  const submit = form.querySelector("[data-filter-submit]");
  const mobile = window.matchMedia("(max-width: 63.99em)");
  // Desktop : filtrage instantané, le bouton est inutile. Mobile : il ferme le tiroir (« Voir N produits »).
  const syncSubmit = () => submit?.toggleAttribute("hidden", !mobile.matches);
  syncSubmit();
  mobile.addEventListener("change", syncSubmit);

  // Tiroir plein écran (mobile). Sans JS : ancre #filtres + :target.
  const openDrawer = () => {
    aside.classList.add("is-open");
    document.documentElement.classList.add("has-filters-open");
    aside.querySelector("summary, input")?.focus();
  };
  const closeDrawer = () => {
    aside.classList.remove("is-open");
    document.documentElement.classList.remove("has-filters-open");
    fab?.focus();
  };
  fab?.addEventListener("click", (event) => { event.preventDefault(); openDrawer(); });
  aside?.querySelector("[data-filters-close]")?.addEventListener("click", (event) => { event.preventDefault(); closeDrawer(); });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && aside?.classList.contains("is-open")) closeDrawer();
  });

  // Filtres actifs (en haut de la sidebar), compteurs par section, bouton flottant et total.
  const syncChrome = () => {
    const src = results.querySelector("template[data-active-src]");
    if (slot && src) slot.replaceChildren(src.content.cloneNode(true));
    form.querySelectorAll(".filter-group").forEach((group) => {
      const n = group.querySelectorAll("input:checked").length;
      const badge = group.querySelector("[data-group-count]");
      if (badge) { badge.textContent = n; badge.hidden = n === 0; }
    });
    const active = form.querySelectorAll("input[type=checkbox]:checked").length;
    if (fab) fab.textContent = active ? `Filtrer (${active})` : "Filtrer";
    const total = results.querySelector("[data-results-count] strong")?.textContent || "0";
    if (submit) submit.textContent = `Voir ${total} produit${Number(total) > 1 ? "s" : ""}`;
  };

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
      syncChrome();
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
    if (aside?.classList.contains("is-open")) closeDrawer();
  });
  slot?.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-filter-link]");
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    load(link.href);
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
