import * as process from 'node:process';

/**
 * Ensures extracted environment variable is a string
 *
 * @param value - extracted environment variable
 * @returns environment variable as string
 */
function asString(value: string | undefined): string {
    if (value === undefined) {
        const message = 'The environment variable cannot be "undefined".';
        throw new Error(message);
    }

    return value;
}

/**
 * Ensures extracted environment variable is a number
 *
 * @param value - extracted environment variable
 * @returns environment variable as integer
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function asNumber(value: string | undefined): number {
    const stringValue = asString(value);
    const numberValue = Number.parseFloat(stringValue);

    if (Number.isNaN(numberValue)) {
        const message = `The environment variable has to hold a stringified number value - not ${stringValue}`;
        throw new Error(message);
    }

    return numberValue;
}

/**
 * Ensures extracted environment variable is a boolean
 *
 * @param value - extracted environment variable
 * @returns environment variable as boolean
 */
function asBoolean(value: string | undefined): boolean {
    const stringVariable = asString(value);
    if (!(stringVariable === 'true' || stringVariable === 'false')) {
        const message = `The environment variable has to hold a stringified boolean value - not ${stringVariable}`;
        throw new Error(message);
    }
    return stringVariable === 'true';
}

/**
 * Ensures extracted environment variable is one of the provided values
 *
 * @param value - extracted environment variable
 * @param valueList - list of possible values
 * @returns environment variable
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function asOneOf<T extends string | number>(value: T, valueList: T[]): T {
    if (!valueList.includes(value)) {
        const message = `The environment variable must be one of the following: ${valueList.join(
            ',',
        )} - not ${value.toString()}`;
        throw new Error(message);
    }
    return value;
}

export default {
    /**
     * @returns Url of graphql backend endpoint
     * @example http://localhost:3000/graphql
     */
    get BACKEND_URL(): string {
        // 始终使用同源相对路径，由 Vite devServer proxy 转发 API 请求到后端
        // 避免 HTTPS 页面直接请求 HTTP 后端导致 Mixed Content 被拦截
        if (typeof window !== 'undefined') {
            return '';
        }
        const configuredUrl = import.meta.env.BACKEND_URL;
        return configuredUrl ?? 'http://localhost:3000';
    },

    get VERSION(): string {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        return asString(import.meta.env.VITE_QUASAR_VERSION ?? '0.0.0');
    },

    /**
     * @returns whether this build is a production build
     */
    get VUE_APP_PRODUCTION(): boolean {
        return asBoolean(process.env.VUE_APP_PRODUCTION);
    },
    /**
     * @returns whether application is in DEV mode
     */
    get DEV(): boolean {
        return asBoolean(process.env.DEV);
    },

    get USE_FAKE_OAUTH_FOR_DEVELOPMENT(): boolean {
        return asBoolean(
            // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
            import.meta.env.VITE_USE_FAKE_OAUTH_FOR_DEVELOPMENT ?? 'false',
        );
    },

    get DOCS_URL(): string {
        return asString(
            // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
            import.meta.env.VITE_DOCS_URL ?? 'https://docs.rslstudio.com',
        );
    },
    get S3_ENDPOINT(): string {
        const endpoint = import.meta.env.VITE_S3_ENDPOINT as string | undefined;
        if (endpoint) {
            return asString(endpoint);
        }

        // 使用与主页面相同的主机名，支持本地和远程访问
        if (typeof window !== 'undefined') {
            const hostname = window.location.hostname;
            const host = (hostname === 'localhost' || hostname === '127.0.0.1')
                ? 'localhost'
                : hostname;
            return `http://${host}:9000`;
        }

        return asString('http://localhost:9000');
    },

    /**
     * @returns URL of the Robot Data Studio frontend
     * @example http://localhost:5173
     */
    get RDS_FRONTEND_URL(): string {
        if (typeof window !== 'undefined') {
            // 生产:子应用由主站 nginx 挂在同源 /rds/ 下;dev:RDS 独立跑在 :5173
            if (!import.meta.env.DEV) return `${window.location.origin}/rds-app/`;
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            // 本地访问用 localhost，远程访问用相同 hostname
            const host = (hostname === 'localhost' || hostname === '127.0.0.1')
                ? 'localhost'
                : hostname;
            return `${protocol}//${host}:5173`;
        }
        return asString(
            import.meta.env.VITE_RDS_FRONTEND_URL ?? 'https://localhost:5173',
        );
    },

    /**
     * @returns URL of the Spark Studio frontend
     * @example https://localhost:5174
     */
    get SPARK_STUDIO_URL(): string {
        if (typeof window !== 'undefined') {
            // 生产:子应用由主站 nginx 挂在同源 /spark/ 下;dev:Spark 独立跑在 :5174
            if (!import.meta.env.DEV) return `${window.location.origin}/spark/`;
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            // 本地访问用 localhost，远程访问用相同 hostname
            const host = (hostname === 'localhost' || hostname === '127.0.0.1')
                ? 'localhost'
                : hostname;
            return `${protocol}//${host}:5174`;
        }
        return asString(
            import.meta.env.VITE_SPARK_STUDIO_URL ?? 'https://localhost:5174',
        );
    },
};
