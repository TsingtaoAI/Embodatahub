import { ApiProperty } from '@nestjs/swagger';
import { Expose } from 'class-transformer';
import {
    IsArray,
    IsInt,
    IsOptional,
    IsString,
    IsUUID,
} from 'class-validator';

@Expose()
export class RdsFilterResultDto {
    @ApiProperty()
    @IsUUID()
    @Expose()
    uuid!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    episodeIndex!: number;

    @ApiProperty()
    @IsString()
    @Expose()
    stageId!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    count!: number;

    @ApiProperty()
    @IsString()
    @Expose()
    skippedReason!: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @Expose()
    findings?: Record<string, unknown>[] | null;
}
