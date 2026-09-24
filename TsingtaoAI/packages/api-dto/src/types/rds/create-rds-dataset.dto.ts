import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
    IsArray,
    IsInt,
    IsNumber,
    IsOptional,
    IsString,
    IsUUID,
    ValidateNested,
} from 'class-validator';

export class CreateRdsDatasetDto {
    @ApiProperty({ description: '数据集名称' })
    @IsString()
    name!: string;

    @ApiProperty({ description: '数据集文件系统路径' })
    @IsString()
    path!: string;

    @ApiProperty({ description: '数据格式标识' })
    @IsString()
    format!: string;

    @ApiProperty({ description: '格式版本' })
    @IsString()
    version!: string;

    @ApiProperty({ description: 'Episode 总数' })
    @IsInt()
    totalEpisodes!: number;

    @ApiProperty({ description: '总帧数' })
    @IsInt()
    totalFrames!: number;

    @ApiProperty({ description: '帧率 (Hz)' })
    @IsNumber()
    fps!: number;

    @ApiProperty({ description: '机器人类型' })
    @IsString()
    robotType!: string;

    @ApiProperty({ description: '视频流 keys', required: false })
    @IsOptional()
    @IsArray()
    @IsString({ each: true })
    videoKeys?: string[];

    @ApiProperty({ description: '特征 schema', required: false })
    @IsOptional()
    features?: Record<string, unknown>;

    @ApiProperty({ description: '所属项目 UUID' })
    @IsUUID()
    projectUuid!: string;
}

export class CreateRdsEpisodeDto {
    @ApiProperty({ description: 'Episode 索引' })
    @IsInt()
    episodeIndex!: number;

    @ApiProperty({ description: '时长（秒）' })
    @IsNumber()
    durationSeconds!: number;

    @ApiProperty({ description: '帧数' })
    @IsInt()
    length!: number;

    @ApiProperty({ description: '任务描述', required: false })
    @IsOptional()
    @IsArray()
    tasks?: string[];

    @ApiProperty({ description: '子任务', required: false })
    @IsOptional()
    subtasks?: Record<string, unknown>[];

    @ApiProperty({ description: '数据文件路径' })
    @IsString()
    dataFile!: string;

    @ApiProperty({ description: '视频文件映射', required: false })
    @IsOptional()
    videoFiles?: Record<string, string>;
}

export class CreateRdsCleaningResultDto {
    @ApiProperty({ description: 'Episode 索引' })
    @IsInt()
    episodeIndex!: number;

    @ApiProperty({ description: '质量总分 (0-1)', required: false })
    @IsOptional()
    @IsNumber()
    score?: number | null;

    @ApiProperty({ description: '清洗状态' })
    @IsString()
    status!: string;

    @ApiProperty({ description: '判定来源' })
    @IsString()
    source!: string;

    @ApiProperty({ description: '各属性维度分数', required: false })
    @IsOptional()
    perAttributeScores?: Record<string, number> | null;

    @ApiProperty({ description: '质检发现', required: false })
    @IsOptional()
    findings?: Record<string, unknown>[] | null;

    @ApiProperty({ description: '人工审核备注', required: false })
    @IsOptional()
    @IsString()
    reviewNote?: string | null;

    @ApiProperty({ description: '评分器版本' })
    @IsString()
    scorerVersion!: string;
}

export class CreateRdsFilterResultDto {
    @ApiProperty({ description: 'Episode 索引' })
    @IsInt()
    episodeIndex!: number;

    @ApiProperty({ description: '过滤阶段 ID' })
    @IsString()
    stageId!: string;

    @ApiProperty({ description: '问题数量' })
    @IsInt()
    count!: number;

    @ApiProperty({ description: '跳过原因', required: false })
    @IsOptional()
    @IsString()
    skippedReason?: string;

    @ApiProperty({ description: '发现详情', required: false })
    @IsOptional()
    findings?: Record<string, unknown>[] | null;
}

/** RDS Python 回写结构化处理结果的请求体 */
export class SaveRdsResultsDto {
    @ApiProperty({ description: '数据集信息' })
    @ValidateNested()
    @Type(() => CreateRdsDatasetDto)
    dataset!: CreateRdsDatasetDto;

    @ApiProperty({ description: 'Episode 列表' })
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => CreateRdsEpisodeDto)
    episodes!: CreateRdsEpisodeDto[];

    @ApiProperty({ description: '清洗结果列表' })
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => CreateRdsCleaningResultDto)
    cleaningResults!: CreateRdsCleaningResultDto[];

    @ApiProperty({ description: '过滤结果列表' })
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => CreateRdsFilterResultDto)
    filterResults!: CreateRdsFilterResultDto[];
}
