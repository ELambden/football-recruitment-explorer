const INKS = [
  { color: "#0088b0", fill: "rgba(0,136,176,.30)" },
  { color: "#d6006c", fill: "rgba(214,0,108,.28)" },
  { color: "#a07f00", fill: "rgba(237,187,0,.42)" },
  { color: "#201e1d", fill: "rgba(32,30,29,.22)" },
];

const ZONES = [
  { g: "Centre Forward", abbr: "CF", x: 45, y: 16, w: 110, h: 58 },
  { g: "Attacking Midfielder / Winger", abbr: "AM", x: 45, y: 78, w: 110, h: 44 },
  { g: "Attacking Midfielder / Winger", abbr: "W", x: 6, y: 78, w: 35, h: 92 },
  { g: "Attacking Midfielder / Winger", abbr: "W", x: 159, y: 78, w: 35, h: 92 },
  { g: "Central Midfielder", abbr: "CM", x: 45, y: 126, w: 110, h: 44 },
  { g: "Defensive Midfielder", abbr: "DM", x: 45, y: 174, w: 110, h: 44 },
  { g: "Full Back / Wing Back", abbr: "FB", x: 6, y: 174, w: 35, h: 92 },
  { g: "Full Back / Wing Back", abbr: "FB", x: 159, y: 174, w: 35, h: 92 },
  { g: "Centre Back", abbr: "CB", x: 45, y: 222, w: 110, h: 44 },
  { g: "Goalkeeper", abbr: "GK", x: 70, y: 270, w: 60, h: 30 },
];

const ROLE_SHORT = {
  "Centre Forward": "centre forwards",
  "Attacking Midfielder / Winger": "attacking midfielders and wingers",
  "Central Midfielder": "central midfielders",
  "Defensive Midfielder": "defensive midfielders",
  "Full Back / Wing Back": "full backs and wing backs",
  "Centre Back": "centre backs",
  "Goalkeeper": "goalkeepers",
  "Other": "other roles",
  "All": "all roles",
};

const state = {
  ready: false,
  players: [],
  metrics: [],
  metricById: new Map(),
  rolePresets: {},
  caseStudy: null,
  caseCandidateId: null,
  role: "Centre Forward",
  competition: "All",
  team: "All",
  minMinutes: 900,
  search: "",
  metricIds: [],
  pinned: [],
  xMetric: "non_penalty_xg_p90",
  yMetric: "xg_assisted_p90",
  sortKey: "min",
  sortDirection: "desc",
};

const els = {
  caseTitle: document.getElementById("caseTitle"),
  caseQuestion: document.getElementById("caseQuestion"),
  caseStats: document.getElementById("caseStats"),
  caseShortlist: document.getElementById("caseShortlist"),
  caseDeltaTitle: document.getElementById("caseDeltaTitle"),
  deltaHeatmap: document.getElementById("deltaHeatmap"),
  validationSummary: document.getElementById("validationSummary"),
  pitchSelector: document.getElementById("pitchSelector"),
  allRoles: document.getElementById("allRoles"),
  otherRole: document.getElementById("otherRole"),
  cohortNote: document.getElementById("cohortNote"),
  competitionChips: document.getElementById("competitionChips"),
  teamFilter: document.getElementById("teamFilter"),
  searchFilter: document.getElementById("searchFilter"),
  minutesFilter: document.getElementById("minutesFilter"),
  minutesValue: document.getElementById("minutesValue"),
  metricCount: document.getElementById("metricCount"),
  resetMetrics: document.getElementById("resetMetrics"),
  metricChips: document.getElementById("metricChips"),
  shareState: document.getElementById("shareState"),
  compareTray: document.getElementById("compareTray"),
  radarChart: document.getElementById("radarChart"),
  percentileStrips: document.getElementById("percentileStrips"),
  invertedNote: document.getElementById("invertedNote"),
  xMetric: document.getElementById("xMetric"),
  yMetric: document.getElementById("yMetric"),
  scatterChart: document.getElementById("scatterChart"),
  nearestNote: document.getElementById("nearestNote"),
  nearestProfiles: document.getElementById("nearestProfiles"),
  tableCount: document.getElementById("tableCount"),
  table: document.getElementById("candidateTable"),
};

