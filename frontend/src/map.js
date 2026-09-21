// Find-spot map (self-hosted Leaflet). Reads the find-spot data emitted by the
// template as a json_script tag and renders one circle marker per find spot.
import L from "leaflet";
import "leaflet/dist/leaflet.css";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
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

  const bounds = [];
  findspots.forEach((f) => {
    const radius = 6 + Math.min(18, Math.sqrt(f.count) * 3);
    const marker = L.circleMarker([f.lat, f.lng], {
      radius,
      color: "#0d6efd",
      weight: 1,
      fillColor: "#0d6efd",
      fillOpacity: 0.55,
    }).addTo(map);

    let html = `<strong>${escapeHtml(f.name)}</strong>`;
    if (f.ancient) html += ` <span class="text-muted">(${escapeHtml(f.ancient)})</span>`;
    if (f.region) html += `<br>${escapeHtml(f.region)}`;
    html += `<br>${f.count} object(s)`;
    html += `<br><a href="${encodeURI(f.url)}">View objects →</a>`;
    marker.bindPopup(html);
    bounds.push([f.lat, f.lng]);
  });

  if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 10 });
}

document.addEventListener("DOMContentLoaded", initMap);
