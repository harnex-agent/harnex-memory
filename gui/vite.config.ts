import { svelte } from "@sveltejs/vite-plugin-svelte";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  envPrefix: ["VITE_", "TAURI_"],
  resolve: {
    alias: {
      $lib: fileURLToPath(new URL("./src/lib", import.meta.url))
    }
  },
  server: {
    host: process.env.TAURI_DEV_HOST ?? false,
    port: 1420,
    strictPort: true
  },
  test: {
    environment: "node",
    include: ["src/**/*.{test,spec}.ts"]
  }
});