function versioned(path) {
  const version = window.DASHBOARD_ASSET_VERSION || "dev";
  return `${path}${path.includes("?") ? "&" : "?"}v=${encodeURIComponent(version)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function fmt(value, format = ".1f") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const digits = { ".3f": 3, ".2f": 2, ".1f": 1, ".0f": 0 }[format] ?? 1;
  return Number(value).toFixed(digits);
}

function normalizePlayers(payload) {
  if (payload.players.length && payload.players[0].n) return payload.players;
  return payload.players.map((p) => ({
    id: `${p.competitionName}|${p.seasonName}|${p.playerId}`,
    n: p.playerName,
    t: p.teamName,
    c: p.competitionName,
    g: p.positionGroup,
    sh: p.positionShare,
    min: p.minutes,
    m: p.matches,
    st: p.starts,
    v: p.metrics,
    p: p.percentiles,
  }));
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function playerIdFromCase(player) {
  return `${player.competitionName}|${player.seasonName}|${player.playerId}`;
}

function readHash() {
  const raw = (location.hash || "").replace(/^#/, "");
  if (!raw) return;
  const q = new URLSearchParams(raw);
  if (q.get("role")) state.role = q.get("role");
  if (q.get("comp")) state.competition = q.get("comp");
  if (q.get("team")) state.team = q.get("team");
  if (q.get("min")) state.minMinutes = Number(q.get("min"));
  if (q.get("q")) state.search = q.get("q");
  if (q.get("m")) {
    const ids = q.get("m").split(",").filter((id) => state.metricById.has(id));
    if (ids.length) state.metricIds = ids;
  }
  if (q.get("p")) state.pinned = q.get("p").split("~").filter(Boolean);
  if (q.get("x") && state.metricById.has(q.get("x"))) state.xMetric = q.get("x");
  if (q.get("y") && state.metricById.has(q.get("y"))) state.yMetric = q.get("y");
}

function writeHash() {
  const q = new URLSearchParams();
  q.set("role", state.role);
  if (state.competition !== "All") q.set("comp", state.competition);
  if (state.team !== "All") q.set("team", state.team);
  q.set("min", String(state.minMinutes));
  if (state.search) q.set("q", state.search);
  q.set("m", state.metricIds.join(","));
  if (state.pinned.length) q.set("p", state.pinned.join("~"));
  q.set("x", state.xMetric);
  q.set("y", state.yMetric);
  const next = "#" + q.toString();
  if (location.hash !== next) history.replaceState(null, "", next);
}

function preset(role = state.role) {
  const key = role !== "All" ? role : "Centre Forward";
  return (state.rolePresets[key] || state.rolePresets["Centre Forward"] || []).filter((id) => state.metricById.has(id));
}

function filteredPlayers() {
  const q = state.search.trim().toLowerCase();
  return state.players.filter((p) =>
    (state.role === "All" || p.g === state.role) &&
    (state.competition === "All" || p.c === state.competition) &&
    (state.team === "All" || p.t === state.team) &&
    p.min >= state.minMinutes &&
    (!q || p.n.toLowerCase().includes(q))
  );
}

function setFilter(patch, resetMetrics = false) {
  Object.assign(state, patch);
  if (resetMetrics) state.metricIds = preset(state.role);
  state.pinned = state.pinned.filter((id, index, arr) => arr.indexOf(id) === index && state.players.some((p) => p.id === id)).slice(0, 4);
  if (!state.pinned.length) pickDefaults();
  render();
}

function pickDefaults() {
  state.pinned = filteredPlayers().slice().sort((a, b) => b.min - a.min).slice(0, 3).map((p) => p.id);
}

function togglePin(id) {
  const next = state.pinned.slice();
  const idx = next.indexOf(id);
  if (idx >= 0) next.splice(idx, 1);
  else if (next.length < 4) next.push(id);
  else next[3] = id;
  state.pinned = next;
  render();
}

function selectedPlayers() {
  const byId = new Map(state.players.map((p) => [p.id, p]));
  return state.pinned.map((id) => byId.get(id)).filter(Boolean).slice(0, 4);
}

function metricDefs() {
  return state.metricIds.map((id) => state.metricById.get(id)).filter(Boolean).slice(0, 12);
}

function renderCaseStudy() {
  const cs = state.caseStudy;
  if (!cs) return;
  const candidate = cs.candidates.find((c) => playerIdFromCase(c) === state.caseCandidateId) || cs.candidates[0];
  state.caseCandidateId = playerIdFromCase(candidate);
  els.caseTitle.textContent = cs.title;
  els.caseQuestion.textContent = cs.question;
  els.caseStats.innerHTML = [
    ["Benchmark", cs.benchmark.playerName],
    ["Cohort", `${cs.scope.cohortPlayers} CFs`],
    ["Minutes filter", `${fmt(cs.scope.minMinutes, ".0f")}+`],
    ["Role share", `${fmt(cs.scope.minPositionShare * 100, ".0f")}%+`],
  ].map(([label, value]) => `<div class="stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");

  els.caseShortlist.innerHTML = cs.candidates.slice(0, 6).map((c) => {
    const id = playerIdFromCase(c);
    const interval = c.rankInterval && c.rankInterval.lower !== null ? `${fmt(c.rankInterval.lower, ".0f")}-${fmt(c.rankInterval.upper, ".0f")}` : "-";
    return `<article class="candidate-card" data-id="${escapeHtml(id)}" data-on="${id === state.caseCandidateId ? "1" : "0"}">
      <div class="card-top"><div><div class="card-title">${escapeHtml(c.playerName)}</div><div class="card-meta">${escapeHtml(c.teamName)} | ${escapeHtml(c.competitionName)}</div></div><div class="score">#${fmt(c.similarityRank, ".0f")}<br>${fmt(c.similarityPercentile, ".1f")}%</div></div>
      <p class="card-meta">Rank interval ${escapeHtml(interval)} | ${escapeHtml(c.sensitivity.scenariosInTopN ?? "-")} scenarios in top 10</p>
      <p>${escapeHtml(c.note)}</p>
    </article>`;
  }).join("");
  els.caseShortlist.querySelectorAll(".candidate-card").forEach((el) => el.addEventListener("click", () => {
    state.caseCandidateId = el.dataset.id;
    if (!state.pinned.includes(el.dataset.id)) togglePin(el.dataset.id);
    renderCaseStudy();
  }));

  els.caseDeltaTitle.textContent = `${candidate.playerName} vs ${cs.benchmark.playerName}`;
  const maxAbs = Math.max(0.01, ...candidate.metricDeltas.map((d) => Math.abs(d.delta || 0)));
  els.deltaHeatmap.innerHTML = candidate.metricDeltas.map((d) => {
    const width = Math.max(2, Math.abs(d.delta || 0) / maxAbs * 50);
    const left = (d.delta || 0) >= 0 ? 50 : 50 - width;
    const cls = (d.delta || 0) < 0 ? "delta-bar negative" : "delta-bar";
    return `<div class="delta-row"><span>${escapeHtml(d.label)}</span><span class="num">${fmt(d.candidateValue, ".2f")}</span><span class="delta-track"><span class="delta-zero"></span><span class="${cls}" style="left:${left}%;width:${width}%"></span></span></div>`;
  }).join("");

  const rel = cs.validation.splitHalfReliability.slice().sort((a, b) => (b.correlation || 0) - (a.correlation || 0)).slice(0, 6);
  els.validationSummary.innerHTML = [
    `<div class="validation-card"><div class="card-title">${cs.validation.bootstrapIterations}</div><div class="card-meta">bootstrap iterations for rank intervals</div></div>`,
    `<div class="validation-card"><div class="card-title">${cs.validation.weightScenarios.length}</div><div class="card-meta">weight scenarios tested for shortlist stability</div></div>`,
    `<div class="validation-card"><div class="card-title">${fmt(rel[0]?.correlation, ".2f")}</div><div class="card-meta">best split-half reliability: ${escapeHtml(rel[0]?.label || "-")}</div></div>`,
  ].join("");
}

