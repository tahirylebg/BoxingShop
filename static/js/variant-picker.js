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
    $("[data-sku]").textContent = v.sku;
    form.querySelector("[data-variant-id]").value = v.id;

    const stock = $("[data-stock]");
    stock.classList.toggle("stock-line--out", v.stock <= 0);
    stock.classList.toggle("stock-line--low", v.stock > 0 && v.low);
    $("[data-stock-text]").textContent = v.stock <= 0
      ? "Épuisé dans cette déclinaison"
      : v.low ? `Stock faible : plus que ${v.stock} en stock` : "En stock — expédié sous 48 h";
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
