<template>
    <q-page class="about-page">
        <div class="q-pa-xl" style="max-width: 900px; margin: 0 auto">
            <!-- 项目信息 -->
            <q-card flat bordered class="q-mb-lg">
                <q-card-section>
                    <div class="text-h4 q-mb-md">RSL Studio</div>
                    <div class="text-subtitle1 text-grey-7 q-mb-md">
                        基于 RslStudio 二次开发的机器人数据管理平台
                    </div>
                    <q-separator class="q-mb-md" />
                    <div class="row q-col-gutter-md">
                        <div class="col-6">
                            <div class="text-caption text-grey">版本</div>
                            <div>v0.59.0</div>
                        </div>
                        <div class="col-6">
                            <div class="text-caption text-grey">许可证</div>
                            <div>MIT License</div>
                        </div>
                    </div>
                </q-card-section>
            </q-card>

            <!-- 核心开源项目 -->
            <q-card flat bordered class="q-mb-lg">
                <q-card-section>
                    <div class="text-h5 q-mb-sm">致谢</div>
                    <div class="text-body2 text-grey-7 q-mb-md">
                        本项目的开发和运行离不开以下优秀的开源项目。我们在此表示诚挚的感谢。
                    </div>
                </q-card-section>

                <q-separator />

                <q-list separator>
                    <q-item
                        v-for="project in openSourceProjects"
                        :key="project.name"
                        clickable
                        :href="project.url"
                        target="_blank"
                    >
                        <q-item-section>
                            <q-item-label class="text-weight-medium">{{
                                project.name
                            }}</q-item-label>
                            <q-item-label caption>
                                {{ project.description }}
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side top>
                            <q-badge
                                :label="project.license"
                                outline
                                color="grey-7"
                            />
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card>

            <!-- 第三方依赖声明 -->
            <q-card flat bordered>
                <q-card-section>
                    <div class="text-h5 q-mb-sm">第三方依赖声明</div>
                    <div class="text-body2 text-grey-7 q-mb-md">
                        本项目使用了以下开源仓库和依赖库，按许可证类型分类列出。使用时请遵守相应许可协议。
                    </div>
                </q-card-section>

                <q-separator />

                <q-expansion-item
                    v-for="(group, license) in groupedLicenses"
                    :key="license"
                    :label="`${license}`"
                    :caption="`${group.length} 个项目`"
                    header-class="text-weight-medium"
                >
                    <q-card>
                        <q-list separator dense>
                            <q-item
                                v-for="item in group"
                                :key="item.name"
                                dense
                            >
                                <q-item-section>
                                    <q-item-label class="text-body2">{{
                                        item.name
                                    }}</q-item-label>
                                    <q-item-label
                                        v-if="item.url"
                                        caption
                                        class="text-caption"
                                    >
                                        <a
                                            :href="item.url"
                                            target="_blank"
                                            class="text-grey"
                                            >{{ item.url }}</a
                                        >
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section
                                    v-if="item.author"
                                    side
                                    class="text-caption text-grey"
                                >
                                    {{ item.author }}
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>
                </q-expansion-item>
            </q-card>
        </div>
    </q-page>
</template>

<script setup lang="ts">
interface OpenSourceProject {
    name: string;
    description: string;
    url: string;
    license: string;
}

interface DependencyItem {
    name: string;
    license: string;
    url?: string;
    author?: string;
}

