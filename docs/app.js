const state = {
  players: [],
  metrics: [],
  metricById: new Map(),
  rolePresets: {},
  selectedMetricIds: [],
  selectedPlayerIds: [],
  sortKey: "similarityRank",
  sortDirection: "asc",
};

const els = {
  positionFilter: document.getElementById("positionFilter"),
  competitionFilter: document.getElementById("competitionFilter"),
  teamFilter: document.getElementById("teamFilter"),
  minutesFilter: document.getElementById("minutesFilter"),
  minutesValue: document.getElementById("minutesValue"),
  searchFilter: document.getElementById("searchFilter"),
  kaneOnlyFilter: document.getElementById("kaneOnlyFilter"),
  metricCheckboxes: document.getElementById("metricCheckboxes"),
  playerSelects: Array.from(document.querySelectorAll(".player-select")),
  resetPlayers: document.getElementById("resetPlayers"),
  barMetricSelect: document.getElementById("barMetricSelect"),
  summaryPlayers: document.getElementById("summaryPlayers"),
  summaryCompetitions: document.getElementById("summaryCompetitions"),
  summarySelected: document.getElementById("summarySelected"),
  tableCount: document.getElementById("tableCount"),
  table: document.getElementById("candidateTable"),
};

const colors = ["#0f766e", "#8a4b12", "#1d4ed8", "#be123c"];

function formatValue(value, format = ".1f") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const number = Number(value);
  if (format === ".3f") return number.toFixed(3);
  if (format === ".2f") return number.toFixed(2);
  if (format === ".1f") return number.toFixed(1);
  if (format === ".0f") return number.toFixed(0);
  return String(value);
}

function playerKey(player) {
  return `${player.competitionName}|${player.seasonName}|${player.playerId}`;
}

function playerLabel(player) {
  return `${player.playerName} - ${player.teamName}`;
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function setOptions(select, values, { includeAll = true, selected = "All" } = {}) {
  select.innerHTML = "";
  const options = includeAll ? ["All", ...values] : values;
  for (const value of options) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
  select.value = options.includes(selected) ? selected : options[0] || "";
}

function getFilteredPlayers() {
  const position = els.positionFilter.value;
  const competition = els.competitionFilter.value;
  const team = els.teamFilter.value;
  const minMinutes = Number(els.minutesFilter.value);
  const search = els.searchFilter.value.trim().toLowerCase();
  const kaneOnly = els.kaneOnlyFilter.checked;

  return state.players.filter((player) => {
    if (position !== "All" && player.positionGroup !== position) return false;
    if (competition !== "All" && player.competitionName !== competition) return false;
    if (team !== "All" && player.teamName !== team) return false;
    if (player.minutes < minMinutes) return false;
    if (kaneOnly && !player.isKaneSimilarityCandidate) return false;
    if (search && !player.playerName.toLowerCase().includes(search)) return false;
    return true;
  });
}

function currentPresetRole() {
  return els.positionFilter.value !== "All" ? els.positionFilter.value : "Centre Forward";
}

function selectPresetMetrics() {
  const preset = state.rolePresets[currentPresetRole()] || state.rolePresets["Centre Forward"] || [];
  state.selectedMetricIds = preset.filter((metricId) => state.metricById.has(metricId));
}

function renderMetricCheckboxes() {
  const grouped = new Map();
  for (const metric of state.metrics) {
    if (!grouped.has(metric.group)) grouped.set(metric.group, []);
    grouped.get(metric.group).push(metric);
  }

  els.metricCheckboxes.innerHTML = "";
  for (const [group, metrics] of grouped.entries()) {
    const groupLabel = document.createElement("div");
    groupLabel.className = "metric-group-label";
    groupLabel.textContent = group;
    els.metricCheckboxes.appendChild(groupLabel);

    for (const metric of metrics) {
      const id = `metric-${metric.id}`;
      const label = document.createElement("label");
      label.className = "metric-option";
      label.htmlFor = id;

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = id;
      checkbox.value = metric.id;
      checkbox.checked = state.selectedMetricIds.includes(metric.id);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          state.selectedMetricIds.push(metric.id);
        } else {
          state.selectedMetricIds = state.selectedMetricIds.filter((value) => value !== metric.id);
        }
        if (state.selectedMetricIds.length === 0) selectPresetMetrics();
        renderMetricCheckboxes();
        renderDashboard();
      });

      const text = document.createElement("span");
      text.textContent = metric.label;

      label.appendChild(checkbox);
      label.appendChild(text);
      els.metricCheckboxes.appendChild(label);
    }
  }
}

function selectedPlayers() {
  const byKey = new Map(state.players.map((player) => [playerKey(player), player]));
  return state.selectedPlayerIds.map((id) => byKey.get(id)).filter(Boolean).slice(0, 4);
}

