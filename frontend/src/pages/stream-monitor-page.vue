<template>
  <q-page padding>
    <div class="stream-monitor">
      <!-- 头部 -->
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h5">
          📡 实时采集监控
          <q-badge v-if="activeCount" color="green" class="q-ml-sm">
            {{ activeCount }} 活跃
          </q-badge>
        </div>
        <div class="q-gutter-sm">
          <q-btn color="green" icon="sym_o_fiber_manual_record" label="启动采集" @click="showDialog = true" />
          <q-btn color="primary" icon="sym_o_refresh" label="刷新" @click="fetchStreams" />
        </div>
      </div>

      <!-- 启动采集对话框 -->
      <q-dialog v-model="showDialog" persistent>
        <q-card style="min-width: 420px">
          <q-card-section class="row items-center">
            <q-icon name="fiber_manual_record" color="green" size="24px" class="q-mr-sm" />
            <div class="text-h6">启动实时采集</div>
          </q-card-section>
          <q-card-section>
            <q-select
              v-model="captureType"
              :options="captureTypes"
              label="采集源类型"
              class="q-mb-md"
            />
            <q-input
              v-model="captureSource"
              :label="captureType === 'rtsp' ? 'RTSP 地址' : '设备路径'"
              :hint="captureType === 'usb' ? '例如: /dev/video0' : '例如: rtsp://192.168.1.50:554/stream'"
              class="q-mb-md"
            />
            <q-input
              v-model="captureMission"
              label="采集任务名"
              hint="用于在 MinIO 中组织数据: streams/{任务名}/日期/"
              class="q-mb-md"
            />
            <q-input
              v-model="captureSegment"
              label="分段时长 (秒)"
              type="number"
              :min="5"
              :max="60"
              hint="建议 10-30 秒"
            />
          </q-card-section>
          <q-card-section class="bg-grey-2">
            <div class="text-caption text-grey-8">等效命令行:</div>
            <code class="text-caption cmd-preview">{{ generatedCmd }}</code>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="复制命令" color="primary" icon="sym_o_content_copy" @click="copyCmd" />
            <q-btn flat label="取消" color="negative" v-close-popup />
            <q-btn
              unelevated
              color="green"
              label="▶ 启动采集"
              icon="sym_o_play_arrow"
              :loading="startingCapture"
              @click="startCapture"
            />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <!-- 空状态 -->
      <div v-if="streams.length === 0" class="text-center q-pa-xl text-grey-6">
        <q-icon name="sym_o_videocam_off" size="64px" />
        <div class="text-h6 q-mt-md">暂无活跃采集流</div>
        <div class="q-mt-sm">
          点击<b>"启动采集"</b>按钮开始，或在终端运行 edge-agent.py
        </div>
      </div>

      <!-- 采集流程图 -->
      <div class="pipeline-flow q-mb-lg" :class="{ 'has-streams': streams.length > 0 }">
        <div class="flow-row">
          <!-- 步骤 1: 视频源 -->
          <div class="flow-step" :class="{ active: streams.length > 0 }">
            <div class="flow-icon">
              <q-icon name="sym_o_videocam" size="28px" />
            </div>
            <div class="flow-label">
              <div class="flow-title">采集源</div>
              <div class="flow-desc">USB / RTSP</div>
            </div>
          </div>
          <div class="flow-arrow">→</div>

          <!-- 步骤 2: FFmpeg -->
          <div class="flow-step" :class="{ active: streams.length > 0 }">
            <div class="flow-icon">
              <q-icon name="sym_o_settings" size="28px" />
            </div>
            <div class="flow-label">
              <div class="flow-title">FFmpeg 分段</div>
              <div class="flow-desc">{{ segmentDesc }}</div>
            </div>
          </div>
          <div class="flow-arrow">→</div>

          <!-- 步骤 3: MinIO -->
          <div class="flow-step" :class="{ active: anyUploaded }">
            <div class="flow-icon">
              <q-icon name="sym_o_cloud_upload" size="28px" />
            </div>
            <div class="flow-label">
              <div class="flow-title">MinIO 直传</div>
              <div class="flow-desc">S3 API 断点续传</div>
            </div>
          </div>
          <div class="flow-arrow">→</div>

          <!-- 步骤 4: 平台 -->
          <div class="flow-step" :class="{ active: anyUploaded }">
            <div class="flow-icon">
              <q-icon name="sym_o_check_circle" size="28px" />
            </div>
            <div class="flow-label">
              <div class="flow-title">平台注册</div>
              <div class="flow-desc">{{ totalDesc }}</div>
            </div>
          </div>
          <div class="flow-arrow">→</div>

          <!-- 步骤 5: 质检 -->
          <div class="flow-step" :class="{ active: anyUploaded }">
            <div class="flow-icon">
              <q-icon name="sym_o_fact_check" size="28px" />
            </div>
            <div class="flow-label">
              <div class="flow-title">数据集质检</div>
              <div class="flow-desc">自动触发</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 采集流卡片 -->
      <div class="row q-col-gutter-md">
        <div v-for="stream in streams" :key="stream.id" class="col-12 col-md-6 col-lg-4">
          <q-card :class="{ 'stream-card': true, 'disconnected': stream.status === 'disconnected' }">
            <!-- 状态指示器 -->
            <q-card-section horizontal>
              <q-card-section class="q-pa-sm">
                <q-icon
                  :name="statusIcon(stream.status)"
                  :color="statusColor(stream.status)"
                  size="32px"
                  :class="{ 'pulse-animation': stream.status === 'active' }"
                />
              </q-card-section>
              <q-card-section class="q-pa-sm col">
                <div class="text-h6">{{ stream.mission }}</div>
                <div class="text-caption text-grey-7">{{ stream.source }}</div>
                <div class="text-caption">
                  已运行 {{ formatDuration(stream.duration) }}
                </div>
              </q-card-section>
            </q-card-section>

            <!-- 指标 -->
            <q-card-section class="q-pa-sm">
              <div class="row text-center">
                <div class="col">
                  <div class="text-h5 text-primary">{{ stream.metrics.segmentsUploaded }}</div>
                  <div class="text-caption">分段数</div>
                </div>
                <div class="col">
                  <div class="text-h5 text-primary">{{ formatBytes(stream.metrics.bytesUploaded) }}</div>
                  <div class="text-caption">已上传</div>
                </div>
                <div class="col">
                  <div class="text-h5" :class="stream.metrics.queueDepth > 10 ? 'text-orange' : ''">
                    {{ stream.metrics.queueDepth }}
                  </div>
                  <div class="text-caption">待上传</div>
                </div>
                <div class="col">
                  <div class="text-h5" :class="stream.metrics.errors > 0 ? 'text-red' : ''">
                    {{ stream.metrics.errors }}
                  </div>
                  <div class="text-caption">错误</div>
                </div>
              </div>
            </q-card-section>

            <!-- S3 路径 -->
            <q-card-section class="q-pa-sm bg-grey-2">
              <div class="text-caption text-grey-8 ellipsis">
                s3://{{ stream.s3Prefix }}
              </div>
            </q-card-section>

            <!-- 操作 -->
            <q-card-actions align="right">
              <q-btn
                flat dense color="grey" icon="sym_o_open_in_new"
                label="查看文件" @click="openFiles(stream)"
              />
              <q-btn
                v-if="stream.status !== 'stopped'"
                flat dense color="red" icon="sym_o_stop"
                label="停止" @click="stopStream(stream.id)"
              />
            </q-card-actions>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useQuasar } from 'quasar';
