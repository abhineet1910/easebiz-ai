document.addEventListener("DOMContentLoaded", () => {
  const tabBtns = document.querySelectorAll(".tabBtn");
  const panels = document.querySelectorAll(".tabPanel");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;

      tabBtns.forEach((b) => {
        b.classList.remove("border-brand-600", "text-brand-600", "bg-brand-50/30");
        b.classList.add("border-transparent", "text-slate-500");
      });
      btn.classList.add("border-brand-600", "text-brand-600", "bg-brand-50/30");
      btn.classList.remove("border-transparent", "text-slate-500");

      panels.forEach((panel) => {
        if (panel.dataset.panel === target) {
          panel.classList.remove("hidden");
          panel.classList.add("fade-in");
        } else {
          panel.classList.add("hidden");
          panel.classList.remove("fade-in");
        }
      });
    });
  });
});
