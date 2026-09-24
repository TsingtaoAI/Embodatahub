import { ApiProperty } from '@nestjs/swagger';
import { Expose } from 'class-transformer';
import {
    IsArray,
    IsInt,
    IsNumber,
    IsOptional,
    IsString,
    IsUUID,
} from 'class-validator';

@Expose()
export class RdsCleaningResultDto {
    @ApiProperty()
    @IsUUID()
    @Expose()
    uuid!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    episodeIndex!: number;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsNumber()
    @Expose()
    score!: number | null;

    @ApiProperty()
    @IsString()
    @Expose()
    status!: string;

    @ApiProperty()
    @IsString()
    @Expose()
    source!: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @Expose()
    perAttributeScores?: Record<string, number> | null;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @Expose()
    findings?: Record<string, unknown>[] | null;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsString()
    @Expose()
    reviewNote?: string | null;

    @ApiProperty()
    @IsString()
    @Expose()
    scorerVersion!: string;
}
