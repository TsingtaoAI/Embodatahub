import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";

// Resolve certs relative to project root (robot-data-studio/)
const certDir = path.resolve(__dirname, "../../certs");

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // 生产由主站 nginx 挂在 /rds-app/ 下；dev 必须保持 "/"（Vite 的 base 在 dev 也生效）
  base: command === "build" ? "/rds-app/" : "/",
  server: {
    port: 5173,
    https: fs.existsSync(path.join(certDir, "key.pem"))
      ? { key: path.join(certDir, "key.pem"), cert: path.join(certDir, "cert.pem") }
      : false,
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "credentialless",
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8005",
        configure: (proxy: any) => {
          proxy.on("proxyRes", (proxyRes: any) => {
            proxyRes.headers["Cross-Origin-Resource-Policy"] = "cross-origin";
          });
        },
      },
    },
  },
  // 产物落 dist/rds-app：dist 变成稳定的「父目录」，容器挂 dist，
  // nginx root 指向 /srv/rds-holder，URI 前缀 rds-app/ 正好对应子目录。
  // 这样 vite build 只替换 dist/rds-app，父目录 inode 不变，重建后无需重启容器。
  build: {
    outDir: "dist/rds-app",
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
  },
}));
