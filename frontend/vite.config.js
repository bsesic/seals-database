import { defineConfig } from "vite";
import { resolve } from "path";

// Vite builds the theme assets (Bootstrap SCSS + JS) and the per-feature bundles
// (map, IIIF viewer, charts) into Django's static dir. django-vite reads the
// generated manifest and emits the right tags per env. Self-hosting these
// libraries (instead of CDNs) lets the app run offline and behind a strict CSP.
export default defineConfig({
  base: "/static/dist/",
  build: {
    manifest: true,
    emptyOutDir: true,
    outDir: resolve(__dirname, "../backend/static/dist"),
    rollupOptions: {
      input: {
        main: resolve(__dirname, "src/main.js"),
        map: resolve(__dirname, "src/map.js"),
        iiif: resolve(__dirname, "src/iiif.js"),
        charts: resolve(__dirname, "src/charts.js"),
      },
    },
  },
  server: {
    origin: "http://localhost:5173",
  },
});
