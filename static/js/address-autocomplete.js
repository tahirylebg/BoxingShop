// Autocomplétion d'adresse (API Adresse — Géoplateforme IGN / data.gouv.fr).
// Combobox ARIA accessible au clavier. Sans JS : saisie manuelle classique.
const root = document.querySelector("[data-autocomplete-root]");
const input = root?.querySelector("[data-address-autocomplete]");

if (root && input) {
  const apiUrl = root.dataset.apiUrl;
  const postcode = document.querySelector("[data-address-postcode]");
  const city = document.querySelector("[data-address-city]");
  const list = document.createElement("ul");
  const listId = `${input.id}-suggestions`;
  list.id = listId;
  list.className = "autocomplete__list";
  list.setAttribute("role", "listbox");
  list.setAttribute("aria-label", "Suggestions d'adresses");
  list.hidden = true;
  input.after(list);

  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", listId);

  let results = [];
  let active = -1;
  let timer = null;
  let controller = null;

  const closeList = () => {
    list.hidden = true;
    list.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    active = -1;
  };

  const highlight = (index) => {
    active = index;
    [...list.children].forEach((li, i) => li.setAttribute("aria-selected", String(i === index)));
    if (index >= 0) input.setAttribute("aria-activedescendant", list.children[index].id);
  };

  const choose = (index) => {
    const props = results[index]?.properties;
    if (!props) return;
    input.value = props.name || props.label;
    if (postcode && props.postcode) postcode.value = props.postcode;
    if (city && props.city) city.value = props.city;
    closeList();
    input.focus();
  };

  const render = () => {
    list.replaceChildren(...results.map((feature, i) => {
      const li = document.createElement("li");
      li.id = `${listId}-${i}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.textContent = feature.properties.label; // jamais d'innerHTML avec des données externes
      li.addEventListener("mousedown", (event) => {
        event.preventDefault();
        choose(i);
      });
      return li;
    }));
    list.hidden = results.length === 0;
    input.setAttribute("aria-expanded", String(results.length > 0));
  };

  const search = async (query) => {
    controller?.abort();
    controller = new AbortController();
    const url = new URL(apiUrl);
    url.search = new URLSearchParams({ q: query, limit: "5", index: "address", autocomplete: "1" });
    try {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) return;
      const data = await response.json();
      results = (data.features || []).filter((f) => f.properties && f.properties.label);
      render();
    } catch {
      /* réseau indisponible : la saisie manuelle reste possible */
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const query = input.value.trim();
    if (query.length < 4) {
      closeList();
      return;
    }
    timer = setTimeout(() => search(query), 250);
  });

  input.addEventListener("keydown", (event) => {
    if (list.hidden) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      highlight((active + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      highlight(active <= 0 ? results.length - 1 : active - 1);
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      choose(active);
    } else if (event.key === "Escape") {
      closeList();
    }
  });

  input.addEventListener("blur", () => setTimeout(closeList, 150));
}
