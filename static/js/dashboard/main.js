// Placeholder for future dashboard interactivity
console.log("Dashboard JS loaded.");

// Example: Add subtle transition class on load or interaction
document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".card");
  cards.forEach((card, index) => {
    card.style.transition = `opacity 0.5s ease ${
      index * 0.1
    }s, transform 0.5s ease ${index * 0.1}s`;
    card.style.opacity = 0;
    card.style.transform = "translateY(20px)";

    // Trigger animation
    setTimeout(() => {
      card.style.opacity = 1;
      card.style.transform = "translateY(0)";
    }, 100);
  });
});