function pickDefaultPlayers(filteredPlayers) {
  const byId = new Map(filteredPlayers.map((player) => [player.playerId, player]));
  const picked = [];
  for (const id of [10955, 3018, 20521, 4269]) {
    if (byId.has(id)) picked.push(playerKey(byId.get(id)));
  }
  for (const player of filteredPlayers) {
    if (picked.length >= 4) break;
    const key = playerKey(player);
    if (!picked.includes(key)) picked.push(key);
  }
  state.selectedPlayerIds = picked;
}

function renderPlayerSelectors() {
  const filtered = getFilteredPlayers();
  const options = filtered
    .slice()
    .sort((a, b) => a.playerName.localeCompare(b.playerName))
    .map((player) => ({ value: playerKey(player), label: playerLabel(player) }));

  const validKeys = new Set(options.map((option) => option.value));
  state.selectedPlayerIds = state.selectedPlayerIds.filter((key, index, array) => validKeys.has(key) && array.indexOf(key) === index);
  if (state.selectedPlayerIds.length === 0) pickDefaultPlayers(filtered);

  els.playerSelects.forEach((select, index) => {
    const selected = state.selectedPlayerIds[index] || "";
    select.innerHTML = "";
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = index === 0 ? "Select player" : "None";
    select.appendChild(empty);

    for (const optionData of options) {
      const option = document.createElement("option");
      option.value = optionData.value;
      option.textContent = optionData.label;
      option.disabled = state.selectedPlayerIds.includes(optionData.value) && optionData.value !== selected;
      select.appendChild(option);
    }
    select.value = selected;
  });
}

function updateSelectedPlayersFromControls() {
  state.selectedPlayerIds = els.playerSelects
    .map((select) => select.value)
    .filter(Boolean)
    .filter((value, index, array) => array.indexOf(value) === index);
}

function renderBarMetricSelect() {
  const selected = els.barMetricSelect.value || state.selectedMetricIds[0] || state.metrics[0].id;
  els.barMetricSelect.innerHTML = "";
  for (const metric of state.metrics) {
    const option = document.createElement("option");
    option.value = metric.id;
    option.textContent = metric.label;
    els.barMetricSelect.appendChild(option);
  }
  els.barMetricSelect.value = state.metricById.has(selected) ? selected : state.metrics[0].id;
}

function renderSummary(filteredPlayers) {
  els.summaryPlayers.textContent = String(filteredPlayers.length);
  els.summaryCompetitions.textContent = String(uniqueSorted(filteredPlayers.map((player) => player.competitionName)).length);
  els.summarySelected.textContent = String(selectedPlayers().length);
  els.minutesValue.textContent = els.minutesFilter.value;
}

