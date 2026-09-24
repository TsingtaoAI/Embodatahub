<template>
    <div class="scene-controls">
        <!-- 左侧：文件操作 -->
        <div class="controls-group">
            <button class="ctrl-btn" title="打开文件" @click="triggerFileInput">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                打开
            </button>
            <input
                ref="fileInputRef"
                type="file"
                accept=".spz,.ply,.splat,.ksplat,.sog,.rad"
                multiple
                style="display:none"
                @change="onFileSelected"
            />

            <button class="ctrl-btn" title="重置视角" @click="$emit('reset-camera')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
                重置视角
            </button>

            <button v-if="splatCount > 0" class="ctrl-btn ctrl-btn-danger" title="清除所有" @click="$emit('clear-all')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                清除
            </button>
        </div>

        <!-- 右侧：信息 -->
        <div class="controls-info">
            <span class="splat-count" v-if="splatCount > 0">
                {{ splatCount }} 个场景
            </span>
            <span class="fps" v-if="showFps">{{ fps }} FPS</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
    splatCount: number;
    showFps?: boolean;
    fps?: number;
}>();

const emit = defineEmits<{
    (e: 'open-file'): void;
    (e: 'reset-camera'): void;
    (e: 'clear-all'): void;
}>();

const fileInputRef = ref<HTMLInputElement | null>(null);

function triggerFileInput() {
    fileInputRef.value?.click();
}

function onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
        // 通过自定义事件向上传递文件列表
        emit('open-file');
        // 使用 CustomEvent 通知父组件
        window.dispatchEvent(new CustomEvent('spark-files-selected', { detail: { files: Array.from(input.files) } }));
    }
    // 重置以便重复选择同一文件
    input.value = '';
}
</script>

<style scoped>
.scene-controls {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    background: linear-gradient(180deg, rgba(0,0,0,0.5) 0%, transparent 100%);
    z-index: 20;
    pointer-events: none;
}

.controls-group {
    display: flex;
    gap: 6px;
    pointer-events: auto;
}

.ctrl-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.4);
    backdrop-filter: blur(8px);
    color: rgba(255,255,255,0.85);
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
}

.ctrl-btn:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.3);
}

.ctrl-btn-danger:hover {
    border-color: #ff6b6b;
    color: #ff6b6b;
}

.controls-info {
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 12px;
    color: rgba(255,255,255,0.5);
    pointer-events: none;
}
</style>
