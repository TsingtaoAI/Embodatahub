<template>
    <div class="splat-info" v-if="visible">
        <div class="splat-info-header">
            <span>场景信息</span>
            <button class="close-btn" @click="$emit('close')">✕</button>
        </div>
        <div class="splat-info-body">
            <div class="info-row">
                <span class="label">模型数</span>
                <span class="value">{{ splatCount }}</span>
            </div>
            <div class="info-row" v-if="currentFile">
                <span class="label">当前文件</span>
                <span class="value file-name">{{ currentFile }}</span>
            </div>
            <div class="info-row">
                <span class="label">渲染器</span>
                <span class="value">Spark 2.0 (WebGL2)</span>
            </div>
            <div class="info-row" v-if="gpuInfo">
                <span class="label">GPU</span>
                <span class="value">{{ gpuInfo }}</span>
            </div>
            <div class="info-divider"></div>
            <div class="info-hint">
                支持格式: .spz .ply .splat .ksplat .sog .rad
            </div>
            <div class="info-hint">
                拖放文件到场景中加载
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineProps<{
    visible: boolean;
    splatCount: number;
    currentFile?: string;
}>();

defineEmits<{
    (e: 'close'): void;
}>();

const gpuInfo = ref('');

onMounted(() => {
    // 尝试获取 GPU 信息
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2');
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                gpuInfo.value = renderer;
            }
            gl.getExtension('WEBGL_lose_context')?.loseContext();
        }
    } catch {
        // 忽略 GPU 信息获取失败
    }
});
</script>

<style scoped>
.splat-info {
    position: absolute;
    bottom: 12px;
    left: 12px;
    width: 240px;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    z-index: 20;
    color: rgba(255,255,255,0.85);
    font-size: 13px;
}

.splat-info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    font-weight: 500;
}

.close-btn {
    background: none;
    border: none;
    color: rgba(255,255,255,0.4);
    cursor: pointer;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
}

.close-btn:hover {
    color: #fff;
    background: rgba(255,255,255,0.1);
}

.splat-info-body {
    padding: 10px 12px;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
}

.label {
    color: rgba(255,255,255,0.5);
}

.value {
    color: rgba(255,255,255,0.9);
}

.file-name {
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: right;
}

.info-divider {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 8px 0;
}

.info-hint {
    color: rgba(255,255,255,0.35);
    font-size: 11px;
    padding: 2px 0;
}
</style>