function renderPitch() {
  const counts = new Map();
  for (const p of state.players) {
    if ((state.competition === "All" || p.c === state.competition) && (state.team === "All" || p.t === state.team) && p.min >= state.minMinutes) {
      counts.set(p.g, (counts.get(p.g) || 0) + 1);
    }
  }
  const zones = ZONES.map((z, i) => {
    const on = state.role === z.g;
    const fill = on ? "var(--color-accent)" : "color-mix(in srgb, var(--color-text) 5%, transparent)";
    const textColor = on ? "var(--color-bg)" : "var(--color-text)";
    const count = z.w > 60 ? `<text x="${z.x + z.w / 2}" y="${z.y + z.h / 2 + 12}" text-anchor="middle" font-size="8.5" fill="${textColor}">${counts.get(z.g) || 0}</text>` : "";
    return `<g class="re-zone" data-role="${escapeHtml(z.g)}"><rect x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="1" fill="${fill}" stroke="rgba(32,30,29,.28)" stroke-width="${on ? 1.5 : 1}"></rect><text x="${z.x + z.w / 2}" y="${z.y + z.h / 2 + (z.w > 60 ? -1 : 4)}" text-anchor="middle" font-size="11" font-weight="600" fill="${textColor}">${z.abbr}</text>${count}</g>`;
  }).join("");
  els.pitchSelector.innerHTML = `<svg viewBox="0 0 200 306" role="group" aria-label="Position group selector"><rect x="2" y="2" width="196" height="302" fill="color-mix(in srgb, var(--color-accent) 5%, transparent)" stroke="rgba(32,30,29,.28)"></rect><line x1="2" y1="153" x2="198" y2="153" stroke="rgba(32,30,29,.28)"></line><circle cx="100" cy="153" r="30" fill="none" stroke="rgba(32,30,29,.2)"></circle><rect x="55" y="2" width="90" height="34" fill="none" stroke="rgba(32,30,29,.2)"></rect><rect x="55" y="270" width="90" height="34" fill="none" stroke="rgba(32,30,29,.2)"></rect>${zones}</svg>`;
  els.pitchSelector.querySelectorAll(".re-zone").forEach((el) => el.addEventListener("click", () => setFilter({ role: el.dataset.role, pinned: [] }, true)));
}

