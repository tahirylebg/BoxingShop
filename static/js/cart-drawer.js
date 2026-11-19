// Panier latéral coulissant (<dialog> natif : focus piégé, Échap, retour du focus).
// Sans JS : les liens et formulaires mènent à la page /panier/.
const dialog = document.getElementById("cart-drawer");
const content = dialog?.querySelector("[data-drawer-content]");
let opener = null;

const setCount = (count) => {
  document.querySelectorAll("[data-cart-count]").forEach((el) => {
    const changed = el.dataset.count !== String(count);
    el.textContent = count;
    el.dataset.count = count;
    if (changed) {
      el.classList.remove("is-bumped");
      void el.offsetWidth; // relance l'animation
      el.classList.add("is-bumped");
    }
  });
};

const renderDrawer = (html) => {
  const doc = new DOMParser().parseFromString(html, "text/html"); // HTML échappé côté serveur
  content.replaceChildren(...doc.body.childNodes);
  const marker = content.querySelector("[data-cart-total-count]");
  if (marker) setCount(marker.dataset.cartTotalCount);
};

const refresh = async () => {
  const response = await fetch(dialog.dataset.drawerUrl, { headers: { "X-Requested-With": "fetch" } });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  renderDrawer(await response.text());
};

const open = () => {
  if (dialog.open) return;
  opener = document.activeElement;
  dialog.showModal();
  dialog.querySelector("[data-drawer-close]")?.focus();
};

const close = () => dialog.close();

const post = async (formEl, submitter) => {
  const data = new FormData(formEl);
  if (submitter?.name) data.set(submitter.name, submitter.value);
  const response = await fetch(formEl.action, {
    method: "POST",
    body: data,
    headers: { "X-Requested-With": "fetch" },
  });
  return response.json();
};

// Bouton d'ajout : « ✓ Ajouté » pendant 2 s après un ajout réussi.
const confirmAdded = () => {
  document.querySelectorAll("[data-add-label]").forEach((label) => {
    const button = label.closest("button");
    if (!label.dataset.idle) label.dataset.idle = label.textContent;
    label.textContent = "✓ Ajouté";
    button?.classList.add("is-added");
    clearTimeout(Number(label.dataset.timer));
    label.dataset.timer = String(setTimeout(() => {
      label.textContent = label.dataset.idle;
      button?.classList.remove("is-added");
    }, 2000));
  });
};

const announce = (formEl, message) => {
  let region = formEl.querySelector("[data-form-message]");
  if (!region) {
    region = document.createElement("p");
    region.className = "message message--error mt-3";
    region.setAttribute("role", "alert");
    region.dataset.formMessage = "";
    formEl.append(region);
  }
  region.textContent = message;
};

if (dialog && content) {
  document.addEventListener("click", async (event) => {
    if (event.target.closest("[data-cart-open]")) {
      event.preventDefault();
      try {
        await refresh();
        open();
      } catch {
        window.location.href = event.target.closest("a").href;
      }
    } else if (event.target.closest("[data-drawer-close]")) {
      close();
    }
  });

  // Clic sur le fond (::backdrop) : fermeture.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) close();
  });
  dialog.addEventListener("close", () => opener?.focus?.());

  document.addEventListener("submit", async (event) => {
    const formEl = event.target;
    const submitter = event.submitter;
    const isAdd = formEl.matches("[data-add-to-cart]") && submitter?.value !== "preview";
    const isLine = formEl.matches("[data-cart-line]") && dialog.contains(formEl);
    if (!isAdd && !isLine) return;
    event.preventDefault();
    const wasDisabled = submitter?.disabled;
    if (submitter) {
      submitter.disabled = true;
      submitter.setAttribute("aria-busy", "true");
    }
    const body = dialog.querySelector(".drawer__body");
    if (isLine) body?.setAttribute("aria-busy", "true");
    try {
      const result = await post(formEl, submitter);
      if (result.html) renderDrawer(result.html);
      if (result.count !== undefined) setCount(result.count);
      if (!result.ok) {
        announce(formEl, result.message || "Action impossible.");
        return;
      }
      formEl.querySelector("[data-form-message]")?.remove();
      if (isAdd) {
        confirmAdded();
        open();
      }
    } catch {
      formEl.submit(); // repli : soumission classique
    } finally {
      if (submitter) {
        submitter.disabled = wasDisabled;
        submitter.removeAttribute("aria-busy");
      }
      dialog.querySelector(".drawer__body")?.removeAttribute("aria-busy");
    }
  });
}

// Panier (mobile) : total + bouton collants tant que le bouton du récapitulatif n'est pas visible.
const cartBar = document.querySelector("[data-cart-bar]");
const checkoutMain = document.querySelector("[data-checkout-main]");
if (cartBar && checkoutMain) {
  let ticking = false;
  const sync = () => {
    ticking = false;
    const r = checkoutMain.getBoundingClientRect();
    cartBar.classList.toggle("is-visible", r.top > window.innerHeight || r.bottom < 0);
  };
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(sync); } }, { passive: true });
  window.addEventListener("resize", sync);
  sync();
}
