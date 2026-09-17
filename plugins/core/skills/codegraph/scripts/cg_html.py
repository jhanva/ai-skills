"""
cg_html.py — Exporta graph.html: visualizacion interactiva autocontenida.

Force-directed layout en canvas con vanilla JS. Sin CDN, sin dependencias:
funciona offline abriendo el archivo en cualquier browser.

Features: zoom/pan, drag de nodos, busqueda, tooltip, filtro por confianza,
colores por comunidad, leyenda con labels de comunidades.
"""

import json

_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>codegraph - __TITLE__</title>
<style>
  :root { color-scheme: dark; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #10131a; color: #d5dae3; font: 13px/1.4 system-ui, sans-serif; overflow: hidden; }
  #graph { display: block; cursor: grab; }
  #graph.dragging { cursor: grabbing; }
  #panel {
    position: fixed; top: 12px; left: 12px; width: 280px;
    background: rgba(18, 22, 30, .92); border: 1px solid #2a3040;
    border-radius: 10px; padding: 14px; backdrop-filter: blur(6px);
  }
  #panel h1 { font-size: 15px; margin-bottom: 2px; }
  #panel .sub { color: #7d8595; font-size: 11px; margin-bottom: 10px; }
  #search {
    width: 100%; padding: 6px 9px; border-radius: 6px;
    border: 1px solid #2a3040; background: #0c0f15; color: #d5dae3;
    font-size: 12px; outline: none;
  }
  #search:focus { border-color: #4a6cf7; }
  .filters { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
  .chip {
    padding: 3px 9px; border-radius: 999px; font-size: 11px;
    border: 1px solid #2a3040; cursor: pointer; user-select: none;
  }
  .chip.on { border-color: #4a6cf7; background: rgba(74, 108, 247, .18); }
  #legend { margin-top: 12px; max-height: 40vh; overflow-y: auto; }
  #legend div { display: flex; align-items: center; gap: 7px; padding: 2px 0;
    font-size: 11.5px; cursor: pointer; }
  #legend div.dim { opacity: .35; }
  #legend span.dot { width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0; }
  #tooltip {
    position: fixed; pointer-events: none; display: none; max-width: 340px;
    background: #171c26; border: 1px solid #333c50; border-radius: 8px;
    padding: 9px 11px; font-size: 12px; z-index: 10;
  }
  #tooltip .t-label { font-weight: 600; margin-bottom: 3px; }
  #tooltip .t-meta { color: #8a93a5; font-size: 11px; }
  #stats { position: fixed; bottom: 10px; right: 14px; color: #5d6575;
    font-size: 11px; }
</style>
</head>
<body>
<canvas id="graph"></canvas>
<div id="panel">
  <h1>__TITLE__</h1>
  <div class="sub">__SUBTITLE__</div>
  <input id="search" placeholder="Buscar nodo..." autocomplete="off">
  <div class="filters">
    <span class="chip on" data-conf="EXTRACTED">EXTRACTED</span>
    <span class="chip on" data-conf="INFERRED">INFERRED</span>
    <span class="chip on" data-conf="AMBIGUOUS">AMBIGUOUS</span>
  </div>
  <div id="legend"></div>
</div>
<div id="tooltip"></div>
<div id="stats"></div>
<script>
const DATA = __DATA__;
const PALETTE = ["#4a6cf7","#e05263","#3fb68b","#e0a542","#9a6cf7",
  "#42b8e0","#e06cb0","#8ab63f","#f77a4a","#6c8af7","#42e0a5","#c9525e",
  "#7d9c3f","#b342e0","#e0d142","#4ae0d4"];

