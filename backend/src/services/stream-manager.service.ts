import { Injectable, Logger } from '@nestjs/common';

/** 采集流会话 */
export interface StreamSession {
    id: string;
    mission: string;
    source: string;
    status: 'active' | 'disconnected' | 'stopped';
    startedAt: Date;
    lastHeartbeat: Date;
    metrics: {
        segmentsUploaded: number;
        bytesUploaded: number;
        reconnectCount: number;
        errors: number;
        queueDepth: number;
    };
    s3Prefix: string;
    healthEndpoint?: string;
}

export interface StreamEvent {
    type: 'heartbeat' | 'started' | 'stopped' | 'disconnected' | 'error';
    sessionId: string;
    data: Partial<StreamSession>;
    timestamp: Date;
}

@Injectable()
export class StreamManagerService {
    private readonly logger = new Logger(StreamManagerService.name);
    private sessions = new Map<string, StreamSession>();
    private readonly DISCONNECT_TIMEOUT = 30_000; // 30s 无心跳视为断开

    constructor() {
        // 定期检查断开的会话
        setInterval(() => this._checkDisconnected(), 10_000);
    }

    /** 注册一个新的采集会话 */
    register(session: Omit<StreamSession, 'id' | 'startedAt' | 'lastHeartbeat' | 'metrics'>): StreamSession {
        const id = `stream_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        const now = new Date();
        const full: StreamSession = {
            ...session,
            id,
            startedAt: now,
            lastHeartbeat: now,
            metrics: {
                segmentsUploaded: 0,
                bytesUploaded: 0,
                reconnectCount: 0,
                errors: 0,
                queueDepth: 0,
            },
        };
        this.sessions.set(id, full);
        this.logger.log(`📡 新采集会话: ${id} (${session.mission})`);
        return full;
    }

    /** 心跳 */
    heartbeat(id: string, metrics?: Partial<StreamSession['metrics']>): StreamSession | null {
        const session = this.sessions.get(id);
        if (!session) return null;

        session.lastHeartbeat = new Date();
        if (session.status === 'disconnected') {
            session.status = 'active';
        }
        if (metrics) {
            Object.assign(session.metrics, metrics);
        }
        return session;
    }

    /** 停止会话 */
    stop(id: string): boolean {
        const session = this.sessions.get(id);
        if (!session) return false;
        session.status = 'stopped';
        this.logger.log(`⏹ 采集会话停止: ${id}`);
        return true;
    }

    /** 获取所有活跃会话 */
    list(): StreamSession[] {
        return Array.from(this.sessions.values())
            .filter(s => s.status !== 'stopped');
    }

    /** 获取单个会话 */
    get(id: string): StreamSession | null {
        return this.sessions.get(id) ?? null;
    }

    /** SSE 事件流（轮询模式，每 2s 推送变更） */
    async *events(): AsyncGenerator<StreamEvent> {
        const seen = new Set<string>();
        while (true) {
            for (const [, session] of this.sessions) {
                const key = `${session.id}_${session.status}_${session.metrics.segmentsUploaded}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    // 清理该 session 的旧 key
                    for (const k of seen) {
                        if (k.startsWith(session.id) && k !== key) seen.delete(k);
                    }
                    yield {
                        type: 'heartbeat',
                        sessionId: session.id,
                        data: session,
                        timestamp: new Date(),
                    };
                }
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    /** 检查并标记断开的会话 */
    private _checkDisconnected(): void {
        const now = Date.now();
        for (const [, session] of this.sessions) {
            if (session.status === 'active' &&
                now - session.lastHeartbeat.getTime() > this.DISCONNECT_TIMEOUT) {
                session.status = 'disconnected';
                this.logger.warn(`⚠️ 采集会话断开: ${session.id}`);
            }
        }
    }
}
