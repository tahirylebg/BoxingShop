// Navigation : annonces en fondu, en-tête masqué au défilement, méga-menu, recherche en direct,
// menu mobile, progression de lecture et sommaire actif. Amélioration progressive : tout fonctionne sans JS
// (<details> natifs, formulaire GET, liens d'ancre).
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function setupAnnounce() {
  const root = document.querySelector("[data-announce]");
  if (!root) return;
  const items = [...root.querySelectorAll("li")];
  const toggle = root.querySelector("[data-announce-toggle]");
  if (items.length < 2 || reduced) return; // mouvement réduit : la première annonce reste fixe
  let index = 0;
  let paused = false;
  let hovered = false;
  toggle.hidden = false;
  setInterval(() => {
    if (paused || hovered || document.hidden) return;
    items[index].classList.remove("is-active");
    index = (index + 1) % items.length;
    items[index].classList.add("is-active");
  }, 4000);
  root.addEventListener("pointerenter", () => { hovered = true; });
  root.addEventListener("pointerleave", () => { hovered = false; });
  toggle.addEventListener("click", () => {
    paused = !paused;
    toggle.setAttribute("aria-pressed", String(paused));
    toggle.querySelector(".visually-hidden").textContent = paused ? "Reprendre les annonces" : "Mettre en pause les annonces";
  });
}

function setupHeader() {
  const header = document.querySelector("[data-site-header]");
  if (!header) return;
  let lastY = window.scrollY;
  let ticking = false;
  const update = () => {
    const y = window.scrollY;
    const busy = header.querySelector("details[open]") || header.matches(":focus-within, :hover");
    if (busy || y < 120 || y < lastY - 4) header.classList.remove("is-hidden");
    else if (y > lastY + 4) header.classList.add("is-hidden");
    header.classList.toggle("is-scrolled", y > 8);
    lastY = y;
    ticking = false;
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { requestAnimationFrame(update); ticking = true; }
  }, { passive: true });
  header.addEventListener("focusin", () => header.classList.remove("is-hidden"));
}

function setupMega() {
  // Le CSS ouvre le panneau au survol et au focus clavier ; Échap le referme et rend le focus au lien.
  document.querySelectorAll("[data-mega-item]").forEach((item) => {
    const link = item.querySelector(".nav-main__link");
    const panel = item.querySelector("[data-mega]");
    if (!panel) return;
    link.setAttribute("aria-haspopup", "true");
    const sync = () => link.setAttribute("aria-expanded", String(item.matches(":hover, :focus-within") && !item.classList.contains("is-dismissed")));
    item.addEventListener("pointerenter", () => { item.classList.remove("is-dismissed"); sync(); });
    item.addEventListener("pointerleave", sync);
    item.addEventListener("focusin", sync);
    item.addEventListener("focusout", () => setTimeout(() => { if (!item.matches(":focus-within")) item.classList.remove("is-dismissed"); sync(); }));
    item.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      item.classList.add("is-dismissed");
      link.focus();
      sync();
    });
    sync();
  });
}

function setupSearch() {
  const panel = document.querySelector("[data-search]");
  if (!panel) return;
  const form = panel.querySelector("form");
  const input = form.querySelector("input[type=search]");
  const list = panel.querySelector("[data-search-results]");
  const status = panel.querySelector("[data-search-status]");
  const url = form.dataset.suggestUrl;
  let timer;
  let controller;

  panel.addEventListener("toggle", () => {
    document.documentElement.classList.toggle("has-search-open", panel.open);
    if (panel.open) input.focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.open) {
      panel.open = false;
      panel.querySelector("summary").focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (panel.open && !panel.contains(event.target)) panel.open = false;
  });

  const render = (results, query) => {
    list.replaceChildren();
    results.forEach((r) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = r.url;
      a.className = "suggestion";
      if (r.image) {
        const img = document.createElement("img");
        img.src = r.image;
        img.alt = "";
        img.width = 64;
        img.height = 80;
        img.loading = "lazy";
        a.append(img);
      } else {
        a.append(document.createElement("span"));
      }
      const text = document.createElement("span");
      const name = document.createElement("strong");
      name.textContent = r.name;
      const meta = document.createElement("small");
      meta.textContent = r.category;
      text.append(name, meta);
      const price = document.createElement("span");
      price.className = "price";
      price.textContent = r.price;
      a.append(text, price);
      li.append(a);
      list.append(li);
    });
    status.textContent = query.length < 2 ? "" : results.length ? `${results.length} suggestion(s)` : "Aucun produit trouvé : validez pour lancer une recherche complète.";
  };

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const query = input.value.trim();
    timer = setTimeout(async () => {
      if (query.length < 2) { render([], query); return; }
      controller?.abort();
      controller = new AbortController();
      list.setAttribute("aria-busy", "true");
      try {
        const response = await fetch(`${url}?q=${encodeURIComponent(query)}`, { signal: controller.signal, headers: { Accept: "application/json" } });
        if (response.ok) render((await response.json()).results, query);
      } catch (error) {
        if (error.name !== "AbortError") status.textContent = "Suggestions indisponibles : validez pour lancer la recherche.";
      } finally {
        list.removeAttribute("aria-busy");
      }
    }, 180);
  });
}

function setupMobileMenu() {
  const menu = document.querySelector("[data-menu-mobile]");
  if (!menu) return;
  menu.addEventListener("toggle", () => {
    document.documentElement.classList.toggle("has-menu-open", menu.open);
    menu.querySelector("summary").setAttribute("aria-label", menu.open ? "Fermer le menu" : "Ouvrir le menu");
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
  window.matchMedia("(min-width: 64em)").addEventListener("change", (e) => { if (e.matches) menu.open = false; });
}

function setupReading() {
  const article = document.querySelector("[data-guide]");
  const bar = document.querySelector("[data-read-progress]");
  if (!article || !bar) return;
  let ticking = false;
  const update = () => {
    const rect = article.getBoundingClientRect();
    const total = rect.height - window.innerHeight;
    const progress = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 1;
    bar.style.transform = `scaleX(${progress})`;
    ticking = false;
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { requestAnimationFrame(update); ticking = true; }
  }, { passive: true });
  update();

  const links = [...document.querySelectorAll("[data-toc-link]")];
  const targets = links.map((a) => document.getElementById(a.hash.slice(1))).filter(Boolean);
  if (!("IntersectionObserver" in window) || !targets.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((a) => a.removeAttribute("aria-current"));
      links.find((a) => a.hash === `#${entry.target.id}`)?.setAttribute("aria-current", "location");
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  targets.forEach((t) => observer.observe(t));
}

setupAnnounce();
setupHeader();
setupMega();
setupSearch();
setupMobileMenu();
setupReading();
