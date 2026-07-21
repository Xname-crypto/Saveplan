import vue from "@vitejs/plugin-vue"
import { rmSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { defineConfig } from "vite"

const configDir = dirname(fileURLToPath(import.meta.url))
const excludedLocalVideos = [
  "dist/video/login-restart-2.mp4",
  "dist/video/register-anime.mp4",
  "dist/video/forgot-study-desk.mp4",
  "dist/stitch/home-study-writing.mp4",
]

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === "mux-video",
        },
      },
    }),
    {
      name: "exclude-r2-hosted-videos",
      closeBundle() {
        for (const file of excludedLocalVideos) {
          rmSync(resolve(configDir, file), { force: true })
        }
      },
    },
  ],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
})