const canvas = document.getElementById("graph");
const ctx = canvas.getContext("2d");
let W, H, dpr = window.devicePixelRatio || 1;
function resize() {
  W = innerWidth; H = innerHeight;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + "px"; canvas.style.height = H + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
resize(); addEventListener("resize", resize);

// --- estado ---
const nodes = DATA.nodes.map((n, i) => ({
  ...n, idx: i,
  x: W / 2 + Math.cos(i * 2.399963) * (40 + Math.sqrt(i) * 22),
  y: H / 2 + Math.sin(i * 2.399963) * (40 + Math.sqrt(i) * 22),
  vx: 0, vy: 0, deg: 0,
}));
const byId = {}; nodes.forEach(n => byId[n.id] = n);
const links = DATA.links.filter(l => byId[l.source] && byId[l.target]);
links.forEach(l => { byId[l.source].deg++; byId[l.target].deg++; });
nodes.forEach(n => n.r = 3 + Math.min(11, Math.sqrt(n.deg) * 1.7));

const confOn = { EXTRACTED: true, INFERRED: true, AMBIGUOUS: true };
const commOn = {};
(DATA.communities || []).forEach(c => commOn[c.id] = true);
let query = "", hoverNode = null, dragNode = null;
let tx = 0, ty = 0, scale = 1;
let panStart = null;

// --- fisica: fuerza de resortes + repulsion aproximada por grilla ---
let alpha = 1;
let rafRunning = false;
function step() {
  alpha *= 0.985;
  const k = 0.035;
  // repulsion via grilla espacial (aprox O(n))
  const cell = 90, grid = new Map();
  for (const n of nodes) {
    const key = ((n.x / cell) | 0) + ":" + ((n.y / cell) | 0);
    if (!grid.has(key)) grid.set(key, []);
    grid.get(key).push(n);
  }
  for (const n of nodes) {
    const cx = (n.x / cell) | 0, cy = (n.y / cell) | 0;
    for (let gx = cx - 1; gx <= cx + 1; gx++)
      for (let gy = cy - 1; gy <= cy + 1; gy++) {
        const bucket = grid.get(gx + ":" + gy);
        if (!bucket) continue;
        for (const m of bucket) {
          if (m === n) continue;
          let dx = n.x - m.x, dy = n.y - m.y;
          let d2 = dx * dx + dy * dy || 1;
          if (d2 > cell * cell) continue;
          const f = 900 / d2 * alpha;
          n.vx += dx * f; n.vy += dy * f;
        }
      }
    // gravedad al centro
    n.vx += (W / 2 - n.x) * 0.0012 * alpha;
    n.vy += (H / 2 - n.y) * 0.0012 * alpha;
  }
  // atraccion al centroide de la comunidad (agrupa visualmente clusters)
  const cent = {};
  for (const n of nodes) {
    const c = cent[n.community] || (cent[n.community] = [0, 0, 0]);
    c[0] += n.x; c[1] += n.y; c[2]++;
  }
  for (const n of nodes) {
    const c = cent[n.community];
    if (c[2] < 2) continue;
    n.vx += (c[0] / c[2] - n.x) * 0.05 * alpha;
    n.vy += (c[1] / c[2] - n.y) * 0.05 * alpha;
  }
  for (const l of links) {
    const a = byId[l.source], b = byId[l.target];
    let dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx * dx + dy * dy) || 1;
    const target = (a.community === b.community ? 45 : 110) + (a.r + b.r);
    const f = (d - target) * k * alpha;
    dx /= d; dy /= d;
    a.vx += dx * f; a.vy += dy * f;
    b.vx -= dx * f; b.vy -= dy * f;
  }
  for (const n of nodes) {
    if (n === dragNode) { n.vx = 0; n.vy = 0; continue; }
    n.x += n.vx; n.y += n.vy;
    n.vx *= 0.6; n.vy *= 0.6;
  }
}
function tick() {
  // loop de animacion unico (solo para interaccion post-carga)
  if (rafRunning) return;
  rafRunning = true;
  const loop = () => {
    if (alpha < 0.005) { rafRunning = false; return; }
    step(); draw();
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}

function nodeVisible(n) {
  if (commOn[n.community] === false) return false;
  if (query && !n.label.toLowerCase().includes(query)) return false;
  return true;
}
function linkVisible(l) {
  return confOn[l.confidence] !== false &&
    nodeVisible(byId[l.source]) && nodeVisible(byId[l.target]);
}

function draw() {
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(tx, ty); ctx.scale(scale, scale);
  // edges
  for (const l of links) {
    if (!linkVisible(l)) continue;
    const a = byId[l.source], b = byId[l.target];
    ctx.beginPath();
    ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
    if (l.confidence === "EXTRACTED") {
      ctx.strokeStyle = "rgba(140,155,180,.28)"; ctx.setLineDash([]);
    } else if (l.confidence === "INFERRED") {
      ctx.strokeStyle = "rgba(120,170,247,.30)"; ctx.setLineDash([4, 3]);
    } else {
      ctx.strokeStyle = "rgba(224,82,99,.35)"; ctx.setLineDash([2, 3]);
    }
    ctx.lineWidth = 1 / scale;
    ctx.stroke();
  }
  ctx.setLineDash([]);
  // nodes
  const showLabels = scale > 0.7;
  for (const n of nodes) {
    if (!nodeVisible(n)) continue;
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, 6.2832);
    ctx.fillStyle = PALETTE[n.community % PALETTE.length];
    ctx.globalAlpha = query && !n.label.toLowerCase().includes(query) ? .15 : 1;
    ctx.fill();
    ctx.globalAlpha = 1;
    if (n === hoverNode) {
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 2 / scale; ctx.stroke();
    }
    if (showLabels && (n.deg >= 3 || scale > 1.6 || n === hoverNode ||
        (query && n.label.toLowerCase().includes(query)))) {
      ctx.fillStyle = "rgba(213,218,227,.85)";
      ctx.font = (11 / scale) + "px system-ui";
      ctx.fillText(n.label, n.x + n.r + 3, n.y + 3);
    }
  }
  ctx.restore();
}

