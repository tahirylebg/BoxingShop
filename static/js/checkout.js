// Checkout : en mobile, le récapitulatif est un accordéon replié en haut de page ; ouvert sur grand écran.
const summary = document.querySelector("[data-order-summary]");
const desktop = window.matchMedia("(min-width: 64em)");
const sync = () => {
  if (!summary) return;
  summary.open = desktop.matches;
};
sync();
desktop.addEventListener("change", sync);
