document.querySelectorAll(".material-quote-link").forEach((link) => {
  link.addEventListener("click", () => {
    const slug = link.dataset.materialSlug;
    if (slug) sessionStorage.setItem("3dlab:selected-material", slug);
  });
});

