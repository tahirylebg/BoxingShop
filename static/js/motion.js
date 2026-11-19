// Mouvement sobre : révélation au défilement (IntersectionObserver) et loupe qui suit le curseur.
// Amélioration progressive : sans JS, tout le contenu est visible et la galerie zoome au centre.
// html.js : seul cas où un état caché (.reveal) peut s'appliquer ; sans JS tout reste visible.
document.documentElement.classList.add("js");
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Compteurs du hero : 0 -> valeur au chargement. La valeur finale est déjà dans le HTML (sans JS ni mouvement).
function setupCounters() {
  if (reduced) return;
  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = Number(el.dataset.count);
    if (!target) return;
    const start = performance.now();
    const duration = 1100;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      el.textContent = String(Math.round(target * (1 - (1 - t) ** 3)));
      if (t < 1) requestAnimationFrame(tick);
    };
    el.textContent = "0";
    requestAnimationFrame(tick);
  });
}
setupCounters();

// Une seule classe utilitaire, .reveal ; l'état est porté par data-reveal (pending -> in).
// Les éléments d'une même liste (cartes) apparaissent en cascade : 60 ms d'écart, 6 au plus.
function setupReveal() {
  const items = [...document.querySelectorAll(".reveal")];
  if (reduced || !("IntersectionObserver" in window) || !items.length) return;
  const fold = window.innerHeight;
  const pending = items.filter((el) => el.getBoundingClientRect().top > fold);
  pending.forEach((el) => { el.dataset.reveal = "pending"; });
  // Un titre masqué par clip-path n'a plus de surface visible : on observe alors sa bande parente.
  const watched = new Map(pending.map((el) => [el.matches(".campaign__title") ? el.closest(".campaign") : el, el]));
  const observer = new IntersectionObserver((entries) => {
    let step = 0;
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = watched.get(entry.target);
      if (el.tagName === "LI") {
        el.style.setProperty("--reveal-delay", `${Math.min(step, 5) * 60}ms`);
        step += 1;
      }
      el.dataset.reveal = "in";
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });
  watched.forEach((_, target) => observer.observe(target));
}

// Bandes photo plein-largeur : léger parallax de l'image (±40 px), calculé au scroll (rAF).
function setupParallax() {
  const images = [...document.querySelectorAll(".campaign__media img")];
  if (reduced || !images.length) return;
  let ticking = false;
  const update = () => {
    ticking = false;
    const vh = window.innerHeight;
    images.forEach((img) => {
      const rect = img.parentElement.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > vh) return;
      const progress = (rect.top + rect.height / 2 - vh / 2) / (vh / 2 + rect.height / 2);
      img.style.setProperty("--parallax", `${(-progress * 40).toFixed(1)}px`);
    });
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  update();
}

function setupGalleryZoom() {
  if (!window.matchMedia("(hover: hover) and (min-width: 64em)").matches) return;
  document.querySelectorAll(".gallery__slide").forEach((slide) => {
    const img = slide.querySelector("img");
    if (!img) return;
    slide.addEventListener("pointermove", (event) => {
      const rect = slide.getBoundingClientRect();
      img.style.setProperty("--zoom-x", `${((event.clientX - rect.left) / rect.width) * 100}%`);
      img.style.setProperty("--zoom-y", `${((event.clientY - rect.top) / rect.height) * 100}%`);
    });
  });
}

setupReveal();
setupParallax();
setupGalleryZoom();

// Cartes produit : survol (ou focus) d'une pastille -> photo de cette couleur ; on revient à la photo d'origine en sortant.
document.addEventListener("pointerover", swapCardImage);
document.addEventListener("focusin", swapCardImage);
function swapCardImage(event) {
  const link = event.target.closest?.("[data-swatch-srcset]");
  if (!link) return;
  const card = link.closest("[data-card]");
  const img = card?.querySelector(".card__main");
  if (!img) return;
  if (!img.dataset.origSrcset) {
    img.dataset.origSrc = img.getAttribute("src");
    img.dataset.origSrcset = img.getAttribute("srcset");
    const restore = () => {
      img.setAttribute("srcset", img.dataset.origSrcset);
      img.setAttribute("src", img.dataset.origSrc);
      card.querySelectorAll(".swatch-link").forEach((l) => l.classList.toggle("is-preview", false));
    };
    card.querySelector(".swatches")?.addEventListener("pointerleave", restore);
    card.querySelector(".swatches")?.addEventListener("focusout", (e) => { if (!card.querySelector(".swatches").contains(e.relatedTarget)) restore(); });
  }
  img.setAttribute("srcset", link.dataset.swatchSrcset);
  img.setAttribute("src", link.dataset.swatchSrc);
  card.querySelectorAll(".swatch-link").forEach((l) => l.classList.toggle("is-preview", l === link));
}
