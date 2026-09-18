window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["$$", "$$"], ["\\[", "\\]"]],
  },
  options: { skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"] },
};

const SITE = {
  name: "Geospatial Proximity Engine",
  subtitle: "Network-distance classification on directed graphs",
  author: "Abrahim Borgi · Senior Business Analyst",
  footer: "Geospatial Proximity Engine",
  sections: [
    {
      id: "introduction",
      title: "Introduction",
      items: [{
        label: "Problem framing",
        href: "introduction.html",
        page: "introduction",
        desc: "Classify targets by routed proximity to sources.",
      }],
    },
    {
      id: "theory",
      title: "Theory",
      items: [{
        label: "Graph model & pruning",
        href: "theory.html",
        page: "theory",
        desc: "Directed distance, a lower bound and the triangle inequality.",
      }],
    },
    {
      id: "solution",
      title: "Solution",
      items: [{
        label: "Four-step algorithm",
        href: "solution.html",
        page: "solution",
        desc: "Screen, route, filter and aggregate.",
      }],
    },
    {
      id: "implementation",
      title: "Implementation",
      items: [{
        label: "Python & OSRM",
        href: "implementation.html",
        page: "implementation",
        desc: "NumPy matrices, OSRM tables and reproducible outputs.",
      }],
    },
    {
      id: "applications",
      title: "Applications",
      items: [{
        label: "Lead and site classification",
        href: "applications.html",
        page: "applications",
        desc: "Addresses, comparable stores and weighted lead potential.",
      }],
    },
    {
      id: "poster",
      title: "Poster",
      items: [{
        label: "Conference poster",
        href: "poster.html",
        page: "poster",
        desc: "A concise visual summary of the method and its applications.",
      }],
    },
  ],
};

const SECTION_STATE_KEY = "geospatial-proximity-sidebar-sections";

function currentPage() {
  return document.body.dataset.page || "home";
}

function sectionIsOpen(section, state) {
  if (Object.hasOwn(state, section.id)) return Boolean(state[section.id]);
  return section.items.some((item) => item.page === currentPage());
}

function readState() {
  try {
    return JSON.parse(localStorage.getItem(SECTION_STATE_KEY) || "{}");
  } catch {
    return {};
  }
}

function renderSidebar() {
  const sidebar = document.querySelector("[data-sidebar]");
  if (!sidebar) return;

  const state = readState();
  const activePage = currentPage();
  const sections = SITE.sections.map((section) => {
    const open = sectionIsOpen(section, state);
    const active = section.items.some((item) => item.page === activePage);
    const links = section.items.map((item) => `
      <a class="nav-link ${item.page === activePage ? "active" : ""}" href="${item.href}">
        <div class="nav-dot"></div>
        <div class="nav-body">
          <div class="nav-title">${item.label}</div>
          <div class="nav-desc">${item.desc}</div>
        </div>
      </a>`).join("");
    return `
      <div class="section-block ${open ? "is-open" : ""}">
        <div class="section-heading">
          <a class="section-link ${active ? "active" : ""}" href="${section.items[0].href}">${section.title}</a>
          <button class="section-toggle" type="button" data-section-toggle="${section.id}" aria-label="Toggle ${section.title}" aria-expanded="${open}">
            <span class="section-chevron" aria-hidden="true"></span>
          </button>
        </div>
        <div class="nav-group" ${open ? "" : "hidden"}>${links}</div>
      </div>`;
  }).join("");

  sidebar.innerHTML = `
    <div class="sidebar-top">
      <a class="brand brand-link" href="index.html">
        <div class="brand-name">${SITE.name}</div>
        <div class="brand-tag">${SITE.subtitle}</div>
      </a>
    </div>${sections}`;

  sidebar.querySelectorAll("[data-section-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const nextState = readState();
      const id = button.dataset.sectionToggle;
      nextState[id] = button.getAttribute("aria-expanded") !== "true";
      localStorage.setItem(SECTION_STATE_KEY, JSON.stringify(nextState));
      renderSidebar();
    });
  });
}

function renderTopbar() {
  const topbar = document.querySelector("[data-topbar]");
  if (!topbar) return;
  topbar.innerHTML = `
    <div class="topbar-title">
      <h1>${document.body.dataset.pageTitle || SITE.name}</h1>
      <p>${document.body.dataset.pageSubtitle || ""}</p>
      <p>${SITE.author}</p>
    </div>
    <div class="topbar-actions">
      <button class="icon-button" type="button" data-sidebar-toggle>Menu</button>
      <img class="topbar-logo" src="assets/logo.png" alt="Project logo">
    </div>`;
}

function renderFooter() {
  const footer = document.querySelector("[data-footer]");
  if (footer) footer.textContent = `${SITE.footer} · ${SITE.author} · ${new Date().getFullYear()}`;
}

function wireEvents() {
  document.querySelector("[data-sidebar-toggle]")?.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 980px)").matches) {
      document.body.dataset.sidebarOpen = document.body.dataset.sidebarOpen === "true" ? "false" : "true";
      return;
    }
    const collapsed = document.body.dataset.sidebarCollapsed === "true";
    document.body.dataset.sidebarCollapsed = collapsed ? "false" : "true";
  });
}

function loadMathJax() {
  const script = document.createElement("script");
  script.async = true;
  script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js";
  document.head.appendChild(script);
}

document.addEventListener("DOMContentLoaded", () => {
  renderSidebar();
  renderTopbar();
  renderFooter();
  wireEvents();
  loadMathJax();
});
