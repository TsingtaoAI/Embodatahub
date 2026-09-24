<template>
    <div ref="containerRef" class="spark-viewer" @drop.prevent="onDrop" @dragover.prevent>
        <!-- 加载中遮罩 -->
        <div v-if="isLoading" class="spark-overlay">
            <div class="spark-loading">
                <div class="spinner"></div>
                <p>{{ loadingText }}</p>
                <div v-if="loadProgress > 0" class="progress-bar">
                    <div class="progress-fill" :style="{ width: `${loadProgress}%` }"></div>
                </div>
            </div>
        </div>

        <!-- 空状态提示 -->
        <div v-if="!isLoading && splatCount === 0 && !error" class="spark-overlay spark-empty">
            <div class="spark-empty-content">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 002 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                </svg>
                <h3>3D 场景可视化</h3>
                <p>拖放 .spz / .ply / .rad 文件到此处加载</p>
                <p class="sub">或使用上方工具栏打开文件</p>
            </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="spark-overlay spark-error">
            <p>⚠️ {{ error }}</p>
            <button @click="clearError">关闭</button>
        </div>

        <!-- 加载中的 splat 列表提示 -->
        <div v-if="loadingNames.length > 0" class="spark-toast-list">
            <div v-for="item in loadingNames" :key="item.name" class="spark-toast-item">
                <span class="spark-toast-name">{{ item.name }}</span>
                <span class="spark-toast-progress">{{ item.progress }}%</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { initSparkScene, type SparkScene, isSupportedFormat } from '../utils/spark';

const props = withDefaults(
    defineProps<{
        /** 初始加载的 splat URL */
        src?: string;
        /** 背景色 */
        backgroundColor?: string;
        /** splat 质量预算 */
        splatBudget?: number;
    }>(),
    {
        src: '',
        backgroundColor: '#1a1a2e',
        splatBudget: 2_500_000,
    },
);

const emit = defineEmits<{
    (e: 'loaded', name: string): void;
    (e: 'error', msg: string): void;
    (e: 'splat-count', count: number): void;
}>();

const containerRef = ref<HTMLDivElement | null>(null);

let scene: SparkScene | null = null;

// --- 状态 ---
const isLoading = ref(false);
const loadingText = ref('正在加载...');
const loadProgress = ref(0);
const splatCount = ref(0);
const error = ref('');
const loadingNames = ref<Array<{ name: string; progress: number }>>([]);

// --- 方法 ---

function clearError() {
    error.value = '';
}

/** 加载 splat 文件（自动清除之前错误） */
async function loadSplat(url: string, name?: string): Promise<boolean> {
    if (!scene) return false;

    // 清除之前的错误状态
    clearError();

    const fileName = name || url.split('/').pop() || url;
    const formatSupported = isSupportedFormat(fileName);
    if (!formatSupported) {
        error.value = `不支持的文件格式: ${fileName}。支持的格式: .spz, .ply, .splat, .ksplat, .sog, .rad`;
        emit('error', error.value);
        return false;
    }

    isLoading.value = true;
    loadingText.value = `正在加载: ${fileName}`;
    loadProgress.value = 0;

    const loadingItem = { name: fileName, progress: 0 };
    loadingNames.value.push(loadingItem);

    try {
        // 模拟进度（真实进度依赖 SplatMesh 的 progress 属性）
        const progressInterval = setInterval(() => {
            loadingItem.progress = Math.min(loadingItem.progress + 5, 95);
            // 刷新响应式
            loadingNames.value = [...loadingNames.value];
        }, 200);

        await scene.loadSplat(url);

        clearInterval(progressInterval);
        loadingItem.progress = 100;
        splatCount.value = scene.splats.length;
        loadProgress.value = 100;
        isLoading.value = false;

        // 移除加载提示
        setTimeout(() => {
            loadingNames.value = loadingNames.value.filter((item) => item.name !== fileName);
        }, 800);

        emit('loaded', fileName);
        emit('splat-count', splatCount.value);
        return true;
    } catch (err) {
        error.value = `加载失败: ${fileName} — ${err instanceof Error ? err.message : String(err)}`;
        emit('error', error.value);
        isLoading.value = false;
        loadingNames.value = loadingNames.value.filter((item) => item.name !== fileName);
        return false;
    }
}

