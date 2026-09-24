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
export class RdsEpisodeDto {
    @ApiProperty()
    @IsUUID()
    @Expose()
    uuid!: string;

    @ApiProperty()
    @IsInt()
    @Expose()
    episodeIndex!: number;

    @ApiProperty()
    @IsNumber()
    @Expose()
    durationSeconds!: number;

    @ApiProperty()
    @IsInt()
    @Expose()
    length!: number;

    @ApiProperty({ required: false })
    @IsOptional()
    @IsArray()
    @Expose()
    tasks?: string[] | null;

    @ApiProperty({ required: false })
    @IsOptional()
    @Expose()
    subtasks?: Record<string, unknown>[] | null;

    @ApiProperty()
    @IsString()
    @Expose()
    dataFile!: string;

    @ApiProperty({ required: false })
    @IsOptional()
    @Expose()
    videoFiles?: Record<string, string> | null;
}
