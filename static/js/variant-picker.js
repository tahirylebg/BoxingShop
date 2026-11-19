// Sélecteur de déclinaisons : met à jour prix, SKU, stock et visuel sans rechargement.
// Sans JS : le bouton « Afficher le prix et la disponibilité » recharge la fiche avec la déclinaison choisie.
const form = document.querySelector("[data-variant-form]");
const dataEl = document.getElementById("variant-data");

if (form && dataEl) {
  const variants = JSON.parse(dataEl.textContent);
  const axes = ["color", "weight", "size"].filter((a) => form.querySelector(`[data-axis="${a}"]`));
  const money = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });
  const $ = (sel) => document.querySelector(sel);
  const track = $("[data-gallery-track]");

  form.querySelectorAll("[data-nojs-only]").forEach((el) => { el.hidden = true; });

  const value = (v, axis) => (v[axis] === null || v[axis] === undefined ? "" : String(v[axis]));
  const selection = () => Object.fromEntries(axes.map((a) => {
    const checked = form.querySelector(`[data-axis="${a}"]:checked`);
    return [a, checked ? checked.value : null];
  }));
  const matches = (v, sel) => axes.every((a) => sel[a] === null || value(v, a) === sel[a]);

  const showSlide = (index) => {
    if (!track || index === null || index === undefined) return;
    const slide = track.children[index];
    if (slide) track.scrollTo({ left: slide.offsetLeft, behavior: "smooth" });
    document.querySelectorAll("[data-gallery-thumb]").forEach((t) => {
      t.setAttribute("aria-current", String(Number(t.dataset.galleryThumb) === index));
    });
  };

  const render = (v) => {
    const priceText = money.format(Number(v.price));
    $("[data-price]").textContent = priceText;
    $("[data-price]").classList.toggle("price--sale", Boolean(v.compare));
    const sticky = $("[data-price-sticky]");
    if (sticky) sticky.textContent = priceText;
    const compare = $("[data-compare]");
    compare.hidden = !v.compare;
    compare.textContent = v.compare ? money.format(Number(v.compare)) : "";
    const off = $("[data-discount]");
    if (off) {
      off.hidden = !v.compare;
      off.textContent = v.compare ? `-${Math.round((1 - Number(v.price) / Number(v.compare)) * 100)} %` : "";
    }
    $("[data-sku]").textContent = v.sku;
    form.querySelector("[data-variant-id]").value = v.id;

    const stock = $("[data-stock]");
    stock.classList.toggle("stock-line--out", v.stock <= 0);
    stock.classList.toggle("stock-line--low", v.stock > 0 && v.stock < 5);
    $("[data-stock-text]").textContent = v.stock <= 0
      ? "Épuisé dans cette déclinaison"
      : v.stock < 5 ? `Plus que ${v.stock} en stock` : "En stock · expédié sous 48 h";
    document.querySelectorAll("[data-add-button]").forEach((b) => { b.disabled = v.stock <= 0; });

    const labels = { color: v.color, weight: v.weight ? `${v.weight} oz` : "", size: v.size };
    axes.forEach((a) => {
      const out = form.querySelector(`[data-option-label="${a}"]`);
      if (out) out.textContent = labels[a];
    });

    const url = new URL(window.location.href);
    url.searchParams.set("sku", v.sku);
    ["couleur", "poids", "taille"].forEach((k) => url.searchParams.delete(k));
    window.history.replaceState(null, "", url);
  };

  const update = (changedAxis) => {
    let sel = selection();
    let variant = variants.find((v) => matches(v, sel));
    if (!variant && changedAxis) {
      // Combinaison inexistante : on garde l'option choisie et on ajuste les autres axes.
      const same = variants.filter((v) => value(v, changedAxis) === sel[changedAxis]);
      variant = same.find((v) => v.stock > 0) || same[0];
      if (variant) {
        axes.forEach((a) => {
          const input = form.querySelector(`[data-axis="${a}"][value="${CSS.escape(value(variant, a))}"]`);
          if (input) input.checked = true;
        });
        sel = selection();
      }
    }
    // Barre les options indisponibles compte tenu des autres choix.
    axes.forEach((a) => {
      form.querySelectorAll(`[data-axis="${a}"]`).forEach((input) => {
        const candidate = variants.find((v) => matches(v, { ...sel, [a]: input.value }));
        input.closest(".chip")?.classList.toggle("chip--unavailable", !candidate || candidate.stock <= 0);
      });
    });
    if (variant) {
      render(variant);
      if (changedAxis === "color") showSlide(variant.image);
    }
  };

  form.addEventListener("change", (event) => {
    const axis = event.target.dataset.axis;
    if (axis) update(axis);
  });

  document.querySelectorAll("[data-gallery-thumb]").forEach((thumb) => {
    thumb.addEventListener("click", (event) => {
      event.preventDefault();
      showSlide(Number(thumb.dataset.galleryThumb));
    });
  });

  update(null);
}