/** 从 File 对象加载 */
async function loadFile(file: File): Promise<boolean> {
    if (!scene) return false;

    // 先检查文件格式（用原始文件名，而不是 blob URL）
    if (!isSupportedFormat(file.name)) {
        error.value = `不支持的文件格式: ${file.name}。支持的格式: .spz, .ply, .splat, .ksplat, .sog, .rad`;
        emit('error', error.value);
        return false;
    }

    const url = URL.createObjectURL(file);
    try {
        const result = await loadSplat(url, file.name);
        URL.revokeObjectURL(url);
        return result;
    } catch {
        URL.revokeObjectURL(url);
        return false;
    }
}

/** 拖放处理 */
async function onDrop(event: DragEvent) {
    const files = event.dataTransfer?.files;
    if (!files || files.length === 0) return;

    isLoading.value = true;
    for (const file of Array.from(files)) {
        if (isSupportedFormat(file.name)) {
            await loadFile(file);
        } else {
            error.value = `跳过不支持的文件: ${file.name}`;
        }
    }
    isLoading.value = false;
}

/** 重置相机 */
function resetCamera() {
    scene?.resetCamera();
}

/** 移除所有 splat（只从场景移除，不销毁，避免破坏渲染器状态） */
function clearAll() {
    if (!scene) return;
    for (const splat of [...scene.splats]) {
        // 从 Three.js 场景移除，但不调用 dispose()
        // 这样 SparkRenderer 内部状态不会损坏
        scene.scene.remove(splat);
        const idx = scene.splats.indexOf(splat);
        if (idx !== -1) scene.splats.splice(idx, 1);
    }
    splatCount.value = 0;
    emit('splat-count', 0);
}

// 暴露给父组件的方法
defineExpose({ loadSplat, loadFile, resetCamera, clearAll });

// --- 初始化 ---
onMounted(async () => {
    if (!containerRef.value) return;

    try {
        scene = await initSparkScene({
            container: containerRef.value,
            splatBudget: props.splatBudget,
        });

        // 如果有初始 src，自动加载
        if (props.src) {
            await loadSplat(props.src);
        }
    } catch (err) {
        error.value = `初始化失败: ${err instanceof Error ? err.message : String(err)}`;
    }
});

onUnmounted(() => {
    scene?.dispose();
});

// 监听 src 变化
watch(
    () => props.src,
    (newSrc) => {
        if (newSrc && scene) {
            // 先清除再加载
            clearAll();
            loadSplat(newSrc);
        }
    },
);
</script>

<style scoped>
.spark-viewer {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
    background: v-bind('props.backgroundColor');
}

.spark-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 10;
    pointer-events: none;
}

.spark-loading {
    text-align: center;
    color: #ccc;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255, 255, 255, 0.15);
    border-top-color: #6c63ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 16px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.progress-bar {
    width: 200px;
    height: 4px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 2px;
    margin-top: 12px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6c63ff, #48b0ff);
    border-radius: 2px;
    transition: width 0.3s ease;
}

.spark-empty-content {
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
    pointer-events: none;
}

.spark-empty-content svg {
    margin-bottom: 16px;
    opacity: 0.4;
}

.spark-empty-content h3 {
    font-size: 20px;
    font-weight: 500;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.6);
}

.spark-empty-content p {
    font-size: 14px;
    margin-bottom: 4px;
}

.spark-empty-content .sub {
    font-size: 12px;
    opacity: 0.6;
}

.spark-error {
    background: rgba(0, 0, 0, 0.7);
    color: #ff6b6b;
    pointer-events: auto;
}

.spark-error button {
    margin-top: 12px;
    padding: 6px 20px;
    border: 1px solid #ff6b6b;
    background: transparent;
    color: #ff6b6b;
    border-radius: 4px;
    cursor: pointer;
}

.spark-toast-list {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.spark-toast-item {
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    padding: 8px 14px;
    border-radius: 6px;
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 13px;
    color: #ccc;
}

.spark-toast-name {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.spark-toast-progress {
    color: #6c63ff;
    font-variant-numeric: tabular-nums;
}
</style>