function renderControls() {
  const cohort = filteredPlayers();
  els.allRoles.dataset.on = state.role === "All" ? "1" : "0";
  els.otherRole.dataset.on = state.role === "Other" ? "1" : "0";
  els.cohortNote.textContent = `Showing ${cohort.length} ${ROLE_SHORT[state.role] || state.role}, ${state.minMinutes}+ minutes${state.competition === "All" ? ", all three leagues" : ", " + state.competition}.`;
  els.minutesValue.textContent = state.minMinutes;
  els.minutesFilter.value = state.minMinutes;
  els.searchFilter.value = state.search;

  const competitions = ["All", ...uniqueSorted(state.players.map((p) => p.c))];
  els.competitionChips.innerHTML = competitions.map((c) => `<button class="chip" type="button" data-comp="${escapeHtml(c)}" data-on="${state.competition === c ? "1" : "0"}">${c === "All" ? "All three" : escapeHtml(c)}</button>`).join("");
  els.competitionChips.querySelectorAll("button").forEach((btn) => btn.addEventListener("click", () => setFilter({ competition: btn.dataset.comp })));

  const teams = ["All", ...uniqueSorted(state.players.map((p) => p.t))];
  els.teamFilter.innerHTML = teams.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
  els.teamFilter.value = teams.includes(state.team) ? state.team : "All";

  const groups = new Map();
  for (const m of state.metrics) {
    if (!groups.has(m.group)) groups.set(m.group, []);
    groups.get(m.group).push(m);
  }
  els.metricCount.textContent = metricDefs().length;
  els.metricChips.innerHTML = Array.from(groups, ([name, metrics]) => `<div class="metric-group"><div class="metric-group-name">${escapeHtml(name)}</div><div class="chip-row">${metrics.map((m) => `<button class="chip metric-chip" type="button" data-id="${escapeHtml(m.id)}" data-on="${state.metricIds.includes(m.id) ? "1" : "0"}" title="${escapeHtml(m.label)}">${escapeHtml(m.shortLabel || m.label)}</button>`).join("")}</div></div>`).join("");
  els.metricChips.querySelectorAll(".metric-chip").forEach((btn) => btn.addEventListener("click", () => {
    const id = btn.dataset.id;
    const next = state.metricIds.includes(id) ? state.metricIds.filter((item) => item !== id) : state.metricIds.concat(id);
    state.metricIds = next.length ? next.slice(0, 12) : preset();
    render();
  }));

  const metricOptions = state.metrics.map((m) => `<option value="${escapeHtml(m.id)}">${escapeHtml(m.label)}</option>`).join("");
  els.xMetric.innerHTML = metricOptions;
  els.yMetric.innerHTML = metricOptions;
  els.xMetric.value = state.metricById.has(state.xMetric) ? state.xMetric : state.metrics[0].id;
  els.yMetric.value = state.metricById.has(state.yMetric) ? state.yMetric : state.metrics[1].id;
}

