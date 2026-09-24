import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const files = ["re_viewer_bg.wasm", "re_viewer.js"];

for (const file of files) {
  const source = resolve(
    root,
    `apps/web/node_modules/@rerun-io/web-viewer/${file}`,
  );
  const destination = resolve(root, `apps/web/public/rerun/${file}`);

  await mkdir(dirname(destination), { recursive: true });
  await copyFile(source, destination);
  console.log(`Prepared Rerun WebViewer asset: ${file} → ${destination}`);
}