import axios from 'src/api/axios';

const $q = useQuasar();

// ── 对话框 ──
const showDialog = ref(false);
const startingCapture = ref(false);
const captureType = ref('usb');
const captureTypes = [
  { label: 'USB 摄像头', value: 'usb' },
  { label: 'RTSP 网络流', value: 'rtsp' },
];
const captureSource = ref('/dev/video0');
const captureMission = ref('my-capture');
const captureSegment = ref(10);

const generatedCmd = computed(() => {
  return [
    'cd ~/rslstudio',
    'python3 scripts/edge-agent.py',
    `--source ${captureSource.value}`,
    `--mission ${captureMission.value}`,
    `--segment ${captureSegment.value}`,
  ].join(' \\\n    ');
});

function copyCmd() {
  navigator.clipboard.writeText(generatedCmd.value.replace(/ \\\n    /g, ' '));
  $q.notify({ message: '命令已复制到剪贴板', color: 'green', icon: 'check', timeout: 2000 });
}

async function startCapture() {
  startingCapture.value = true;
  try {
    await axios.post('/api/streams/start-capture', {
      source: captureSource.value,
      mission: captureMission.value,
      segmentSeconds: captureSegment.value,
    });
    $q.notify({ message: '采集已启动，等待代理上线...', color: 'green', icon: 'play_arrow' });
    showDialog.value = false;
    setTimeout(fetchStreams, 3000);
  } catch (e: any) {
    $q.notify({
      message: e.response?.data?.message || '启动失败，请检查采集设备连接',
      color: 'red',
      icon: 'error',
    });
  } finally {
    startingCapture.value = false;
  }
}

