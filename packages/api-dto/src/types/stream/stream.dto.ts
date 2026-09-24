import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';

export class StartCaptureDto {
    @ApiProperty({ description: '视频源', example: '/dev/video0' })
    @IsString()
    source!: string;

    @ApiProperty({ description: '采集任务名称', example: 'robot-cam0' })
    @IsString()
    mission!: string;

    @ApiPropertyOptional({ description: '分段时长（秒）', default: 10, minimum: 5, maximum: 60 })
    @IsOptional()
    @IsNumber()
    @Min(5)
    @Max(60)
    segmentSeconds?: number;
}

export class StartCaptureResponseDto {
    @ApiProperty({ description: '采集会话 ID' })
    @IsString()
    id!: string;

    @ApiProperty({ description: '启动状态', example: 'launched' })
    @IsString()
    status!: string;

    @ApiProperty({ description: '采集任务名' })
    @IsString()
    mission!: string;

    @ApiProperty({ description: '日志文件路径' })
    @IsString()
    logFile!: string;
}

export class HeartbeatDto {
    @ApiPropertyOptional({ description: '已上传分段数' })
    @IsOptional()
    @IsNumber()
    segmentsUploaded?: number;

    @ApiPropertyOptional({ description: '已上传字节数' })
    @IsOptional()
    @IsNumber()
    bytesUploaded?: number;

    @ApiPropertyOptional({ description: '重连次数' })
    @IsOptional()
    @IsNumber()
    reconnectCount?: number;

    @ApiPropertyOptional({ description: '错误数' })
    @IsOptional()
    @IsNumber()
    errors?: number;

    @ApiPropertyOptional({ description: '待上传队列深度' })
    @IsOptional()
    @IsNumber()
    queueDepth?: number;
}

export class RegisterStreamDto {
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

    @ApiPropertyOptional({ description: '健康检查端点' })
    @IsOptional()
    @IsString()
    healthEndpoint?: string;
}

export class StreamSessionDto {
    @ApiProperty({ description: '会话 ID' })
    id!: string;

    @ApiProperty({ description: '采集任务名' })
    mission!: string;

    @ApiProperty({ description: '视频源' })
    source!: string;

    @ApiProperty({ description: '状态', enum: ['active', 'disconnected', 'stopped'] })
    status!: string;

    @ApiProperty({ description: '启动时间' })
    startedAt!: string;

    @ApiProperty({ description: '最后心跳时间' })
    lastHeartbeat!: string;

    @ApiProperty({ description: '运行时长（毫秒）' })
    duration!: number;

    @ApiProperty({ description: '指标' })
    metrics!: {
        segmentsUploaded: number;
        bytesUploaded: number;
        reconnectCount: number;
        errors: number;
        queueDepth: number;
    };

    @ApiProperty({ description: 'S3 前缀' })
    s3Prefix!: string;

    @ApiPropertyOptional({ description: '健康检查端点' })
    healthEndpoint?: string;
}

export class StreamListResponseDto {
    @ApiProperty({ description: '活跃采集流数量' })
    count!: number;

    @ApiProperty({ type: [StreamSessionDto] })
    streams!: StreamSessionDto[];
}