const openSourceProjects: OpenSourceProject[] = [
    {
        name: 'RslStudio (上游项目 Kleinkram)',
        description: '机器人数据管理平台（上游项目），支持多格式数据存储、自动化处理与精细化权限控制',
        url: 'https://github.com/leggedrobotics/GrandTourDatasets',
        license: 'MIT',
    },
    {
        name: 'Robot Data Studio',
        description: 'Local-first 机器人数据集检查、清洗、审查、回放与格式转换工作台',
        url: 'https://github.com/Peter-cuhk/robot-data-studio',
        license: 'Apache-2.0',
    },
    {
        name: 'NestJS',
        description: '用于构建高效、可扩展 Node.js 服务端应用的渐进式框架',
        url: 'https://nestjs.com/',
        license: 'MIT',
    },
    {
        name: 'Quasar Framework',
        description: '基于 Vue 3 的高性能跨平台前端框架',
        url: 'https://quasar.dev/',
        license: 'MIT',
    },
    {
        name: 'FastAPI',
        description: '高性能 Python Web 框架，用于构建 API',
        url: 'https://fastapi.tiangolo.com/',
        license: 'MIT',
    },
    {
        name: 'Rerun',
        description: '用于计算机视觉和机器人时序数据的可视化 SDK',
        url: 'https://rerun.io/',
        license: 'MIT',
    },
    {
        name: 'PostgreSQL',
        description: '强大的开源关系型数据库',
        url: 'https://www.postgresql.org/',
        license: 'PostgreSQL',
    },
    {
        name: 'Redis',
        description: '开源内存数据结构存储系统，用作缓存和消息代理',
        url: 'https://redis.io/',
        license: 'BSD-3-Clause',
    },
    {
        name: 'SeaweedFS',
        description: '分布式文件存储系统，用于对象存储（S3-compatible）',
        url: 'https://github.com/seaweedfs/seaweedfs',
        license: 'Apache-2.0',
    },
    {
        name: 'Vue 3',
        description: '渐进式 JavaScript 框架',
        url: 'https://vuejs.org/',
        license: 'MIT',
    },
    {
        name: 'Pinocchio',
        description: '高效的机器人运动学与动力学计算库',
        url: 'https://stack-of-tasks.github.io/pinocchio/',
        license: 'BSD-2-Clause',
    },

    // ── 新增：3D 视觉与模型训练 ─────────────────────
    {
        name: 'Spark 2.0 (World Labs)',
        description: '基于 Three.js + WebGL2 的 3D 高斯泼溅（3DGS）Web 渲染引擎，支持亿级 Splat 流式加载',
        url: 'https://github.com/sparkjsdev/spark',
        license: 'MIT',
    },
    {
        name: 'Three.js',
        description: '轻量级 3D JavaScript 库，WebGL2 渲染核心',
        url: 'https://threejs.org/',
        license: 'MIT',
    },
    {
        name: 'gsplat (nerfstudio-project)',
        description: 'CUDA 加速的 3D 高斯泼溅训练框架，PyTorch 原生实现',
        url: 'https://github.com/nerfstudio-project/gsplat',
        license: 'MIT',
    },
    {
        name: 'PyTorch',
        description: '开源深度学习框架，提供 GPU 加速的张量计算',
        url: 'https://pytorch.org/',
        license: 'BSD',
    },
    {
        name: 'Project Lyra (NVIDIA)',
        description: '生成式 3D 世界模型系列，支持单张图片/视频生成 3D 场景',
        url: 'https://github.com/nv-tlabs/lyra',
        license: 'Apache-2.0',
    },
    {
        name: 'COLMAP',
        description: '通用的运动恢复结构（SfM）和多视角立体（MVS）流水线',
        url: 'https://colmap.github.io/',
        license: 'BSD-3-Clause',
    },
    {
        name: 'TorchVision',
        description: 'PyTorch 的计算机视觉工具库，图像处理与数据加载',
        url: 'https://github.com/pytorch/vision',
        license: 'BSD',
    },
    {
        name: 'OpenCV',
        description: '开源计算机视觉库，视频处理与图像分析',
        url: 'https://opencv.org/',
        license: 'Apache-2.0',
    },
];