// ── 数据 ──

interface StreamMetrics {
  segmentsUploaded: number;
  bytesUploaded: number;
  reconnectCount: number;
  errors: number;
  queueDepth: number;
}

interface StreamSession {
  id: string;
  mission: string;
  source: string;
  status: 'active' | 'disconnected' | 'stopped';
  startedAt: string;
  lastHeartbeat: string;
  duration: number;
  metrics: StreamMetrics;
  s3Prefix: string;
  healthEndpoint?: string;
}

const streams = ref<StreamSession[]>([]);
const activeCount = ref(0);
let eventSource: EventSource | null = null;

const segmentDesc = computed(() => {
  // 显示所有采集流的平均分段配置
  return '10s MP4 分片';
});
const totalDesc = computed(() => {
  const total = streams.value.reduce((s, st) => s + st.metrics.segmentsUploaded, 0);
  return total > 0 ? `已注册 ${total} 分段` : '等待数据';
});
const anyUploaded = computed(() => {
  return streams.value.some(s => s.metrics.segmentsUploaded > 0);
});
let pollTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  fetchStreams();
  // 定期轮询作为 SSE 的兜底
  pollTimer = setInterval(fetchStreams, 5000);
});

onUnmounted(() => {
  if (eventSource) eventSource.close();
  if (pollTimer) clearInterval(pollTimer);
});

async function fetchStreams() {
  try {
    const resp = await axios.get('/api/streams');
    streams.value = resp.data.streams || [];
    activeCount.value = resp.data.count || 0;
  } catch {
    // 后端可能还没有 stream 端点
  }
}

async function stopStream(id: string) {
  try {
    await axios.post(`/api/streams/${id}/stop`);
    fetchStreams();
  } catch (e) {
    console.error('停止失败', e);
  }
}

function openFiles(stream: StreamSession) {
  const url = `http://192.168.1.107:9001/buckets/data/browse/${stream.s3Prefix}`;
  window.open(url, '_blank');
}

function statusIcon(status: string): string {
  return {
    active: 'sym_o_fiber_manual_record',
    disconnected: 'sym_o_wifi_off',
    stopped: 'sym_o_stop_circle',
  }[status] || 'sym_o_help';
}

function statusColor(status: string): string {
  return {
    active: 'green',
    disconnected: 'orange',
    stopped: 'grey',
  }[status] || 'grey';
}

function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}
</script>

<style scoped>
.stream-card {
  transition: all 0.3s;
  border-left: 4px solid #4caf50;
}
.stream-card.disconnected {
  border-left-color: #ff9800;
  opacity: 0.8;
}

/* ── 流程图 ── */
.pipeline-flow {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px;
  padding: 16px 24px;
}
.pipeline-flow.has-streams {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
}
.flow-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  flex-wrap: wrap;
}
.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 12px;
  border-radius: 10px;
  min-width: 90px;
  transition: all 0.4s;
  opacity: 0.5;
  filter: grayscale(0.8);
}
.flow-step.active {
  opacity: 1;
  filter: none;
}
.flow-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #bdbdbd;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  transition: all 0.4s;
}
.flow-step.active .flow-icon {
  background: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
}
.flow-title {
  font-size: 13px;
  font-weight: 600;
  color: #424242;
}
.flow-desc {
  font-size: 11px;
  color: #757575;
  margin-top: 2px;
}
.flow-arrow {
  font-size: 24px;
  color: #bdbdbd;
  margin: 0 4px 16px;
  transition: color 0.4s;
}
.pipeline-flow.has-streams .flow-arrow {
  color: #1976d2;
}
.cmd-preview {
  display: block;
  background: #263238;
  color: #a5d6a7;
  padding: 10px 14px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .flow-row { justify-content: flex-start; }
  .flow-step { min-width: 60px; padding: 6px; }
  .flow-arrow { font-size: 18px; margin: 0 2px 16px; }
}
.pulse-animation {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