function renderTray() {
  const players = selectedPlayers();
  const items = players.map((p, i) => {
    const ink = INKS[i % INKS.length];
    return `<div class="tray-item" style="--item-color:${ink.color}"><span class="swatch"></span><div><div class="tray-title" style="color:${ink.color}">${escapeHtml(p.n)}</div><div class="card-meta">${escapeHtml(p.t)} | ${escapeHtml(p.c)}</div><div class="card-meta num">${fmt(p.min, ".0f")} min | ${p.m} apps | ${fmt((p.sh || 0) * 100, ".0f")}% role share</div></div><button class="chip remove-pin" data-id="${escapeHtml(p.id)}" type="button">x</button></div>`;
  });
  if (players.length < 4) {
    items.push(`<div class="tray-item" style="--item-color:var(--color-divider)"><span class="swatch"></span><div><div class="tray-title">Slot ${players.length + 1} open</div><div class="card-meta">Click a point, row, shortlist candidate, or nearest profile.</div></div></div>`);
  }
  els.compareTray.innerHTML = items.join("");
  els.compareTray.querySelectorAll(".remove-pin").forEach((btn) => btn.addEventListener("click", (event) => { event.stopPropagation(); togglePin(btn.dataset.id); }));
}

function renderRadar() {
  const players = selectedPlayers();
  const metrics = metricDefs();
  const cx = 280, cy = 262, radius = 168;
  const n = Math.max(metrics.length, 3);
  const angle = (i) => (i / n) * Math.PI * 2 - Math.PI / 2;
  const point = (i, value) => [cx + Math.cos(angle(i)) * radius * (value / 100), cy + Math.sin(angle(i)) * radius * (value / 100)];
  const rings = [20, 40, 60, 80, 100].map((v) => `<circle cx="${cx}" cy="${cy}" r="${radius * v / 100}" fill="${v === 100 ? "color-mix(in srgb, var(--color-text) 3%, transparent)" : "none"}" stroke="rgba(32,30,29,.16)"></circle>`).join("");
  const spokes = metrics.map((m, i) => { const [x, y] = point(i, 100); return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="rgba(32,30,29,.2)"></line>`; }).join("");
  const labels = metrics.map((m, i) => { const a = angle(i); const ax = Math.cos(a), ay = Math.sin(a); const anchor = ax > .25 ? "start" : ax < -.25 ? "end" : "middle"; return `<text x="${(cx + ax * (radius + 24)).toFixed(1)}" y="${(cy + ay * (radius + 24) + 4).toFixed(1)}" text-anchor="${anchor}" font-size="12.5" font-weight="600">${escapeHtml(m.shortLabel || m.label)}</text>`; }).join("");
  const polys = players.map((p, i) => {
    const ink = INKS[i % INKS.length];
    const pts = metrics.map((m, j) => point(j, p.p[m.id] || 0).map((v) => v.toFixed(1)).join(",")).join(" ");
    return `<polygon points="${pts}" fill="${ink.fill}" stroke="${ink.color}" stroke-width="1.8" stroke-linejoin="round"></polygon>`;
  }).join("");
  const dots = players.map((p, i) => {
    const ink = INKS[i % INKS.length];
    return metrics.map((m, j) => { const [x, y] = point(j, p.p[m.id] || 0); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.2" fill="${ink.color}"></circle>`; }).join("");
  }).join("");
  els.radarChart.innerHTML = `<svg viewBox="0 0 560 540" aria-label="Role percentile radar">${rings}${spokes}<text x="284" y="${cy - radius + 3}" font-size="10" class="num" fill="var(--color-muted)">100</text>${labels}<g style="mix-blend-mode:multiply">${polys}</g>${dots}</svg>`;
}

