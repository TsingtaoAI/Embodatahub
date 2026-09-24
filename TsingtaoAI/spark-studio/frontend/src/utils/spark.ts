/**
 * Spark 2.0 3DGS 渲染工具函数
 *
 * 封装 @sparkjsdev/spark 的核心初始化逻辑，
 * 提供场景管理、文件加载、格式支持等通用能力。
 */

import * as THREE from 'three';
import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark';

/** 支持的 3DGS 文件格式 */
export const SUPPORTED_FORMATS = ['.spz', '.ply', '.splat', '.ksplat', '.sog', '.rad'] as const;
export type SplatFormat = (typeof SUPPORTED_FORMATS)[number];

/** 判断是否为支持的 splat 文件格式 */
export function isSupportedFormat(filename: string): boolean {
    const lower = filename.toLowerCase();
    return SUPPORTED_FORMATS.some((ext) => lower.endsWith(ext));
}

/** 从 URL 猜测文件格式 */
export function guessFormat(url: string): SplatFormat | null {
    const match = url.match(/\.(spz|ply|splat|ksplat|sog|rad)(\?|$)/i);
    if (!match) return null;
    return `.${match[1].toLowerCase()}` as SplatFormat;
}

export interface SparkSceneOptions {
    /** 已有的 WebGLRenderer（可选，不传则自动创建） */
    renderer?: THREE.WebGLRenderer;
    /** 容器 DOM 元素 */
    container: HTMLElement;
    /** splat 预算（默认 2_500_000） */
    splatBudget?: number;
    /** 背景色（默认 0x1a1a2e） */
    backgroundColor?: number;
    /** 相机初始位置 */
    cameraPosition?: THREE.Vector3;
}

export interface SparkScene {
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    spark: SparkRenderer;
    controls: OrbitControlsProxy;
    /** 已加载的 SplatMesh 列表 */
    splats: SplatMesh[];
    /** 添加一个 splat 文件到场景 */
    loadSplat: (url: string, options?: Partial<SplatLoadOptions>) => Promise<SplatMesh>;
    /** 从场景中移除 splat */
    removeSplat: (splat: SplatMesh) => void;
    /** 清理所有资源 */
    dispose: () => void;
    /** 重置相机视角到最佳观看位置 */
    resetCamera: () => void;
}

export interface SplatLoadOptions {
    autoCenter: boolean;
    autoScale: boolean;
    position: THREE.Vector3;
    scale: number;
}

/**
 * 简单的轨道控制代理
 * 无需额外依赖，直接使用 Three.js 官方 OrbitControls
 */
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
type OrbitControlsProxy = OrbitControls;

/**
 * 初始化 Spark 3D 场景
 *
 * @example
 * ```ts
 * const scene = await initSparkScene({ container: document.getElementById('viewer')! });
 * await scene.loadSplat('/models/scene.spz');
 * ```
 */
export async function initSparkScene(options: SparkSceneOptions): Promise<SparkScene> {
    const {
        container,
        splatBudget,
        backgroundColor = 0x1a1a2e,
        cameraPosition = new THREE.Vector3(0, 0.5, 2),
    } = options;

    // --- 1. 场景 ---
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(backgroundColor);

    // --- 2. 相机 ---
    const aspect = container.clientWidth / container.clientHeight;
    const camera = new THREE.PerspectiveCamera(60, aspect, 0.01, 1000);
    camera.position.copy(cameraPosition);
    camera.lookAt(0, 0, 0);

    // --- 3. 渲染器 ---
    const renderer =
        options.renderer ??
        new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
        });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;

    if (!options.renderer) {
        container.appendChild(renderer.domElement);
    }

    // --- 4. 轨道控制器 ---
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 0.1;
    controls.maxDistance = 50;
    controls.target.set(0, 0, 0);

    // --- 5. SparkRenderer ---
    const spark = new SparkRenderer({ renderer });
    scene.add(spark);

    // --- 6. 环境光（协助传统 Three.js 对象视觉） ---
    const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(1, 2, 1);
    scene.add(dirLight);

    // --- 7. 辅助网格（可选） ---
    const gridHelper = new THREE.GridHelper(10, 20, 0x444466, 0x333355);
    scene.add(gridHelper);

    // --- 8. 窗口自适应 ---
    function onResize() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }
    window.addEventListener('resize', onResize);

    // --- 9. 渲染循环 ---
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    // --- 返回的场景对象 ---
    const splats: SplatMesh[] = [];

    async function loadSplat(
        url: string,
        loadOptions?: Partial<SplatLoadOptions>,
    ): Promise<SplatMesh> {
        const opts: SplatLoadOptions = {
            autoCenter: loadOptions?.autoCenter ?? false,
            autoScale: loadOptions?.autoScale ?? false,
            position: loadOptions?.position ?? new THREE.Vector3(0, 0, 0),
            scale: loadOptions?.scale ?? 1,
        };

        const splat = new SplatMesh({
            url,
            autoCenter: opts.autoCenter,
            autoScale: opts.autoScale,
        });

        splat.position.copy(opts.position);
        splat.scale.set(opts.scale, opts.scale, opts.scale);

        scene.add(splat);
        splats.push(splat);

        return splat;
    }

    function removeSplat(splat: SplatMesh) {
        scene.remove(splat);
        const idx = splats.indexOf(splat);
        if (idx !== -1) splats.splice(idx, 1);
        splat.dispose();
    }

    function resetCamera() {
        // 计算所有 splat 的包围盒
        const box = new THREE.Box3();
        let hasGeometry = false;
        for (const splat of splats) {
            if (splat.position) {
                box.expandByPoint(splat.position);
                hasGeometry = true;
            }
        }
        if (hasGeometry) {
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z, 1);
            const dist = maxDim * 1.5;
            controls.target.copy(center);
            camera.position.set(center.x, center.y, center.z + dist);
        } else {
            controls.target.set(0, 0, 0);
            camera.position.set(0, 0, 3);
        }
        controls.update();
    }

    function dispose() {
        window.removeEventListener('resize', onResize);
        controls.dispose();
        for (const splat of splats) {
            splat.dispose();
        }
        splats.length = 0;
        spark.dispose();
        renderer.dispose();
        if (!options.renderer && renderer.domElement.parentElement) {
            renderer.domElement.parentElement.removeChild(renderer.domElement);
        }
    }

    return {
        scene,
        camera,
        renderer,
        spark,
        controls,
        splats,
        loadSplat,
        removeSplat,
        dispose,
        resetCamera,
    };
}
