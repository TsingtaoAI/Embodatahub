import {
    Body, Controller, Get, HttpCode, Param, Post, Sse,
} from '@nestjs/common';
import { ApiOperation, ApiProperty, ApiPropertyOptional, ApiTags } from '@nestjs/swagger';
import { exec } from 'child_process';
import { IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';
import { Observable, from } from 'rxjs';
import { map } from 'rxjs/operators';
import { StreamEvent, StreamManagerService } from '../../services/stream-manager.service';

// ── 内联 DTO（绕过 tsconfig 跨项目引用缓存问题）──

class StartCaptureDto {
    @ApiProperty({ description: '视频源', example: '/dev/video0' })
    @IsString()
    source!: string;

    @ApiProperty({ description: '采集任务名称' })
    @IsString()
    mission!: string;

    @ApiPropertyOptional({ description: '分段时长（秒）', default: 10 })
    @IsOptional()
    @IsNumber()
    @Min(5)
    @Max(60)
    segmentSeconds?: number;
}

class RegisterStreamDto {
    @ApiProperty({ description: '采集任务名' })
    @IsString()
    mission!: string;

    @ApiProperty({ description: '视频源' })
    @IsString()
    source!: string;

    @ApiPropertyOptional({ description: 'S3 前缀' })
    @IsOptional()
    @IsString()
    s3Prefix?: string;

    @ApiPropertyOptional()
    @IsOptional()
    @IsString()
    healthEndpoint?: string;
}

class HeartbeatDto {
    @ApiPropertyOptional()
    @IsOptional()
    @IsNumber()
    segmentsUploaded?: number;

    @ApiPropertyOptional()
    @IsOptional()
    @IsNumber()
    bytesUploaded?: number;

    @ApiPropertyOptional()
    @IsOptional()
    @IsNumber()
    queueDepth?: number;
}

class StartCaptureResponseDto {
    @ApiProperty()
    id!: string;

    @ApiProperty()
    status!: string;

    @ApiProperty()
    mission!: string;

    @ApiProperty()
    logFile!: string;
}

@ApiTags('streams')
@Controller('api/streams')
export class StreamController {
    constructor(private readonly streamManager: StreamManagerService) {}

    /** 列出所有活跃采集流 */
    @Get()
    @ApiOperation({ summary: '列出所有活跃采集流' })
    list() {
        const sessions = this.streamManager.list();
        return {
            count: sessions.length,
            streams: sessions.map(s => ({
                id: s.id,
                mission: s.mission,
                source: s.source,
                status: s.status,
                startedAt: s.startedAt.toISOString(),
                lastHeartbeat: s.lastHeartbeat.toISOString(),
                duration: Date.now() - s.startedAt.getTime(),
                metrics: s.metrics,
                s3Prefix: s.s3Prefix,
            })),
        };
    }

    /** 获取单个采集流详情 */
    @Get(':id')
    @ApiOperation({ summary: '获取单个采集流详情' })
    get(@Param('id') id: string) {
        const s = this.streamManager.get(id);
        if (!s) return { error: 'not found' };
        return {
            id: s.id,
            mission: s.mission,
            source: s.source,
            status: s.status,
            startedAt: s.startedAt.toISOString(),
            lastHeartbeat: s.lastHeartbeat.toISOString(),
            duration: Date.now() - s.startedAt.getTime(),
            metrics: s.metrics,
            s3Prefix: s.s3Prefix,
        };
    }

    /** 注册新采集会话（边缘代理调用） */
    @Post('register')
    @HttpCode(201)
    @ApiOperation({ summary: '注册新采集会话' })
    register(@Body() body: RegisterStreamDto) {
        const session = this.streamManager.register({
            mission: body.mission,
            source: body.source,
            status: 'active',
            s3Prefix: body.s3Prefix || `streams/${body.mission}/`,
            healthEndpoint: body.healthEndpoint,
        });
        return { id: session.id, status: 'registered' };
    }

    /** 心跳（边缘代理定期调用） */
    @Post(':id/heartbeat')
    @ApiOperation({ summary: '发送心跳' })
    heartbeat(@Param('id') id: string, @Body() body: HeartbeatDto) {
        const session = this.streamManager.heartbeat(id, body);
        if (!session) return { error: 'session not found' };
        return { status: 'ok', metrics: session.metrics };
    }

    /** 停止采集 */
    @Post(':id/stop')
    @ApiOperation({ summary: '停止采集' })
    stop(@Param('id') id: string) {
        const ok = this.streamManager.stop(id);
        return { status: ok ? 'stopped' : 'not found' };
    }

    /** 启动采集（在 R240 本地执行 edge-agent.py） */
    @Post('start-capture')
    @ApiOperation({ summary: '在服务器本地启动边缘采集代理' })
    async startCapture(@Body() body: StartCaptureDto): Promise<StartCaptureResponseDto> {
        const script = '/home/msd/rslstudio/scripts/edge-agent.py';
        const cmd = [
            'python3', script,
            '--source', body.source,
            '--mission', body.mission,
            '--segment', String(body.segmentSeconds || 10),
        ].map(a => `"${a}"`).join(' ');

        const child = exec(`nohup ${cmd} > /tmp/edge-${body.mission}.log 2>&1 &`);
        child.unref();

        const session = this.streamManager.register({
            mission: body.mission,
            source: body.source,
            status: 'active',
            s3Prefix: `streams/${body.mission}/`,
        });

        return {
            id: session.id,
            status: 'launched',
            mission: body.mission,
            logFile: `/tmp/edge-${body.mission}.log`,
        };
    }

    /** SSE 实时事件流（前端订阅） */
    @Sse('events')
    @ApiOperation({ summary: '实时事件流（SSE）' })
    events(): Observable<MessageEvent> {
        return from(this._generateEvents()).pipe(
            map(event => ({ data: event } as MessageEvent)),
        );
    }

    private async *_generateEvents(): AsyncGenerator<StreamEvent> {
        for await (const event of this.streamManager.events()) {
            yield event;
        }
    }
}
