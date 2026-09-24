/// <reference types="vite/client" />

declare module '*.vue' {
    import type { DefineComponent } from 'vue';
    const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
    export default component;
}

declare module '@sparkjsdev/spark' {
    import type { Object3D, Material, BufferGeometry } from 'three';

    export interface SparkRendererOptions {
        renderer: THREE.WebGLRenderer;
        /** 最大 splat 预算（默认移动端 500K，桌面 2.5M） */
        splatBudget?: number;
        /** 是否启用 VR */
        xr?: boolean;
    }

    export class SparkRenderer extends Object3D {
        constructor(options: SparkRendererOptions);
        /** 设置 splat 质量预算 */
        setSplatBudget(budget: number): void;
        /** 销毁清理 */
        dispose(): void;
    }

    export interface SplatMeshOptions {
        url: string;
        /** 加载后自动居中 */
        autoCenter?: boolean;
        /** 自动缩放以适应场景 */
        autoScale?: boolean;
        /** 加载优先级 */
        priority?: number;
    }

    export class SplatMesh extends Object3D {
        constructor(options: SplatMeshOptions);
        /** 加载进度 0-1 */
        progress: number;
        /** 是否已加载完成 */
        loaded: boolean;
        /** 销毁释放 GPU 资源 */
        dispose(): void;
        /** reload from a new URL */
        load(url: string): Promise<void>;
    }
}
