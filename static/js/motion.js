// Mouvement sobre : révélation au défilement (IntersectionObserver) et loupe qui suit le curseur.
// Amélioration progressive : sans JS, tout le contenu est visible et la galerie zoome au centre.
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
