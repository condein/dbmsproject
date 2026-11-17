// Small progressive enhancements: animated counters, profile ring, flash timeout.
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.querySelectorAll("[data-count]").forEach((el) => {
  const target = Number(el.dataset.count);
  const decimals = Number(el.dataset.decimals || 0);
  if (!Number.isFinite(target) || reduceMotion) return;

  const started = performance.now();
  const duration = 900;
  const tick = (now) => {
    const progress = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = (target * eased).toFixed(decimals);
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
});

document.querySelectorAll("[data-ring]").forEach((el) => {
  const value = Number(el.dataset.ring) || 0;
  if (reduceMotion) {
    el.style.setProperty("--value", value);
    return;
  }
  requestAnimationFrame(() => el.style.setProperty("--value", value));
});

document.querySelectorAll(".flash").forEach((el) => {
  window.setTimeout(() => el.classList.add("is-hidden"), 6000);
});
