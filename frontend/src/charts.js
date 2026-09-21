// Statistics charts (self-hosted Chart.js). Reads the aggregated data emitted by
// the statistics template and renders one chart per <canvas data-chart="...">.
// Wired into templates/catalog/statistics.html (added with the statistics view).
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

// Colourblind-friendly categorical palette (Tableau 10).
const PALETTE = [
  "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948",
  "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295",
];

function initCharts() {
  const dataEl = document.getElementById("charts-data");
  if (!dataEl) return;

  const data = JSON.parse(dataEl.textContent);
  const dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  Chart.defaults.color = dark ? "#adb5bd" : "#495057";
  Chart.defaults.borderColor = dark ? "rgba(255,255,255,.1)" : "rgba(0,0,0,.1)";

  document.querySelectorAll("canvas[data-chart]").forEach((canvas) => {
    const key = canvas.dataset.chart;
    const kind = canvas.dataset.type;
    const d = data[key];
    if (!d || !d.labels.length) {
      const note = document.createElement("p");
      note.className = "text-muted small mb-0";
      note.textContent = "No data.";
      canvas.replaceWith(note);
      return;
    }
    const isDoughnut = kind === "doughnut";
    const horizontal = kind === "bar";
    new Chart(canvas, {
      type: isDoughnut ? "doughnut" : "bar",
      data: {
        labels: d.labels,
        datasets: [{
          label: "Objects",
          data: d.data,
          backgroundColor: isDoughnut ? PALETTE : "#4e79a7",
          borderWidth: isDoughnut ? 1 : 0,
        }],
      },
      options: {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: isDoughnut, position: "right" } },
        scales: isDoughnut ? {} : {
          x: { beginAtZero: true, ticks: { precision: 0 } },
          y: { beginAtZero: true, ticks: { precision: 0 } },
        },
      },
    });
  });
}

document.addEventListener("DOMContentLoaded", initCharts);
