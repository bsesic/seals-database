// Find-spot map (self-hosted Leaflet). Reads the find-spot data emitted by the
// template as a json_script tag and renders the find spots as clustered circle
// markers, with an alternative density heatmap the user can toggle.
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.heat";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function popupHtml(f) {
  let html = `<strong>${escapeHtml(f.name)}</strong>`;
  if (f.ancient) html += ` <span class="text-muted">(${escapeHtml(f.ancient)})</span>`;
  if (f.region) html += `<br>${escapeHtml(f.region)}`;
  html += `<br>${f.count} object(s)`;
  html += `<br><a href="${encodeURI(f.url)}">View objects →</a>`;
  return html;
}

function initMap() {
  const el = document.getElementById("map");
  const dataEl = document.getElementById("findspots-data");
  if (!el || !dataEl) return;

  const findspots = JSON.parse(dataEl.textContent);
  const map = L.map("map").setView([31.6, 35.3], 7); // Southern Levant
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  const maxCount = findspots.reduce((m, f) => Math.max(m, f.count), 1);
  const bounds = [];
  const clusters = L.markerClusterGroup({ chunkedLoading: true });
  const heatPoints = [];

  findspots.forEach((f) => {
    const radius = 6 + Math.min(18, Math.sqrt(f.count) * 3);
    L.circleMarker([f.lat, f.lng], {
      radius,
      color: "#0d6efd",
      weight: 1,
      fillColor: "#0d6efd",
      fillOpacity: 0.55,
    })
      .bindPopup(popupHtml(f))
      .addTo(clusters);

    // Heat intensity scaled by the object count at the find spot.
    heatPoints.push([f.lat, f.lng, 0.25 + 0.75 * (f.count / maxCount)]);
    bounds.push([f.lat, f.lng]);
  });

  const heat = L.heatLayer(heatPoints, { radius: 25, blur: 18, maxZoom: 11 });

  clusters.addTo(map); // clustered markers shown by default
  L.control
    .layers(null, { "Clustered markers": clusters, Heatmap: heat }, { collapsed: false })
    .addTo(map);

  if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 10 });
}

document.addEventListener("DOMContentLoaded", initMap);
