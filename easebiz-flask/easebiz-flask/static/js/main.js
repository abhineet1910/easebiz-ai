document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();

  // Navbar glass effect on scroll (mirrors the React isScrolled state)
  const navbar = document.getElementById("navbar");
  const onScroll = () => {
    if (window.scrollY > 20) {
      navbar.classList.add("glass", "py-3");
      navbar.classList.remove("bg-transparent", "py-5");
    } else {
      navbar.classList.remove("glass", "py-3");
      navbar.classList.add("bg-transparent", "py-5");
    }
  };
  window.addEventListener("scroll", onScroll);
  onScroll();

  // Mobile menu toggle
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenu = document.getElementById("mobileMenu");
  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", () => {
      const isOpen = !mobileMenu.classList.contains("hidden");
      mobileMenu.classList.toggle("hidden");
      mobileMenu.classList.toggle("flex");
      mobileMenuBtn.innerHTML = isOpen
        ? '<i data-lucide="menu" class="w-6 h-6"></i>'
        : '<i data-lucide="x" class="w-6 h-6"></i>';
      if (window.lucide) lucide.createIcons();
    });
  }

  // Quick tag buttons fill the business type input
  document.querySelectorAll(".quickTagBtn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById("businessTypeInput");
      if (input) input.value = btn.dataset.tag;
    });
  });

  // Analyze form: show a spinner + disable while the free LLM call runs server-side
  const analyzeForm = document.getElementById("analyzeForm");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const analyzeBtnText = document.getElementById("analyzeBtnText");
  if (analyzeForm && analyzeBtn) {
    analyzeForm.addEventListener("submit", () => {
      analyzeBtn.disabled = true;
      analyzeBtn.classList.add("bg-slate-100", "text-slate-400", "cursor-not-allowed");
      analyzeBtn.classList.remove("bg-brand-600", "text-white", "hover:bg-brand-700");
      analyzeBtnText.innerHTML =
        '<div class="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div> Analyzing Market & Compliance...';
    });
  }
});
