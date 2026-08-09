export function mountPostSearch(root) {
  const input = root.querySelector("[data-post-search]");
  if (!input) return;
  const items = [...root.querySelectorAll("[data-post-item]")];
  const years = [...root.querySelectorAll("[data-post-year].post-year")];
  const count = root.querySelector("[data-post-count]");
  const empty = root.querySelector("[data-search-empty]");
  const status = root.querySelector("[data-search-status]");
  const noResults = empty?.textContent ?? "";

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    const visibleYears = new Set();
    let visible = 0;
    for (const item of items) {
      const matches = item.dataset.postTitle.toLowerCase().includes(query);
      item.hidden = !matches;
      if (matches) {
        visible += 1;
        visibleYears.add(item.dataset.postYear);
      }
    }
    for (const year of years) year.hidden = !visibleYears.has(year.dataset.postYear);
    if (empty) empty.hidden = query === "" || visible !== 0;
    const template = visible === 1 ? root.dataset.countOne : root.dataset.countMany;
    const countText = template.replace("{count}", String(visible));
    if (count) count.textContent = countText;
    if (status) {
      status.textContent = query !== "" && visible === 0 ? noResults : countText;
    }
  });
}

if (typeof document !== "undefined") {
  for (const root of document.querySelectorAll("[data-post-list]")) {
    mountPostSearch(root);
  }
}
