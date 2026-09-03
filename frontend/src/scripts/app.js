document.documentElement.classList.add("js");

const materialCarousel = document.querySelector("[data-material-carousel]");

if (materialCarousel) {
  const scrollOneCard = (direction) => {
    const card = materialCarousel.querySelector(".featured-material-card");
    if (!card) return;

    const gap = Number.parseFloat(getComputedStyle(materialCarousel).columnGap) || 0;
    materialCarousel.scrollBy({ left: direction * (card.offsetWidth + gap), behavior: "smooth" });
  };

  document.querySelector("[data-carousel-previous]")?.addEventListener("click", () => scrollOneCard(-1));
  document.querySelector("[data-carousel-next]")?.addEventListener("click", () => scrollOneCard(1));

  materialCarousel.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    scrollOneCard(event.key === "ArrowLeft" ? -1 : 1);
  });
}

const projectCarousel = document.querySelector("[data-project-carousel]");

if (projectCarousel) {
  const scrollProject = (direction) => {
    const card = projectCarousel.querySelector(".project-card");
    if (!card) return;
    const gap = Number.parseFloat(getComputedStyle(projectCarousel).columnGap) || 0;
    projectCarousel.scrollBy({ left: direction * (card.offsetWidth + gap), behavior: "smooth" });
  };

  document.querySelector("[data-project-previous]")?.addEventListener("click", () => scrollProject(-1));
  document.querySelector("[data-project-next]")?.addEventListener("click", () => scrollProject(1));
  projectCarousel.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    scrollProject(event.key === "ArrowLeft" ? -1 : 1);
  });
}