// Quantité : stepper [ − n + ] (l'input reste utilisable sans JS).
document.querySelectorAll("[data-stepper]").forEach((stepper) => {
  const input = stepper.querySelector("input");
  stepper.querySelectorAll("[data-step]").forEach((btn) => {
    btn.hidden = false;
    btn.addEventListener("click", () => {
      const next = Math.min(Number(input.max) || 99, Math.max(Number(input.min) || 1, (Number(input.value) || 1) + Number(btn.dataset.step)));
      input.value = String(next);
    });
  });
  stepper.classList.add("is-enhanced");
});

// Favoris : préférence propre au visiteur, conservée dans ce navigateur.
document.querySelectorAll("[data-fav]").forEach((btn) => {
  const key = "bs:favoris";
  const read = () => { try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; } };
  const sync = () => btn.setAttribute("aria-pressed", String(read().includes(btn.dataset.fav)));
  btn.hidden = false;
  sync();
  btn.addEventListener("click", () => {
    const list = read();
    const i = list.indexOf(btn.dataset.fav);
    if (i >= 0) list.splice(i, 1); else list.push(btn.dataset.fav);
    try { localStorage.setItem(key, JSON.stringify(list)); } catch { /* stockage indisponible */ }
    sync();
  });
});

// Guide des tailles : le tableau de la page est déplacé dans un tiroir latéral, puis remis en place.
const guide = document.querySelector("[data-size-guide]");
const guideOpen = document.querySelector("[data-size-guide-open]");
const chartSection = document.getElementById("tailles");
if (guide && guideOpen && chartSection && typeof guide.showModal === "function") {
  const body = guide.querySelector("[data-size-guide-body]");
  const nodes = [];
  guideOpen.addEventListener("click", (event) => {
    event.preventDefault();
    nodes.push(...chartSection.childNodes);
    body.replaceChildren(...nodes);
    guide.showModal();
  });
  const restore = () => { chartSection.replaceChildren(...nodes.splice(0)); };
  guide.addEventListener("close", () => { restore(); guideOpen.focus(); });
  guide.querySelector("[data-size-guide-close]").addEventListener("click", () => guide.close());
  guide.addEventListener("click", (event) => { if (event.target === guide) guide.close(); });
}

// Mobile : barre d'achat collante seulement quand le bouton principal est hors écran.
const mainAdd = document.querySelector("[data-add-main]");
const stickyBuy = document.querySelector("[data-sticky-buy]");
if (mainAdd && stickyBuy) {
  // Calcul au défilement (rAF) : fiable même après un saut de position (touche Début, ancre).
  let ticking = false;
  const sync = () => {
    ticking = false;
    stickyBuy.classList.toggle("is-visible", mainAdd.getBoundingClientRect().bottom < 0);
  };
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(sync); } }, { passive: true });
  sync();
}