// 关键依赖分类
const dependencies: DependencyItem[] = [
    // 前端
    { name: 'Vue 3', license: 'MIT', url: 'https://vuejs.org/' },
    { name: 'Vue Router', license: 'MIT', url: 'https://router.vuejs.org/' },
    { name: 'Quasar', license: 'MIT', url: 'https://quasar.dev/' },
    { name: 'Vite', license: 'MIT', url: 'https://vitejs.dev/' },
    { name: 'TypeScript', license: 'Apache-2.0', url: 'https://www.typescriptlang.org/' },
    { name: 'ESLint', license: 'MIT', url: 'https://eslint.org/' },
    { name: 'Prettier', license: 'MIT', url: 'https://prettier.io/' },

    // 后端
    { name: 'NestJS', license: 'MIT', url: 'https://nestjs.com/' },
    { name: 'TypeORM', license: 'MIT', url: 'https://typeorm.io/' },
    { name: 'GraphQL', license: 'MIT', url: 'https://graphql.org/' },
    { name: 'RxJS', license: 'Apache-2.0', url: 'https://rxjs.dev/' },
    { name: 'bcrypt', license: 'MIT' },
    { name: 'Passport', license: 'MIT', url: 'https://www.passportjs.org/' },

    // Python
    { name: 'FastAPI', license: 'MIT', url: 'https://fastapi.tiangolo.com/' },
    { name: 'Uvicorn', license: 'BSD-3-Clause', url: 'https://www.uvicorn.org/' },
    { name: 'Rerun SDK', license: 'MIT', url: 'https://rerun.io/' },
    { name: 'H5py', license: 'BSD-3-Clause', url: 'https://www.h5py.org/' },
    { name: 'PyArrow', license: 'Apache-2.0', url: 'https://arrow.apache.org/' },
    { name: 'Zarr', license: 'MIT', url: 'https://zarr.dev/' },
    { name: 'NumPy', license: 'BSD-3-Clause', url: 'https://numpy.org/' },
    { name: 'Pydantic', license: 'MIT', url: 'https://pydantic.dev/' },
    { name: 'Pytest', license: 'MIT', url: 'https://pytest.org/' },

    // 3D 可视化与模型训练（新增）
    { name: '@sparkjsdev/spark', license: 'MIT', url: 'https://github.com/sparkjsdev/spark' },
    { name: 'Three.js', license: 'MIT', url: 'https://threejs.org/' },
    { name: 'gsplat', license: 'MIT', url: 'https://github.com/nerfstudio-project/gsplat' },
    { name: 'PyTorch', license: 'BSD', url: 'https://pytorch.org/' },
    { name: 'torchvision', license: 'BSD', url: 'https://github.com/pytorch/vision' },
    { name: 'OpenCV', license: 'Apache-2.0', url: 'https://opencv.org/' },
    { name: 'Ninja', license: 'Apache-2.0', url: 'https://ninja-build.org/' },
    { name: 'TensorBoard', license: 'Apache-2.0', url: 'https://www.tensorflow.org/tensorboard' },
    { name: 'Colmap', license: 'BSD-3-Clause', url: 'https://colmap.github.io/' },
    { name: 'Project Lyra', license: 'Apache-2.0', url: 'https://github.com/nv-tlabs/lyra' },

    // 基础设施
    { name: 'PostgreSQL', license: 'PostgreSQL', url: 'https://www.postgresql.org/' },
    { name: 'Redis', license: 'BSD-3-Clause', url: 'https://redis.io/' },
    { name: 'SeaweedFS', license: 'Apache-2.0', url: 'https://github.com/seaweedfs/seaweedfs' },
    { name: 'Docker', license: 'Apache-2.0', url: 'https://www.docker.com/' },
    { name: 'Nginx', license: 'BSD-2-Clause', url: 'https://nginx.org/' },
    { name: 'Grafana', license: 'AGPL-3.0', url: 'https://grafana.com/' },
    { name: 'Prometheus', license: 'Apache-2.0', url: 'https://prometheus.io/' },
];

const groupedLicenses = computed(() => {
    const groups: Record<string, DependencyItem[]> = {};
    for (const dep of dependencies) {
        const key = dep.license;
        if (!groups[key]) groups[key] = [];
        groups[key].push(dep);
    }
    // Sort by license name
    const sorted: Record<string, DependencyItem[]> = {};
    for (const key of Object.keys(groups).sort()) {
        sorted[key] = groups[key];
    }
    return sorted;
});

import { computed } from 'vue';
</script>

<style scoped>
.about-page {
    background: var(--q-background, #f5f5f5);
    min-height: 100%;
}

a {
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
</style>
