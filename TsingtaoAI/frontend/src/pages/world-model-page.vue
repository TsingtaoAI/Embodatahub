<template>
    <q-page class="world-model-page">
        <!-- 页面标题 -->
        <div class="page-header q-px-lg q-pt-md q-pb-sm">
            <div class="text-h5 text-weight-bold">世界模型训练</div>
            <div class="text-grey-7 q-mt-xs">具身智能 / 自动驾驶 3DGS 模型训练平台</div>
        </div>

        <!-- 状态栏 -->
        <div class="status-bar q-px-lg q-pb-sm row items-center q-gutter-md">
            <q-chip
                icon="sym_o_article"
                size="sm"
                color="grey-3"
                text-color="grey-8"
            >
                项目: world-model
            </q-chip>
            <q-chip
                icon="sym_o_folder"
                size="sm"
                color="grey-3"
                text-color="grey-8"
            >
                数据: world-model/data/
            </q-chip>
            <q-chip
                icon="sym_o_model_training"
                size="sm"
                color="primary"
                text-color="white"
                v-if="hasGpu"
            >
                GPU 可用
            </q-chip>
            <q-chip
                icon="sym_o_model_training"
                size="sm"
                color="orange-3"
                text-color="orange-9"
                v-else
            >
                GPU 不可用（仅演示）
            </q-chip>
        </div>

        <!-- 选项卡 -->
        <q-tabs
            v-model="currentTab"
            class="q-mx-lg tab-header"
            indicator-color="primary"
            align="left"
            narrow-indicator
        >
            <q-tab name="data-prep" label="数据提取" icon="sym_o_database" />
            <q-tab name="training" label="开始训练" icon="sym_o_model_training" />
            <q-tab name="results" label="训练完成" icon="sym_o_check_circle" />
        </q-tabs>

        <q-separator class="q-mx-lg" />

        <!-- 内容区域 -->
        <q-tab-panels v-model="currentTab" animated class="tab-panels">
            <!-- ═══ 数据提取 ═══ -->
            <q-tab-panel name="data-prep">
                <div class="row q-gutter-md">
                    <!-- 输入源选择 -->
                    <q-card class="col-12 col-md-5">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">数据源</div>
                            <q-list>
                                <q-item tag="label" v-ripple>
                                    <q-item-section avatar>
                                        <q-radio v-model="inputType" val="video" color="primary" />
                                    </q-item-section>
                                    <q-item-section>
                                        <q-item-label>视频文件</q-item-label>
                                        <q-item-label caption>上传 .mp4 / .avi / .mov 视频</q-item-label>
                                    </q-item-section>
                                </q-item>
                                <q-item tag="label" v-ripple>
                                    <q-item-section avatar>
                                        <q-radio v-model="inputType" val="rosbag" color="primary" />
                                    </q-item-section>
                                    <q-item-section>
                                        <q-item-label>ROS Bag</q-item-label>
                                        <q-item-label caption>上传 .bag / .mcap 文件</q-item-label>
                                    </q-item-section>
                                </q-item>
                                <q-item tag="label" v-ripple>
                                    <q-item-section avatar>
                                        <q-radio v-model="inputType" val="image_dir" color="primary" />
                                    </q-item-section>
                                    <q-item-section>
                                        <q-item-label>图像目录</q-item-label>
                                        <q-item-label caption>选择已有的图像序列目录</q-item-label>
                                    </q-item-section>
                                </q-item>
                            </q-list>

                            <q-separator class="q-my-md" />

                            <!-- 文件上传 -->
                            <div class="q-mt-md">
                                <q-file
                                    v-if="inputType === 'video'"
                                    v-model="videoFile"
                                    label="选择视频文件"
                                    accept=".mp4,.avi,.mov,.webm,.mkv"
                                    outlined
                                    dense
                                    class="q-mb-md"
                                >
                                    <template v-slot:prepend>
                                        <q-icon name="sym_o_videocam" />
                                    </template>
                                </q-file>
                                <q-file
                                    v-if="inputType === 'rosbag'"
                                    v-model="rosbagFile"
                                    label="选择 ROS Bag"
                                    accept=".bag,.mcap"
                                    outlined
                                    dense
                                    class="q-mb-md"
                                >
                                    <template v-slot:prepend>
                                        <q-icon name="sym_o_folder" />
                                    </template>
                                </q-file>
                                <q-input
                                    v-if="inputType === 'image_dir'"
                                    v-model="imageDirPath"
                                    label="图像目录路径"
                                    placeholder="如: /data/images"
                                    outlined
                                    dense
                                    class="q-mb-md"
                                />
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- 参数配置 -->
                    <q-card class="col-12 col-md-5">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">参数配置</div>
                            <q-input
                                v-model.number="extractFps"
                                label="提取帧率 (fps)"
                                type="number"
                                outlined
                                dense
                                class="q-mb-md"
                                hint="目标帧率, 如 2.0"
                            />
                            <q-input
                                v-model.number="maxFrames"
                                label="最大帧数"
                                type="number"
                                outlined
                                dense
                                class="q-mb-md"
                                hint="最多提取帧数, 如 300"
                            />
                            <q-input
                                v-model="sceneName"
                                label="场景名称"
                                outlined
                                dense
                                class="q-mb-md"
                                placeholder="如: street_scene_01"
                                hint="训练输出的场景标识"
                            />
                            <q-checkbox v-model="runColmap" label="运行 COLMAP 稀疏重建（需安装）" />
                        </q-card-section>
                        <q-card-actions align="right">
                            <q-btn
                                label="开始提取"
                                color="primary"
                                icon="sym_o_play_arrow"
                                :loading="isExtracting"
                                @click="startExtract"
                            />
                        </q-card-actions>
                    </q-card>

                    <!-- 提取日志 -->
                    <q-card class="col-12">
                        <q-card-section>
                            <div class="text-h6">提取日志</div>
                        </q-card-section>
                        <q-card-section class="log-container">
                            <div v-if="extractLogs.length === 0" class="text-grey-5 text-center q-pa-lg">
                                暂无日志，配置参数后点击「开始提取」
                            </div>
                            <div v-for="(log, i) in extractLogs" :key="i" class="log-line">
                                {{ log }}
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </q-tab-panel>

            <!-- ═══ 开始训练 ═══ -->
            <q-tab-panel name="training">
                <div class="row q-gutter-md">
                    <!-- 训练配置 -->
                    <q-card class="col-12 col-md-5">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">训练配置</div>
                            <q-select
                                v-model="trainScene"
                                :options="availableScenes"
                                label="选择场景数据"
                                outlined
                                dense
                                class="q-mb-md"
                                hint="已预处理完成的场景"
                            />
                            <q-input
                                v-model.number="trainIterations"
                                label="训练迭代次数"
                                type="number"
                                outlined
                                dense
                                class="q-mb-md"
                                :min="1000"
                                :max="100000"
                            />
                            <q-input
                                v-model="trainName"
                                label="模型名称"
                                outlined
                                dense
                                class="q-mb-md"
                                placeholder="如: my_street_model"
                            />
                            <q-select
                                v-model="trainConfigFile"
                                :options="['train_default.yaml', 'train_high_quality.yaml', 'train_fast.yaml']"
                                label="配置文件"
                                outlined
                                dense
                                class="q-mb-md"
                            />
                        </q-card-section>
                        <q-card-actions align="right">
                            <q-btn
                                label="开始训练"
                                color="primary"
                                icon="sym_o_model_training"
                                :loading="isTraining"
                                :disable="!trainScene"
                                @click="startTraining"
                            />
                        </q-card-actions>
                    </q-card>

                    <!-- 训练状态 -->
                    <q-card class="col-12 col-md-5">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">训练状态</div>
                            <div v-if="!isTraining && !trainingDone" class="text-grey-5 text-center q-pa-lg">
                                尚未开始训练
                            </div>
                            <div v-if="isTraining">
                                <div class="q-mb-md">
                                    当前迭代: <strong>{{ trainingProgress.currentStep }}</strong> / {{ trainingProgress.totalSteps }}
                                </div>
                                <q-linear-progress
                                    :value="trainingProgress.currentStep / trainingProgress.totalSteps"
                                    color="primary"
                                    class="q-mb-md"
                                    size="20px"
                                >
                                    <div class="absolute-full flex flex-center">
                                        {{ Math.round(trainingProgress.currentStep / trainingProgress.totalSteps * 100) }}%
                                    </div>
                                </q-linear-progress>
                                <q-list dense>
                                    <q-item>
                                        <q-item-section>Loss</q-item-section>
                                        <q-item-section side>{{ trainingProgress.loss }}</q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>高斯球数</q-item-section>
                                        <q-item-section side>{{ trainingProgress.numGaussians }}</q-item-section>
                                    </q-item>
                                    <q-item>
                                        <q-item-section>已用时间</q-item-section>
                                        <q-item-section side>{{ trainingProgress.elapsed }}</q-item-section>
                                    </q-item>
                                </q-list>
                            </div>
                            <div v-if="trainingDone" class="text-center q-pa-lg">
                                <q-icon name="sym_o_check_circle" size="48px" color="positive" />
                                <div class="text-h6 q-mt-sm text-positive">训练完成!</div>
                                <div class="text-grey-7 q-mt-xs">模型已保存至 outputs/models/</div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- 训练日志 -->
                    <q-card class="col-12">
                        <q-card-section>
                            <div class="text-h6">训练日志</div>
                        </q-card-section>
                        <q-card-section class="log-container">
                            <div v-if="trainLogs.length === 0" class="text-grey-5 text-center q-pa-lg">
                                暂无训练日志
                            </div>
                            <div v-for="(log, i) in trainLogs" :key="i" class="log-line">
                                {{ log }}
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </q-tab-panel>

            <!-- ═══ 训练完成 ═══ -->
            <q-tab-panel name="results">
                <div class="row q-gutter-md">
                    <!-- 模型列表 -->
                    <q-card class="col-12 col-md-6">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">已训练的模型</div>
                            <q-list v-if="trainedModels.length > 0" separator>
                                <q-item v-for="model in trainedModels" :key="model.name">
                                    <q-item-section avatar>
                                        <q-icon name="sym_o_model_training" color="primary" />
                                    </q-item-section>
                                    <q-item-section>
                                        <q-item-label>{{ model.name }}</q-item-label>
                                        <q-item-label caption>{{ model.size }}</q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-btn
                                            flat
                                            round
                                            color="primary"
                                            icon="sym_o_visibility"
                                            @click="viewModel(model)"
                                        >
                                            <q-tooltip>在 3D 查看器中打开</q-tooltip>
                                        </q-btn>
                                        <q-btn
                                            flat
                                            round
                                            color="positive"
                                            icon="sym_o_download"
                                            @click="downloadModel(model)"
                                        >
                                            <q-tooltip>下载模型</q-tooltip>
                                        </q-btn>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                            <div v-else class="text-grey-5 text-center q-pa-lg">
                                暂无已训练的模型
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- 模型信息 -->
                    <q-card class="col-12 col-md-4">
                        <q-card-section>
                            <div class="text-h6 q-mb-md">模型信息</div>
                            <div v-if="selectedModel" class="text-left">
                                <div class="q-mb-sm">
                                    <span class="text-grey-7">名称:</span>
                                    <strong class="q-ml-sm">{{ selectedModel.name }}</strong>
                                </div>
                                <div class="q-mb-sm">
                                    <span class="text-grey-7">格式:</span>
                                    <strong class="q-ml-sm">.ply（可转换为 .spz）</strong>
                                </div>
                                <div class="q-mb-sm">
                                    <span class="text-grey-7">大小:</span>
                                    <strong class="q-ml-sm">{{ selectedModel.size }}</strong>
                                </div>
                                <q-separator class="q-my-md" />
                                <div class="text-grey-7 q-mb-sm">操作:</div>
                                <q-btn
                                    flat
                                    color="primary"
                                    icon="sym_o_visibility"
                                    label="在 3D 查看器中打开"
                                    class="full-width q-mb-sm"
                                    @click="viewModel(selectedModel)"
                                />
                                <q-btn
                                    flat
                                    color="secondary"
                                    icon="sym_o_convert"
                                    label="转换为 .spz 格式"
                                    class="full-width q-mb-sm"
                                    :disable="true"
                                />
                                <q-btn
                                    flat
                                    color="negative"
                                    icon="sym_o_delete"
                                    label="删除模型"
                                    class="full-width"
                                />
                            </div>
                            <div v-else class="text-grey-5 text-center q-pa-lg">
                                选择一个模型查看详情
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </q-tab-panel>
        </q-tab-panels>
    </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import environment from 'src/environment';

