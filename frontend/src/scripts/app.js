document.documentElement.classList.add("js");

const menuToggle = document.querySelector(".menu-toggle");
const mainNavigation = document.querySelector("#main-navigation");

if (menuToggle && mainNavigation) {
  menuToggle.addEventListener("click", () => {
    const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", String(!isOpen));
    mainNavigation.classList.toggle("is-open", !isOpen);
  });

  mainNavigation.addEventListener("click", (event) => {
    if (!event.target.closest("a")) return;
    menuToggle.setAttribute("aria-expanded", "false");
    mainNavigation.classList.remove("is-open");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    menuToggle.setAttribute("aria-expanded", "false");
    mainNavigation.classList.remove("is-open");
    menuToggle.focus();
  });
}

const materialCarousel = document.querySelector("[data-material-carousel]");

function connectCarouselPosition(carousel, cardSelector, output) {
  if (!carousel || !output) return;
  const cards = [...carousel.querySelectorAll(cardSelector)];
  if (!cards.length) return;
  const update = () => {
    const gap = Number.parseFloat(getComputedStyle(carousel).columnGap) || 0;
    const step = cards[0].offsetWidth + gap;
    const current = Math.min(cards.length, Math.max(1, Math.round(carousel.scrollLeft / step) + 1));
    output.textContent = `${current} / ${cards.length}`;
  };
  carousel.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
}

if (materialCarousel) {
  connectCarouselPosition(materialCarousel, ".featured-material-card", document.querySelector("[data-material-position]"));
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
  connectCarouselPosition(projectCarousel, ".project-card", document.querySelector("[data-project-position]"));
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
