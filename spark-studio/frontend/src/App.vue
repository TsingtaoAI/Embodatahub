<template>
    <div class="app">
        <!-- 顶部工具栏 -->
        <SceneControls
            :splat-count="splatCount"
            @open-file="onOpenFile"
            @reset-camera="sparkViewerRef?.resetCamera()"
            @clear-all="onClearAll"
        />

        <!-- 核心 3D 查看器 -->
        <SparkViewer
            ref="sparkViewerRef"
            :src="initialSrc"
            @loaded="onSplatLoaded"
            @error="onSplatError"
            @splat-count="onSplatCountChange"
        />

        <!-- 文件浏览器面板 -->
        <div class="file-panel" :class="{ open: showFiles }">
            <div class="file-panel-header">
                <span>📂 演示场景</span>
                <button class="panel-close-btn" @click="showFiles = false">✕</button>
            </div>
            <div class="file-panel-body">
                <div v-if="files.length === 0" class="file-empty">
                    <span class="loading-dots">加载中<span>.</span><span>.</span><span>.</span></span>
                </div>
                <div
                    v-for="f in files"
                    :key="f.name"
                    class="file-item"
                    :class="{ active: currentFileName === f.name }"
                    @click="loadDemoFile(f.path, f.name)"
                >
                    <div class="file-icon">📦</div>
                    <div class="file-info">
                        <div class="file-name">{{ f.name.replace('.spz', '') }}</div>
                        <div class="file-size">{{ (f.size / 1024 / 1024).toFixed(1) }} MB</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 文件信息面板 -->
        <SplatInfo
            :visible="showInfo"
            :splat-count="splatCount"
            :current-file="currentFileName"
            @close="showInfo = false"
        />

        <!-- 返回主平台按钮 -->
        <div class="back-bar">
            <button class="back-btn" @click="goBackToPlatform">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
                <span>返回</span>
            </button>
            <span v-if="currentFileName" class="current-scene-label">{{ currentFileName.replace('.spz', '') }}</span>
        </div>

        <!-- 右下角操作按钮 -->
        <div class="fab-group">
            <button class="fab-btn" title="文件列表" @click="showFiles = !showFiles">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
            </button>
            <button class="fab-btn" title="场景信息" @click="showInfo = !showInfo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import SparkViewer from './components/SparkViewer.vue';
import SceneControls from './components/SceneControls.vue';
import SplatInfo from './components/SplatInfo.vue';

const sparkViewerRef = ref<InstanceType<typeof SparkViewer> | null>(null);

// 状态
const splatCount = ref(0);
const currentFileName = ref('');
const showInfo = ref(false);
const showFiles = ref(true); // 默认打开文件面板
const files = ref<Array<{ name: string; path: string; size: number }>>([]);

// 从 URL 参数获取初始加载文件
const initialSrc = ref('');

/**
 * 后端返回的是 /api/... 形式的绝对路径，必须拼上部署根才是可取的 URL
 * （dev 为 "/" 走 Vite 代理，生产为 "/spark/" 走主站 nginx）。
 * ⚠️ 不要写死 http://localhost:8004 —— 那指向访问者自己的机器，远程必然打不开。
 */
function toPublicUrl(path: string): string {
    return `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`;
}

/** 从后端 API 获取文件列表 */
async function fetchFiles() {
    try {
        // dev 下 BASE_URL 为 "/"，生产为 "/spark/"
        const resp = await fetch(`${import.meta.env.BASE_URL}api/files`);
        const data = await resp.json() as { files: Array<{ name: string; path: string; size: number }> };
        files.value = data.files;
    } catch {
        console.warn('无法连接 Spark Studio 后端');
    }
}

/** 加载演示文件（通过更新 src prop 触发 SparkViewer 内部切换） */
function loadDemoFile(path: string, name: string) {
    initialSrc.value = toPublicUrl(path);
    currentFileName.value = name;
    showFiles.value = false;
}