// ─── 状态 ─────────────────────────────────────────────

const currentTab = ref('data-prep');
const hasGpu = ref(false);

// 数据提取
const inputType = ref('video');
const videoFile = ref<File | null>(null);
const rosbagFile = ref<File | null>(null);
const imageDirPath = ref('');
const extractFps = ref(2.0);
const maxFrames = ref(300);
const sceneName = ref('my_scene');
const runColmap = ref(false);
const isExtracting = ref(false);
const extractLogs = ref<string[]>([]);

// 训练
const trainScene = ref('');
const availableScenes = ref<string[]>(['暂无数据 - 请先在数据提取中准备']);
const trainIterations = ref(30000);
const trainName = ref('my_model');
const trainConfigFile = ref('train_default.yaml');
const isTraining = ref(false);
const trainingDone = ref(false);
const trainingProgress = reactive({
    currentStep: 0,
    totalSteps: 30000,
    loss: '-',
    numGaussians: '-',
    elapsed: '-',
});
const trainLogs = ref<string[]>([]);

// 训练完成
interface ModelInfo {
    name: string;
    size: string;
    path: string;
}
const trainedModels = ref<ModelInfo[]>([]);
const selectedModel = ref<ModelInfo | null>(null);

// ─── 方法 ─────────────────────────────────────────────

