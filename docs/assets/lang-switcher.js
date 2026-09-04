(() => {
  const supported = [
    ["en", "English"],
    ["cs", "Čeština"],
    ["de", "Deutsch"],
    ["fr", "Français"],
    ["es", "Español"]
  ];

  const scriptUrl = document.currentScript?.src;
  const projectRoot = scriptUrl
    ? new URL("../", scriptUrl)
    : new URL("/closure-ethics-for-autonomous-ai-agents/", window.location.origin);
  const projectPath = projectRoot.pathname.endsWith("/")
    ? projectRoot.pathname
    : `${projectRoot.pathname}/`;

  const raw = window.location.pathname.startsWith(projectPath)
    ? window.location.pathname.slice(projectPath.length)
    : window.location.pathname.replace(/^\//, "");
  const parts = raw.split("/").filter(Boolean);

  let currentLang = "en";
  let page = "index.html";
  if (parts.length && ["cs", "de", "fr", "es"].includes(parts[0])) {
    currentLang = parts[0];
    page = parts[1] || "index.html";
  } else if (parts.length) {
    page = parts[0];
  }

  // Keep the comparative-positioning page discoverable from every site page
  // without duplicating navigation markup across all canonical HTML sources.
  const comparisonLabels = {
    en: "Comparison",
    cs: "Srovnání",
    de: "Vergleich",
    fr: "Comparaison",
    es: "Comparación"
  };
  const navLinks = document.querySelector(".site-header .nav-links");
  if (navLinks && !navLinks.querySelector('a[href="comparison.html"]')) {
    const link = document.createElement("a");
    link.href = "comparison.html";
    link.textContent = comparisonLabels[currentLang] || "Comparison";
    if (page === "comparison.html") link.setAttribute("aria-current", "page");
    const implementation = navLinks.querySelector('a[href="implementation.html"]');
    if (implementation) implementation.insertAdjacentElement("afterend", link);
    else navLinks.appendChild(link);
  }

  const targetFor = (lang) => {
    const relative = lang === "en"
      ? (page === "index.html" ? "" : page)
      : `${lang}/${page}`;
    const target = new URL(relative, projectRoot);
    target.search = window.location.search;
    target.hash = window.location.hash;
    return target.href;
  };

  const nav = document.querySelector(".site-header .nav");
  if (!nav) return;

  const wrap = document.createElement("div");
  wrap.className = "language-switcher";

  const label = document.createElement("label");
  label.setAttribute("for", "closure-lang");
  label.textContent = "Language";

  const select = document.createElement("select");
  select.id = "closure-lang";
  select.setAttribute("aria-label", "Language");

  for (const [code, name] of supported) {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = name;
    option.selected = code === currentLang;
    select.appendChild(option);
  }

  select.addEventListener("change", () => {
    window.location.assign(targetFor(select.value));
  });

  wrap.append(label, select);
  nav.appendChild(wrap);
})();