function renderStrips() {
  const players = selectedPlayers();
  const metrics = metricDefs();
  els.percentileStrips.innerHTML = metrics.map((m) => {
    const values = players.map((p, i) => `<span style="color:${INKS[i % INKS.length].color}">${fmt(p.v[m.id], m.format)}</span>`).join(" ");
    const marks = players.map((p, i) => `<span class="strip-mark" style="left:${fmt(p.p[m.id] || 0, ".1f")}% ;--mark-color:${INKS[i % INKS.length].color}" title="${escapeHtml(p.n)}: ${fmt(p.p[m.id], ".0f")} percentile"></span>`).join("");
    return `<div><div class="strip-label"><span>${escapeHtml(m.label)}</span><span class="num">${values}</span></div><div class="strip-track"><span class="strip-middle"></span><span class="strip-midline"></span>${marks}</div></div>`;
  }).join("");
  const inverted = metrics.filter((m) => m.higherIsBetter === false).map((m) => m.shortLabel || m.label);
  els.invertedNote.textContent = inverted.length ? `Inverted axes: ${inverted.join(", ")}. Lower raw value is better; percentile is flipped.` : "All selected axes read higher-is-better.";
}

function extent(values) {
  const nums = values.filter((v) => v !== null && v !== undefined && !Number.isNaN(Number(v))).map(Number);
  if (!nums.length) return [0, 1];
  let lo = Math.min(...nums), hi = Math.max(...nums);
  if (lo === hi) hi = lo + 1;
  const pad = (hi - lo) * .07;
  return [Math.max(0, lo - pad), hi + pad];
}

function renderScatter() {
  const cohort = filteredPlayers();
  const selected = new Set(state.pinned);
  const xm = state.metricById.get(state.xMetric) || state.metrics[0];
  const ym = state.metricById.get(state.yMetric) || state.metrics[1];
  const [x0, x1] = extent(cohort.map((p) => p.v[xm.id]));
  const [y0, y1] = extent(cohort.map((p) => p.v[ym.id]));
  const sx = (v) => 62 + (((v ?? x0) - x0) / (x1 - x0)) * 540;
  const sy = (v) => 382 - (((v ?? y0) - y0) / (y1 - y0)) * 368;
  const ghosts = cohort.filter((p) => !selected.has(p.id)).map((p) => `<circle class="scatter-point" data-id="${escapeHtml(p.id)}" cx="${sx(p.v[xm.id]).toFixed(1)}" cy="${sy(p.v[ym.id]).toFixed(1)}" r="3.2" fill="rgba(32,30,29,.26)"><title>${escapeHtml(p.n)} | ${escapeHtml(p.t)}</title></circle>`).join("");
  const pins = selectedPlayers().map((p, i) => {
    const ink = INKS[i % INKS.length];
    const x = sx(p.v[xm.id]), y = sy(p.v[ym.id]);
    return `<g><circle class="scatter-point" data-id="${escapeHtml(p.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="7.5" fill="${ink.fill}" stroke="${ink.color}" stroke-width="1.7"></circle><text x="${(x + 12).toFixed(1)}" y="${(y + 4).toFixed(1)}" font-size="12" font-weight="600" fill="${ink.color}" style="paint-order:stroke;stroke:var(--color-bg);stroke-width:3.5px">${escapeHtml(p.n)}</text></g>`;
  }).join("");
  els.scatterChart.innerHTML = `<svg viewBox="0 0 620 440" aria-label="Filtered cohort scatter"><rect x="62" y="14" width="540" height="368" fill="color-mix(in srgb, var(--color-text) 3%, transparent)"></rect><line x1="62" y1="382" x2="602" y2="382" stroke="var(--color-text)"></line><line x1="62" y1="14" x2="62" y2="382" stroke="var(--color-text)"></line>${ghosts}<g style="mix-blend-mode:multiply">${pins}</g><text x="602" y="424" text-anchor="end" font-size="12" font-weight="600">${escapeHtml(xm.label)} -></text><text x="14" y="14" transform="rotate(-90 14 14)" text-anchor="end" font-size="12" font-weight="600">${escapeHtml(ym.label)} -></text></svg>`;
  els.scatterChart.querySelectorAll(".scatter-point").forEach((el) => el.addEventListener("click", () => togglePin(el.dataset.id)));
}

