<template>
    <q-page class="rds-page">
        <iframe
            ref="rdsIframeRef"
            :src="rdsUrl"
            class="rds-iframe"
            frameborder="0"
            allow="clipboard-read; clipboard-write"
            @load="onIframeLoaded"
        />
        <div v-if="loading" class="rds-loading-overlay">
            <q-spinner
                size="48px"
                color="primary"
                class="q-mb-md"
            />
            <div class="text-grey-7">{{ loadingText }}</div>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import environment from 'src/environment';

const $route = useRoute();
const { locale } = useI18n();
const loading = ref(true);
const loadError = ref(false);
const rdsIframeRef = ref<HTMLIFrameElement | null>(null);
// postMessage 的 targetOrigin 必须是纯 origin(带路径会抛 SyntaxError)
const rdsOrigin = new URL(environment.RDS_FRONTEND_URL).origin;
let loadTimer: ReturnType<typeof setTimeout> | null = null;

const RDS_LOAD_TIMEOUT_MS = 30_000; // 30 秒超时

/** 从路由路径中检测当前页面 */
const rdsPage = computed(() => {
    const path = $route.path;
    if (path.endsWith('/vlm')) return 'vlm';
    if (path.endsWith('/import')) return 'import';
    return 'quality';
});

const loadingText = computed(() => {
    if (loadError.value) {
        if (rdsPage.value === 'quality') return '数据集质检服务未启动，请运行 scripts/start-all.sh';
        return 'RDS 服务不可用，请检查服务状态';
    }
    if (rdsPage.value === 'vlm') return '正在加载 VLM 设置...';
    if (rdsPage.value === 'import') return '正在加载导入页面...';
    return '正在加载数据集质检工作台...';
});

/**
 * 构建 RDS iframe URL，传递查询参数
 */
const rdsUrl = computed(() => {
    let url = environment.RDS_FRONTEND_URL;

    // 传递查询参数
    const params = new URLSearchParams();
    const datasetPath = $route.query.dataset as string | undefined;
    if (datasetPath) {
        params.set('dataset', datasetPath);
    }
    if (rdsPage.value !== 'quality') {
        params.set('page', rdsPage.value);
    }
    // 传递项目上下文
    const projectUuid = $route.query.projectUuid as string | undefined;
    if (projectUuid) {
        params.set('projectUuid', projectUuid);
    }
    const projectName = $route.query.projectName as string | undefined;
    if (projectName) {
        params.set('projectName', projectName);
    }
    // 同步语言到 RDS iframe
    if (locale.value) {
        params.set('lang', locale.value === 'zh-CN' ? 'zh' : 'en');
    }

    const queryString = params.toString();
    if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
    }

    return url;
});

/**
 * iframe 加载完成后的回调
 * 通过 postMessage 发送认证信息到 RDS
 */
const onIframeLoaded = (): void => {
    if (loadTimer) clearTimeout(loadTimer);
    loading.value = false;
    loadError.value = false;

    // 通知 RDS iframe 父窗口的源地址（用于 CORS 配置）
    const iframe = rdsIframeRef.value;
    if (iframe?.contentWindow) {
        iframe.contentWindow.postMessage(
            {
                type: 'rds-parent-origin',
                payload: {
                    origin: window.location.origin,
                    referrer: document.referrer,
                },
            },
            rdsOrigin,
        );
    }
};

/**
 * 监听来自 RDS iframe 的消息
 */
const handleMessage = (event: MessageEvent): void => {
    // 只接受来自 RDS 源的消息
    if (event.origin !== rdsOrigin) return;

    const { type } = event.data || {};

    if (type === 'rds-ready') {
        // RDS 已就绪，可以再次发送信息
        const iframe = rdsIframeRef.value;
        if (iframe?.contentWindow) {
            iframe.contentWindow.postMessage(
                {
                    type: 'rds-set-token',
                    payload: {
                        // 当前无 token 场景，保留扩展
                        source: 'rsl-studio',
                    },
                },
                rdsOrigin,
            );
        }
    }
};

// 超时处理：30 秒后仍未加载则显示错误提示
const startLoadTimer = (): void => {
    loadTimer = setTimeout(() => {
        if (loading.value) {
            loadError.value = true;
        }
    }, RDS_LOAD_TIMEOUT_MS);
};

onMounted(() => {
    window.addEventListener('message', handleMessage);
    startLoadTimer();
});

onUnmounted(() => {
    window.removeEventListener('message', handleMessage);
    if (loadTimer) clearTimeout(loadTimer);
});
</script>

<style scoped>
.rds-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    position: relative;
}

.rds-iframe {
    width: 100%;
    height: 100%;
    border: none;
    flex: 1;
}

.rds-loading-overlay {
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