async function checkGpu(): Promise<void> {
    // 检查 GPU 是否可用（简单探测模式）
    hasGpu.value = true; // 默认假设有 GPU
}

async function startExtract(): Promise<void> {
    isExtracting.value = true;
    extractLogs.value = [];
    extractLogs.value.push(`[INFO] 开始数据提取...`);
    extractLogs.value.push(`[INFO] 场景名称: ${sceneName.value}`);
    extractLogs.value.push(`[INFO] 提取帧率: ${extractFps.value} fps`);
    extractLogs.value.push(`[INFO] 最大帧数: ${maxFrames.value}`);

    if (inputType.value === 'video' || inputType.value === 'rosbag') {
        const file = inputType.value === 'video' ? videoFile.value : rosbagFile.value;
        if (!file) {
            extractLogs.value.push('[ERROR] 请选择文件');
            isExtracting.value = false;
            return;
        }
        extractLogs.value.push(`[INFO] 文件名: ${file.name}`);
        extractLogs.value.push(`[INFO] 文件大小: ${(file.size / 1024 / 1024).toFixed(1)} MB`);
    } else if (inputType.value === 'image_dir') {
        extractLogs.value.push(`[INFO] 图像目录: ${imageDirPath.value}`);
    }

    // 模拟提取过程
    const totalFrames = Math.floor(Math.random() * 100) + 200;
    for (let i = 0; i < totalFrames; i++) {
        // 模拟进度
        if (i % 20 === 0) {
            extractLogs.value.push(`  [PROGRESS] 已提取 ${i}/${totalFrames} 帧...`);
        }
        await new Promise((r) => setTimeout(r, 5));
    }

    extractLogs.value.push(`[INFO] 数据提取完成! 共 ${totalFrames} 帧`);
    extractLogs.value.push(`[INFO] 输出目录: data/${sceneName.value}/train_data/images/`);

    // 更新可用场景列表
    availableScenes.value = [sceneName.value];
    trainScene.value = sceneName.value;

    isExtracting.value = false;
}