function nearestProfiles() {
  const focus = selectedPlayers()[0];
  const metrics = metricDefs();
  if (!focus || !metrics.length) return [];
  const base = metrics.map((m) => focus.p[m.id] || 0);
  return state.players
    .filter((p) => p.g === focus.g && p.id !== focus.id && (state.competition === "All" || p.c === state.competition) && p.min >= state.minMinutes)
    .map((p) => {
      const sum = metrics.reduce((acc, m, i) => acc + ((p.p[m.id] || 0) - base[i]) ** 2, 0);
      return { p, sim: Math.max(0, 100 - Math.sqrt(sum / metrics.length)) };
    })
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 9);
}

function renderNearest() {
  const focus = selectedPlayers()[0];
  const rows = nearestProfiles();
  els.nearestNote.textContent = focus ? `Profiles closest to ${focus.n} across ${metricDefs().length} selected axes, within ${ROLE_SHORT[focus.g] || focus.g}.` : "Pin a player to rank the cohort by profile distance.";
  els.nearestProfiles.innerHTML = rows.map((row, i) => `<div class="nearest-row" data-id="${escapeHtml(row.p.id)}"><span class="num">${String(i + 1).padStart(2, "0")}</span><span><strong>${escapeHtml(row.p.n)}</strong><br><span class="card-meta">${escapeHtml(row.p.t)} | ${escapeHtml(row.p.c)} | ${fmt(row.p.min, ".0f")} min</span></span><span class="score">${fmt(row.sim, ".1f")}%<span class="mini-bar"><span style="width:${fmt(row.sim, ".1f")}%"></span></span></span></div>`).join("");
  els.nearestProfiles.querySelectorAll(".nearest-row").forEach((el) => el.addEventListener("click", () => togglePin(el.dataset.id)));
}

function renderTable() {
  const metrics = metricDefs();
  const columns = [
    { key: "n", label: "Player" },
    { key: "t", label: "Team" },
    { key: "c", label: "Competition" },
    { key: "g", label: "Role" },
    { key: "min", label: "Mins", numeric: true, format: ".0f" },
    { key: "m", label: "Apps", numeric: true, format: ".0f" },
    ...metrics.map((m) => ({ key: `metric:${m.id}`, label: m.shortLabel || m.label, numeric: true, format: m.format, metric: m.id })),
  ];
  const value = (p, key) => key.startsWith("metric:") ? p.v[key.slice(7)] : p[key];
  const dir = state.sortDirection === "asc" ? 1 : -1;
  const sorted = filteredPlayers().slice().sort((a, b) => {
    const l = value(a, state.sortKey), r = value(b, state.sortKey);
    const lm = l === null || l === undefined, rm = r === null || r === undefined;
    if (lm && rm) return 0;
    if (lm) return 1;
    if (rm) return -1;
    return (typeof l === "number" ? l - r : String(l).localeCompare(String(r))) * dir;
  });
  const rows = sorted.slice(0, 140);
  els.table.querySelector("thead").innerHTML = `<tr>${columns.map((c) => `<th class="${c.numeric ? "numeric" : ""}" data-key="${escapeHtml(c.key)}">${escapeHtml(c.label)}${state.sortKey === c.key ? (state.sortDirection === "asc" ? " ^" : " v") : ""}</th>`).join("")}</tr>`;
  els.table.querySelector("tbody").innerHTML = rows.map((p) => `<tr data-id="${escapeHtml(p.id)}">${columns.map((c) => `<td class="${c.numeric ? "numeric" : ""}">${c.numeric ? fmt(value(p, c.key), c.format) : escapeHtml(value(p, c.key) || "-")}</td>`).join("")}</tr>`).join("");
  els.tableCount.textContent = rows.length === sorted.length ? `${sorted.length} profiles` : `${rows.length} of ${sorted.length} profiles`;
  els.table.querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
    if (state.sortKey === th.dataset.key) state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    else { state.sortKey = th.dataset.key; state.sortDirection = th.classList.contains("numeric") ? "desc" : "asc"; }
    render();
  }));
  els.table.querySelectorAll("tbody tr").forEach((tr) => tr.addEventListener("click", () => togglePin(tr.dataset.id)));
}

