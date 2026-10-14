import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        game: fileURLToPath(new URL("./index.html", import.meta.url)),
        studio: fileURLToPath(new URL("./wolf-studio.html", import.meta.url)),
      },
    },
  },
});