async function startTraining(): Promise<void> {
    isTraining.value = true;
    trainingDone.value = false;
    trainLogs.value = [];
    trainingProgress.currentStep = 0;
    trainingProgress.totalSteps = trainIterations.value;
    trainLogs.value.push('[INFO] 开始 3DGS 训练...');
    trainLogs.value.push(`[INFO] 场景: ${trainScene.value}`);
    trainLogs.value.push(`[INFO] 迭代次数: ${trainIterations.value}`);
    trainLogs.value.push(`[INFO] 配置文件: ${trainConfigFile.value}`);

    await new Promise((r) => setTimeout(r, 2000));

    // 模拟训练过程
    for (let step = 1; step <= trainIterations.value; step += 100) {
        trainingProgress.currentStep = step;
        trainingProgress.loss = `${(Math.random() * 0.1 + 0.01).toFixed(4)}`;
        trainingProgress.numGaussians = `${Math.floor(Math.random() * 50000 + 50000)}`;
        trainingProgress.elapsed = `${Math.floor(step / 100)}m ${Math.floor(Math.random() * 60)}s`;

        if (step % 1000 === 0) {
            trainLogs.value.push(`  [STEP ${step}] loss: ${trainingProgress.loss}, gaussians: ${trainingProgress.numGaussians}`);
        }

        await new Promise((r) => setTimeout(r, 2));
    }

    trainingProgress.currentStep = trainIterations.value;
    trainLogs.value.push('[INFO] ✅ 训练完成！');
    trainLogs.value.push(`[INFO] 模型已保存: outputs/models/${trainName.value}.ply`);

    // 添加到已训练模型列表
    const modelFile: ModelInfo = {
        name: trainName.value || `${trainScene.value}_model`,
        size: `${(Math.random() * 100 + 20).toFixed(0)} MB`,
        path: `outputs/models/${trainName.value || 'model'}.ply`,
    };
    trainedModels.value.unshift(modelFile);

    isTraining.value = false;
    trainingDone.value = true;
}

function viewModel(model: ModelInfo): void {
    selectedModel.value = model;
    // 跳转到 Spark Studio 并打开模型
    const frontendUrl = environment.SPARK_STUDIO_URL || 'http://localhost:5174';
    window.open(`${frontendUrl}?file=${encodeURIComponent(model.path)}`, '_blank');
}

function downloadModel(model: ModelInfo): void {
    // 下载模型文件
    const a = document.createElement('a');
    a.href = model.path;
    a.download = model.name;
    a.click();
}

// ─── 初始化 ───────────────────────────────────────────
onMounted(() => {
    checkGpu();
});
</script>

<style scoped>
.world-model-page {
    background: #f5f5f5;
    min-height: calc(100vh - 50px);
}

.tab-header {
    background: white;
    border-radius: 8px 8px 0 0;
}

.tab-panels {
    background: transparent;
}

.log-container {
    background: #1e1e2e;
    color: #a0e0a0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
    border-radius: 6px;
}

.log-line {
    padding: 2px 0;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
}

.status-bar {
    background: white;
    border-bottom: 1px solid #e0e0e0;
}
</style>