function render() {
  if (!state.ready) return;
  renderCaseStudy();
  renderPitch();
  renderControls();
  renderTray();
  renderRadar();
  renderStrips();
  renderScatter();
  renderNearest();
  renderTable();
  writeHash();
}

function bindEvents() {
  els.allRoles.addEventListener("click", () => setFilter({ role: "All", pinned: [] }, true));
  els.otherRole.addEventListener("click", () => setFilter({ role: "Other", pinned: [] }, true));
  els.teamFilter.addEventListener("change", () => setFilter({ team: els.teamFilter.value }));
  els.searchFilter.addEventListener("input", () => setFilter({ search: els.searchFilter.value }));
  els.minutesFilter.addEventListener("input", () => setFilter({ minMinutes: Number(els.minutesFilter.value) }));
  els.resetMetrics.addEventListener("click", () => setFilter({ metricIds: preset() }));
  els.xMetric.addEventListener("change", () => setFilter({ xMetric: els.xMetric.value }));
  els.yMetric.addEventListener("change", () => setFilter({ yMetric: els.yMetric.value }));
  els.shareState.addEventListener("click", async () => {
    writeHash();
    await navigator.clipboard?.writeText(location.href);
    els.shareState.textContent = "Copied";
    setTimeout(() => { els.shareState.textContent = "Copy view link"; }, 1200);
  });
}

async function fetchJson(path) {
  const response = await fetch(versioned(path));
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

async function init() {
  const [playersPayload, metricsPayload, casePayload] = await Promise.all([
    fetchJson(window.DASHBOARD_PLAYERS_PATH).catch(() => fetchJson(window.DASHBOARD_FALLBACK_DATA_PATH)),
    fetchJson(window.DASHBOARD_METRICS_PATH),
    fetchJson(window.DASHBOARD_CASE_STUDY_PATH).catch(() => null),
  ]);
  state.players = normalizePlayers(playersPayload);
  state.metrics = metricsPayload.metricDefinitions;
  state.metricById = new Map(state.metrics.map((m) => [m.id, m]));
  state.rolePresets = metricsPayload.rolePresets;
  state.metricIds = metricsPayload.defaultMetricIds.slice();
  state.role = metricsPayload.defaultRole;
  state.caseStudy = casePayload;
  if (casePayload?.candidates?.length) {
    state.caseCandidateId = playerIdFromCase(casePayload.candidates[0]);
    state.pinned = [playerIdFromCase(casePayload.benchmark), ...casePayload.candidates.slice(0, 2).map(playerIdFromCase)];
  }
  readHash();
  if (!state.pinned.length) pickDefaults();
  state.ready = true;
  bindEvents();
  render();
}

init().catch((error) => {
  document.body.innerHTML = `<main class="page-shell"><section class="validation-card"><h1>Dashboard data failed to load</h1><p>${escapeHtml(error.message)}</p></section></main>`;
});