// --- interaccion ---
function toWorld(px, py) { return [(px - tx) / scale, (py - ty) / scale]; }
function pick(px, py) {
  const [x, y] = toWorld(px, py);
  let best = null, bestD = 144;
  for (const n of nodes) {
    if (!nodeVisible(n)) continue;
    const dx = n.x - x, dy = n.y - y, d = dx * dx + dy * dy;
    if (d < bestD + n.r * n.r) { best = n; bestD = d; }
  }
  return best;
}
canvas.addEventListener("mousedown", e => {
  const n = pick(e.clientX, e.clientY);
  if (n) { dragNode = n; alpha = Math.max(alpha, 0.1); tick(); }
  else panStart = [e.clientX - tx, e.clientY - ty];
  canvas.classList.add("dragging");
});
addEventListener("mousemove", e => {
  if (dragNode) {
    const [x, y] = toWorld(e.clientX, e.clientY);
    dragNode.x = x; dragNode.y = y;
    alpha = Math.max(alpha, 0.06); tick(); draw();
    return;
  }
  if (panStart) {
    tx = e.clientX - panStart[0]; ty = e.clientY - panStart[1];
    draw(); return;
  }
  const n = pick(e.clientX, e.clientY);
  if (n !== hoverNode) { hoverNode = n; draw(); }
  const tip = document.getElementById("tooltip");
  if (n) {
    tip.style.display = "block";
    tip.style.left = (e.clientX + 14) + "px";
    tip.style.top = (e.clientY + 14) + "px";
    const comm = (DATA.communities || []).find(c => c.id === n.community);
    tip.innerHTML = '<div class="t-label">' + esc(n.label) + '</div>' +
      '<div class="t-meta">' + esc(n.kind || "?") + " · " +
      esc(n.source_file || "externo") +
      (n.source_location ? " " + esc(n.source_location) : "") +
      "<br>grado " + n.deg + " · " +
      esc(comm ? comm.label : "comunidad " + n.community) + "</div>";
  } else tip.style.display = "none";
});
addEventListener("mouseup", () => {
  dragNode = null; panStart = null;
  canvas.classList.remove("dragging");
});
canvas.addEventListener("wheel", e => {
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.12 : 0.89;
  const [wx, wy] = toWorld(e.clientX, e.clientY);
  scale = Math.min(6, Math.max(0.15, scale * f));
  tx = e.clientX - wx * scale; ty = e.clientY - wy * scale;
  draw();
}, { passive: false });

function esc(s) {
  return String(s).replace(/[&<>"]/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// --- panel ---
document.getElementById("search").addEventListener("input", e => {
  query = e.target.value.trim().toLowerCase(); draw();
});
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const c = chip.dataset.conf;
    confOn[c] = !confOn[c];
    chip.classList.toggle("on", confOn[c]);
    draw();
  });
});
const legend = document.getElementById("legend");
(DATA.communities || []).forEach(c => {
  const row = document.createElement("div");
  row.innerHTML = '<span class="dot" style="background:' +
    PALETTE[c.id % PALETTE.length] + '"></span>' +
    esc(c.label) + " (" + c.size + ")";
  row.addEventListener("click", () => {
    commOn[c.id] = !commOn[c.id];
    row.classList.toggle("dim", !commOn[c.id]);
    draw();
  });
  legend.appendChild(row);
});
document.getElementById("stats").textContent =
  nodes.length + " nodos · " + links.length + " edges · " +
  (DATA.communities || []).length + " comunidades";

// layout inicial sincrono: no depende de requestAnimationFrame (que los
// browsers pausan en tabs de fondo). Iteraciones segun tamano del grafo.
const warmup = nodes.length > 1500 ? 120 : nodes.length > 400 ? 200 : 300;
for (let i = 0; i < warmup; i++) step();
alpha = 0.004; // reposo; la interaccion lo reactiva via tick()
draw();
</script>
</body>
</html>
"""


def render_html(title, subtitle, nodes, links, communities):
    """Genera el HTML autocontenido. communities: [{id, label, size}]."""
    slim_nodes = [{
        "id": n["id"], "label": n["label"], "kind": n.get("kind"),
        "source_file": n.get("source_file"),
        "source_location": n.get("source_location"),
        "community": n.get("community", 0),
    } for n in nodes]
    slim_links = [{
        "source": e["source"], "target": e["target"],
        "relation": e["relation"], "confidence": e["confidence"],
    } for e in links]
    data = json.dumps(
        {"nodes": slim_nodes, "links": slim_links,
         "communities": communities},
        ensure_ascii=False, separators=(",", ":"))
    html = _TEMPLATE.replace("__TITLE__", _esc(title))
    html = html.replace("__SUBTITLE__", _esc(subtitle))
    html = html.replace("__DATA__", data.replace("</", "<\\/"))
    return html


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))
