/* BOSS pricing guide: hash routing (#/page), ES/EN, search, lightbox. No external libraries. */
(function () {
  "use strict";
  const pages = (window.GUIDE_PAGES || []).concat(window.GUIDE_SERVICE_PAGES || []);
  const sections = window.GUIDE_SECTIONS || [];
  const byId = Object.fromEntries(pages.map((p) => [p.id, p]));
  const UI = {
    es: { search: "Buscar en la guía…", prev: "Anterior", next: "Siguiente", results: "Resultados", none: "Sin resultados", lang: "English", notFound: "Página no encontrada" },
    en: { search: "Search the guide…", prev: "Previous", next: "Next", results: "Results", none: "No results", lang: "Español", notFound: "Page not found" },
  };
  let lang = new URLSearchParams(location.search).get("lang") || localStorage.getItem("boss-guide-lang") || "es";
  if (!UI[lang]) lang = "es";

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fold = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const t = (v) => (v && typeof v === "object" ? v[lang] || v.es || "" : v || "");

  function inline(s) {
    return esc(s)
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="shot" loading="lazy">')
      .replace(/\[([^\]]+)\]\((#\/[^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\[\[([^\]]+)\]\]/g, '<span class="btnref">$1</span>');
  }

  function render(md) {
    const lines = md.replace(/\r/g, "").split("\n");
    let html = "", i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) { i++; continue; }
      let m;
      if ((m = line.match(/^(#{2,4})\s+(.*)/))) { html += `<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`; i++; continue; }
      if (line.startsWith("|")) {
        const rows = [];
        while (i < lines.length && lines[i].startsWith("|")) rows.push(lines[i++]);
        const cells = (r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        const body = rows.filter((r, k) => !(k === 1 && /^\|[\s:|-]+\|?$/.test(r)));
        html += '<div class="tablewrap"><table><thead><tr>' + cells(body[0]).map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>";
        html += body.slice(1).map((r) => "<tr>" + cells(r).map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>").join("");
        html += "</tbody></table></div>";
        continue;
      }
      const item = (marker) => {  // list item text plus its indented continuation lines
        let text = lines[i++].replace(marker, "");
        while (i < lines.length && /^\s+\S/.test(lines[i]) && !/^\s*([-*]|\d+\.) /.test(lines[i])) text += " " + lines[i++].trim();
        return `<li>${inline(text)}</li>`;
      };
      if (/^\s*[-*] /.test(line)) {
        html += "<ul>";
        while (i < lines.length && /^\s*[-*] /.test(lines[i])) html += item(/^\s*[-*] /);
        html += "</ul>"; continue;
      }
      if (/^\d+\. /.test(line)) {
        html += `<ol start="${parseInt(line, 10)}">`;
        while (i < lines.length && /^\d+\. /.test(lines[i])) html += item(/^\d+\. /);
        html += "</ol>"; continue;
      }
      if (line.startsWith("> ")) {
        let q = "";
        while (i < lines.length && lines[i].startsWith("> ")) q += lines[i++].slice(2) + " ";
        html += `<div class="note">${inline(q)}</div>`; continue;
      }
      let p = "";
      while (i < lines.length && lines[i].trim() && !/^(#{2,4}\s|\||\s*[-*] |\d+\. |> )/.test(lines[i])) p += lines[i++] + " ";
      html += `<p>${inline(p.trim())}</p>`;
    }
    return html;
  }

  function nav() {
    const current = (location.hash.match(/^#\/([^?]+)/) || [])[1] || pages[0].id;
    const box = document.getElementById("nav");
    box.innerHTML = sections.map((s) => {
      const items = pages.filter((p) => p.section === s.id);
      const open = items.some((p) => p.id === current) ? " open" : "";
      return `<details${open}><summary>${esc(t(s.title))}</summary><ul>` +
        items.map((p) => `<li><a href="#/${p.id}" class="${p.id === current ? "active" : ""}">${esc(t(p.title))}</a></li>`).join("") +
        "</ul></details>";
    }).join("");
  }

  function show() {
    const id = (location.hash.match(/^#\/([^?]+)/) || [])[1] || pages[0].id;
    const page = byId[id];
    const main = document.getElementById("content");
    document.documentElement.lang = lang;
    document.getElementById("search").placeholder = UI[lang].search;
    document.getElementById("lang").textContent = UI[lang].lang;
    if (!page) { main.innerHTML = `<h1>${UI[lang].notFound}</h1>`; nav(); return; }
    const idx = pages.indexOf(page);
    const prev = pages[idx - 1], next = pages[idx + 1];
    main.innerHTML = `<h1>${esc(t(page.title))}</h1>` + render(t(page.body)) +
      '<div class="pager">' +
      (prev ? `<a href="#/${prev.id}">← ${esc(t(prev.title))}</a>` : "<span></span>") +
      (next ? `<a href="#/${next.id}">${esc(t(next.title))} →</a>` : "<span></span>") + "</div>";
    document.title = `${t(page.title)} · BOSS`;
    main.querySelectorAll("img.shot").forEach((img) => img.addEventListener("click", () => {
      const lb = document.getElementById("lightbox"); lb.querySelector("img").src = img.src; lb.hidden = false;
    }));
    nav();
    window.scrollTo(0, 0);
  }

  function search(q) {
    const box = document.getElementById("results");
    const words = fold(q).split(/\s+/).filter((w) => w.length > 1);
    if (!words.length) { box.hidden = true; return; }
    const hits = pages.map((p) => {
      const title = fold(t(p.title)), body = fold(t(p.body));
      if (!words.every((w) => title.includes(w) || body.includes(w))) return null;
      return { p, score: words.reduce((s, w) => s + (title.includes(w) ? 10 : 0) + (body.split(w).length - 1), 0) };
    }).filter(Boolean).sort((a, b) => b.score - a.score).slice(0, 15);
    box.innerHTML = `<strong>${UI[lang].results}</strong>` + (hits.length ? "<ul>" + hits.map((h) => `<li><a href="#/${h.p.id}">${esc(t(h.p.title))}</a></li>`).join("") + "</ul>" : `<p>${UI[lang].none}</p>`);
    box.hidden = false;
  }

  document.getElementById("lang").addEventListener("click", () => {
    lang = lang === "es" ? "en" : "es"; localStorage.setItem("boss-guide-lang", lang); show();
    search(document.getElementById("search").value);
  });
  document.getElementById("search").addEventListener("input", (e) => search(e.target.value));
  document.getElementById("results").addEventListener("click", (e) => { if (e.target.tagName === "A") e.currentTarget.hidden = true; });
  document.getElementById("lightbox").addEventListener("click", (e) => { e.currentTarget.hidden = true; });
  document.getElementById("menu").addEventListener("click", (e) => {
    e.currentTarget.setAttribute("aria-expanded", document.body.classList.toggle("nav-open"));
  });
  window.addEventListener("hashchange", () => { document.body.classList.remove("nav-open"); show(); });
  show();
})();
