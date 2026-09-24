import { ApiProperty } from '@nestjs/swagger';
import { Expose, Type } from 'class-transformer';
import {
    IsArray,
    IsDate,
    IsInt,
    IsNumber,
    IsOptional,
    IsString,
    IsUUID,
    ValidateNested,
} from 'class-validator';
import { RdsCleaningResultDto } from './rds-cleaning-result.dto';
import { RdsEpisodeDto } from './rds-episode.dto';
import { RdsFilterResultDto } from './rds-filter-result.dto';

@Expose()
export class RdsDatasetDto {
    @ApiProperty()
    @IsUUID()
    @Expose()
    uuid!: string;

    @ApiProperty()
    @IsDate()
    @Expose()
    createdAt!: Date;

    @ApiProperty()
    @IsDate()
    @Expose()
    updatedAt!: Date;

    @ApiProperty()
    @IsString()
    @Expose()
    name!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    path!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    format!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    version!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    totalEpisodes!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    totalFrames!: number;

    @ApiProperty()
    @IsNumber()
    @Expose()
    fps!: number;

    @ApiProperty()
    @IsString()
    @Expose()
    robotType!: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @Expose()
    videoKeys?: string[] | null;

    @ApiProperty({ required: false })
    @IsOptional()
    @Expose()
    features?: Record<string, unknown> | null;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => RdsEpisodeDto)
    @Expose()
    episodes?: RdsEpisodeDto[];

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => RdsCleaningResultDto)
    @Expose()
    cleaningResults?: RdsCleaningResultDto[];

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => RdsFilterResultDto)
    @Expose()
    filterResults?: RdsFilterResultDto[];
}

@Expose()
export class RdsDatasetSummaryDto {
    @ApiProperty()
    @IsUUID()
    @Expose()
    uuid!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    name!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    format!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    totalEpisodes!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    totalFrames!: number;

    @ApiProperty()
    @IsNumber()
    @Expose()
    fps!: number;

    @ApiProperty()
    @IsString()
    @Expose()
    robotType!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    passedCount!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    reviewCount!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    excludedCount!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    unscoredCount!: number;

    @ApiProperty()
    @IsDate()
    @Expose()
    createdAt!: Date;
}
