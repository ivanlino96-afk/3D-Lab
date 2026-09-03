const comparisonInputs = [...document.querySelectorAll(".compare-checkbox")];
const comparisonTray = document.querySelector("#comparison-tray");
const comparisonCount = document.querySelector("#comparison-count");
const comparisonLink = document.querySelector("#comparison-link");

function updateComparison() {
  const selected = comparisonInputs.filter((input) => input.checked).map((input) => input.value);
  if (!comparisonTray || !comparisonCount || !comparisonLink) return;
  comparisonCount.textContent = String(selected.length);
  comparisonTray.hidden = selected.length === 0;
  comparisonLink.toggleAttribute("aria-disabled", selected.length < 2);
  comparisonLink.href = `/materiales/comparar?${new URLSearchParams(selected.map((slug) => ["material", slug]))}`;
}

comparisonInputs.forEach((input) => input.addEventListener("change", updateComparison));
comparisonLink?.addEventListener("click", (event) => {
  if (comparisonLink.getAttribute("aria-disabled") === "true") event.preventDefault();
});

