// Mouvement sobre : révélation au défilement (IntersectionObserver) et loupe qui suit le curseur.
// Amélioration progressive : sans JS, tout le contenu est visible et la galerie zoome au centre.
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

function setupReveal() {
  const items = [...document.querySelectorAll("[data-reveal]")];
  if (reduced || !("IntersectionObserver" in window) || !items.length) return;
  const fold = window.innerHeight;
  // Seuls les éléments sous la ligne de flottaison sont masqués : aucun clignotement au chargement.
  const pending = items.filter((el) => el.getBoundingClientRect().top > fold);
  pending.forEach((el) => {
    const siblings = [...el.parentElement.children].filter((c) => c.hasAttribute("data-reveal"));
    el.style.setProperty("--reveal-index", String(Math.min(siblings.indexOf(el), 8)));
    el.classList.add("reveal-pending");
  });
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  pending.forEach((el) => observer.observe(el));
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