function renderRadar() {
  const players = selectedPlayers();
  const metrics = state.selectedMetricIds.map((id) => state.metricById.get(id)).filter(Boolean);
  const labels = metrics.map((metric) => metric.shortLabel || metric.label);

  const traces = players.map((player, index) => {
    const values = metrics.map((metric) => player.percentiles[metric.id] ?? 0);
    return {
      type: "scatterpolar",
      r: [...values, values[0]],
      theta: [...labels, labels[0]],
      fill: "toself",
      name: player.playerName,
      line: { color: colors[index % colors.length], width: 2 },
      opacity: 0.72,
      hovertemplate: "%{theta}: %{r:.1f}<extra>%{fullData.name}</extra>",
    };
  });

  Plotly.react("radarChart", traces, {
    margin: { t: 28, r: 40, b: 40, l: 40 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: true,
    legend: { orientation: "h", y: -0.12 },
    polar: {
      bgcolor: "#ffffff",
      radialaxis: { visible: true, range: [0, 100], tickfont: { size: 11 } },
      angularaxis: { tickfont: { size: 12 } },
    },
  }, { responsive: true, displayModeBar: false });
}

function renderBar() {
  const players = selectedPlayers();
  const metric = state.metricById.get(els.barMetricSelect.value) || state.metricById.get(state.selectedMetricIds[0]);
  if (!metric) return;

  const trace = {
    type: "bar",
    x: players.map((player) => player.playerName),
    y: players.map((player) => player.metrics[metric.id] ?? 0),
    marker: { color: players.map((_, index) => colors[index % colors.length]) },
    hovertemplate: `${metric.label}: %{y}<extra></extra>`,
  };

  Plotly.react("barChart", [trace], {
    margin: { t: 26, r: 18, b: 96, l: 56 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    yaxis: { title: metric.label, gridcolor: "#e6ebf1" },
    xaxis: { tickangle: -25 },
  }, { responsive: true, displayModeBar: false });
}

function numericSortValue(value) {
  if (value === null || value === undefined || value === "") return Number.POSITIVE_INFINITY;
  return Number(value);
}

function sortPlayers(players) {
  const key = state.sortKey;
  return players.slice().sort((a, b) => {
    let left;
    let right;
    if (key.startsWith("metric:")) {
      const metricId = key.replace("metric:", "");
      left = numericSortValue(a.metrics[metricId]);
      right = numericSortValue(b.metrics[metricId]);
    } else if (["minutes", "matches", "similarityRank", "similarityPercentile"].includes(key)) {
      left = numericSortValue(a[key]);
      right = numericSortValue(b[key]);
    } else {
      left = String(a[key] || "");
      right = String(b[key] || "");
    }

    let result = 0;
    if (typeof left === "number" && typeof right === "number") result = left - right;
    else result = left.localeCompare(right);
    return state.sortDirection === "asc" ? result : -result;
  });
}

function renderTable(filteredPlayers) {
  const selectedMetricIds = state.selectedMetricIds.slice(0, 6);
  const columns = [
    { key: "playerName", label: "Player" },
    { key: "teamName", label: "Team" },
    { key: "competitionName", label: "Competition" },
    { key: "positionGroup", label: "Role" },
    { key: "minutes", label: "Minutes", numeric: true, format: ".0f" },
    { key: "similarityRank", label: "Kane rank", numeric: true, format: ".0f" },
    ...selectedMetricIds.map((metricId) => {
      const metric = state.metricById.get(metricId);
      return { key: `metric:${metricId}`, label: metric.shortLabel || metric.label, numeric: true, format: metric.format };
    }),
  ];

  const thead = els.table.querySelector("thead");
  const tbody = els.table.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column.label;
    if (column.numeric) th.className = "numeric";
    th.addEventListener("click", () => {
      if (state.sortKey === column.key) {
        state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = column.key;
        state.sortDirection = column.numeric ? "desc" : "asc";
      }
      renderDashboard();
    });
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);

  const rows = sortPlayers(filteredPlayers).slice(0, 100);
  for (const player of rows) {
    const tr = document.createElement("tr");
    for (const column of columns) {
      const td = document.createElement("td");
      if (column.numeric) td.className = "numeric";
      let value;
      if (column.key.startsWith("metric:")) {
        value = player.metrics[column.key.replace("metric:", "")];
      } else {
        value = player[column.key];
      }
      td.textContent = column.numeric ? formatValue(value, column.format) : value || "-";
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  els.tableCount.textContent = `${filteredPlayers.length} rows`;
}

function renderDashboard() {
  const filtered = getFilteredPlayers();
  renderPlayerSelectors();
  renderBarMetricSelect();
  renderSummary(filtered);
  renderRadar();
  renderBar();
  renderTable(filtered);
}

function handleFilterChange({ resetMetrics = false } = {}) {
  if (resetMetrics) {
    selectPresetMetrics();
    renderMetricCheckboxes();
  }
  state.selectedPlayerIds = [];
  renderDashboard();
}

async function init() {
  const [siteData, metricsData] = await Promise.all([
    fetch(window.DASHBOARD_DATA_PATH).then((response) => response.json()),
    fetch(window.DASHBOARD_METRICS_PATH).then((response) => response.json()),
  ]);

  state.players = siteData.players;
  state.metrics = metricsData.metricDefinitions;
  state.metricById = new Map(state.metrics.map((metric) => [metric.id, metric]));
  state.rolePresets = metricsData.rolePresets;
  state.selectedMetricIds = metricsData.defaultMetricIds.slice();

  setOptions(els.positionFilter, siteData.scope.positionGroups, { selected: metricsData.defaultRole });
  setOptions(els.competitionFilter, siteData.scope.competitions);
  setOptions(els.teamFilter, uniqueSorted(state.players.map((player) => player.teamName)));
  els.kaneOnlyFilter.checked = true;

  renderMetricCheckboxes();
  renderDashboard();

  els.positionFilter.addEventListener("change", () => {
    els.kaneOnlyFilter.checked = els.positionFilter.value === "Centre Forward";
    handleFilterChange({ resetMetrics: true });
  });
  els.competitionFilter.addEventListener("change", () => handleFilterChange());
  els.teamFilter.addEventListener("change", () => handleFilterChange());
  els.minutesFilter.addEventListener("input", () => handleFilterChange());
  els.searchFilter.addEventListener("input", () => handleFilterChange());
  els.kaneOnlyFilter.addEventListener("change", () => handleFilterChange());
  els.playerSelects.forEach((select) => {
    select.addEventListener("change", () => {
      updateSelectedPlayersFromControls();
      renderDashboard();
    });
  });
  els.resetPlayers.addEventListener("click", () => {
    els.positionFilter.value = "Centre Forward";
    els.minutesFilter.value = 900;
    els.kaneOnlyFilter.checked = true;
    selectPresetMetrics();
    renderMetricCheckboxes();
    state.selectedPlayerIds = [];
    renderDashboard();
  });
  els.barMetricSelect.addEventListener("change", () => {
    renderBar();
  });
}

init().catch((error) => {
  console.error(error);
  document.body.innerHTML = `<main class="main"><section class="panel"><div class="panel-header"><h2>Dashboard data failed to load</h2></div><div class="table-wrap"><p>${error.message}</p></div></section></main>`;
});
