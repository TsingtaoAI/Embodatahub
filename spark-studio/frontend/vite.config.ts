import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'node:path';
import fs from 'fs';
import path from 'path';

const certDir = path.resolve(__dirname, '../../certs');

export default defineConfig(({ command }) => ({
    plugins: [vue()],
    // 生产由主站 nginx 挂在 /spark/ 下；dev 必须保持 '/'（Vite 的 base 在 dev 也生效）
    base: command === 'build' ? '/spark/' : '/',
    resolve: {
        alias: {
            '@': resolve(__dirname, './src'),
        },
    },
    server: {
        port: 5174,
        host: '0.0.0.0',
        https: fs.existsSync(path.join(certDir, 'key.pem'))
            ? { key: path.join(certDir, 'key.pem'), cert: path.join(certDir, 'cert.pem') }
            : undefined,
        /** 代理后端 API 请求 */
        proxy: {
            '/api': {
                target: 'http://localhost:8004',
                changeOrigin: true,
            },
        },
    },
    build: {
        target: 'esnext',
        // 产物落 dist/spark：dist 变成稳定的「父目录」，容器挂 dist，
        // nginx root 指向 /srv/spark-holder，URI 前缀 spark/ 正好对应子目录。
        // 这样 vite build 只替换 dist/spark，父目录 inode 不变，重建后无需重启容器。
        outDir: 'dist/spark',
    },
}));
