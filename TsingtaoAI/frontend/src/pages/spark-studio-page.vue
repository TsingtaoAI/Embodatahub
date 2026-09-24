<template>
    <q-page class="spark-page">
        <iframe
            ref="sparkIframeRef"
            :src="sparkStudioUrl"
            class="spark-iframe"
            frameborder="0"
            allow="clipboard-read; clipboard-write"
            @load="onIframeLoaded"
        />
        <div v-if="loading" class="spark-loading-overlay">
            <q-spinner
                size="48px"
                color="primary"
                class="q-mb-md"
            />
            <div class="text-grey-7">正在加载 3D 场景可视化...</div>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import environment from 'src/environment';

const $route = useRoute();
const loading = ref(true);
const sparkIframeRef = ref<HTMLIFrameElement | null>(null);
// postMessage 的 targetOrigin 必须是纯 origin(带路径会抛 SyntaxError)
const sparkOrigin = new URL(environment.SPARK_STUDIO_URL).origin;

/**
 * 构建 Spark Studio iframe URL，传递查询参数
 */
const sparkStudioUrl = computed(() => {
    let url = environment.SPARK_STUDIO_URL;

    // 传递文件路径参数（如果有）
    const filePath = $route.query.file as string | undefined;
    const params = new URLSearchParams();
    if (filePath) {
        params.set('file', filePath);
    }

    const queryString = params.toString();
    if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
    }

    return url;
});

/**
 * iframe 加载完成后的回调
 */
const onIframeLoaded = (): void => {
    loading.value = false;

    // 通知 Spark iframe 父窗口的源地址
    const iframe = sparkIframeRef.value;
    if (iframe?.contentWindow) {
        iframe.contentWindow.postMessage(
            {
                type: 'spark-parent-origin',
                payload: {
                    origin: window.location.origin,
                    referrer: document.referrer,
                },
            },
            sparkOrigin,
        );
    }
};

/**
 * 监听来自 Spark iframe 的消息
 */
const handleMessage = (event: MessageEvent): void => {
    // 只接受来自 Spark Studio 源的消息
    if (event.origin !== sparkOrigin) return;

    const { type } = event.data || {};

    if (type === 'spark-ready') {
        // Spark Studio 已就绪，可以发送信息
        const iframe = sparkIframeRef.value;
        if (iframe?.contentWindow) {
            iframe.contentWindow.postMessage(
                {
                    type: 'spark-set-config',
                    payload: {
                        source: 'rsl-studio',
                        theme: 'dark',
                    },
                },
                sparkOrigin,
            );
        }
    }
};

onMounted(() => {
    window.addEventListener('message', handleMessage);
});

onUnmounted(() => {
    window.removeEventListener('message', handleMessage);
});
</script>

<style scoped>
.spark-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    position: relative;
}

.spark-iframe {
    width: 100%;
    height: 100%;
    border: none;
    flex: 1;
}

.spark-loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--q-background, #fff);
    z-index: 1;
}
</style>
