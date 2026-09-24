import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
    IsArray,
    IsNumber,
    IsString,
    ValidateNested,
} from 'class-validator';

type Bytes = number;
type Inodes = number;

export class StorageCategoryDto {
    @ApiProperty()
    @IsString()
    key!: string;

    @ApiProperty()
    @IsString()
    name!: string;

    @ApiProperty()
    @IsNumber()
    usedBytes!: Bytes;

    @ApiProperty()
    @IsNumber()
    fileCount!: number;

    @ApiProperty()
    @IsString()
    color!: string;
}

export class StorageOverviewDto {
    @ApiProperty()
    @IsNumber()
    usedBytes!: Bytes;

    @ApiProperty()
    @IsNumber()
    totalBytes!: Bytes;

    @ApiProperty()
    @IsNumber()
    usedInodes!: Inodes;

    @ApiProperty()
    @IsNumber()
    totalInodes!: Inodes;

    @ApiProperty({ type: [StorageCategoryDto] })
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => StorageCategoryDto)
    categories!: StorageCategoryDto[];
}
