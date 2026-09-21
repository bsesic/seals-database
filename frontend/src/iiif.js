// IIIF viewer (self-hosted Mirador). Reads the manifest URLs emitted by the
// artefact detail template and opens one Mirador window per manifest.
import Mirador from "mirador";

function initViewer() {
  const el = document.getElementById("iiif-viewer");
  const dataEl = document.getElementById("iiif-manifests");
  if (!el || !dataEl) return;

  const manifests = JSON.parse(dataEl.textContent);
  if (!manifests.length) return;

  Mirador.viewer({
    id: "iiif-viewer",
    windows: manifests.map((manifestId) => ({ manifestId })),
    workspaceControlPanel: { enabled: false },
  });
}

document.addEventListener("DOMContentLoaded", initViewer);