onMounted(async () => {
    // 获取文件列表
    await fetchFiles();

    // 如果有演示文件，默认加载第一个
    if (files.value.length > 0 && !initialSrc.value) {
        const first = files.value[0];
        initialSrc.value = toPublicUrl(first.path);
        currentFileName.value = first.name;
    }

    const params = new URLSearchParams(window.location.search);
    const fileUrl = params.get('file');
    if (fileUrl) {
        initialSrc.value = fileUrl;
        currentFileName.value = fileUrl.split('/').pop() || fileUrl;
    }

    // 监听来自主前端的消息（iframe 通信）
    window.addEventListener('message', (event) => {
        const { type, payload } = event.data || {};
        if (type === 'spark-load-file' && payload?.url) {
            sparkViewerRef.value?.loadSplat(payload.url);
            currentFileName.value = payload.url.split('/').pop() || payload.url;
        }
        if (type === 'spark-clear') {
            sparkViewerRef.value?.clearAll();
            currentFileName.value = '';
        }
    });

    // 监听文件选择事件
    window.addEventListener('spark-files-selected', ((event: CustomEvent) => {
        const { files: selectedFiles } = event.detail;
        for (const file of selectedFiles) {
            sparkViewerRef.value?.loadFile(file);
            currentFileName.value = file.name;
        }
    }) as EventListener);
});

function onOpenFile() {
    // 实际文件选择由 SceneControls 的 input 触发
    // 这里可以打开一个文件对话框或展示历史记录
}

function onClearAll() {
    sparkViewerRef.value?.clearAll();
    currentFileName.value = '';
    splatCount.value = 0;
}

/** 返回主平台 */
function goBackToPlatform() {
    // 作为 iframe 嵌入时，通知父窗口导航
    try {
        window.parent.postMessage(
            { type: 'spark-navigate-back', payload: {} },
            '*',
        );
    } catch {
        // 独立窗口时直接跳转
        window.location.href = `${window.location.origin}/`;
    }
}

function onSplatLoaded(name: string) {
    currentFileName.value = name;
}

function onSplatError(msg: string) {
    console.error('[SparkStudio]', msg);
}

function onSplatCountChange(count: number) {
    splatCount.value = count;
}
</script>

<style>
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body, #app {
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    background: #1a1a2e;
}

.app {
    width: 100%;
    height: 100%;
    position: relative;
}

/* 右下角 FAB 按钮组 */
.fab-group {
    position: absolute;
    bottom: 16px;
    right: 16px;
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.fab-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(8px);
    color: rgba(255,255,255,0.7);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
}

.fab-btn:hover {
    background: rgba(255,255,255,0.1);
    color: #fff;
}

/* 顶部返回栏 */
.back-bar {
    position: absolute;
    top: 52px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 25;
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 4px 6px 4px 4px;
}

.back-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border: none;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.8);
    border-radius: 5px;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.15s;
}

.back-btn:hover {
    background: rgba(255,255,255,0.15);
    color: #fff;
}

.current-scene-label {
    color: rgba(255,255,255,0.5);
    font-size: 12px;
    padding-right: 8px;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 文件浏览器面板 */
.file-panel {
    position: absolute;
    top: 56px;
    left: 12px;
    width: 260px;
    max-height: calc(100% - 80px);
    background: rgba(20, 20, 35, 0.92);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    z-index: 30;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transform: translateX(-280px);
    opacity: 0;
    transition: all 0.25s ease;
}

.file-panel.open {
    transform: translateX(0);
    opacity: 1;
}

.file-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.85);
    font-size: 14px;
    font-weight: 500;
}

.panel-close-btn {
    background: none;
    border: none;
    color: rgba(255,255,255,0.4);
    cursor: pointer;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
}

.panel-close-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }

.file-panel-body {
    overflow-y: auto;
    padding: 6px;
    flex: 1;
}

.file-empty {
    padding: 24px;
    text-align: center;
    color: rgba(255,255,255,0.3);
    font-size: 13px;
}

/* loading dots animation */
.loading-dots span { animation: blink 1.4s infinite both; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

.file-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
}

.file-item:hover { background: rgba(255,255,255,0.06); }
.file-item.active { background: rgba(108, 99, 255, 0.2); }

.file-icon { font-size: 20px; }

.file-info { flex: 1; min-width: 0; }

.file-info .file-name {
    color: rgba(255,255,255,0.8);
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.file-info .file-size {
    color: rgba(255,255,255,0.35);
    font-size: 11px;
    margin-top: 2px;
}

/* 滚动条 */
.file-panel-body::-webkit-scrollbar { width: 4px; }
.file-panel-body::-webkit-scrollbar-track { background: transparent; }
.file-panel-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
</style>
