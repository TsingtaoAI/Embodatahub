import { ApiProperty } from '@nestjs/swagger';
import { Expose, Type } from 'class-transformer';
import { IsArray, IsInt, IsNumber, IsString, ValidateNested } from 'class-validator';
import { RdsCleaningResultDto } from './rds-cleaning-result.dto';

@Expose()
export class RdsCleaningSummaryDto {
    @ApiProperty({ description: 'Episode 总数' })
    @IsInt()
    @Expose()
    total!: number;

    @ApiProperty({ description: '通过数' })
    @IsInt()
    @Expose()
    passedCount!: number;

    @ApiProperty({ description: '待审核数' })
    @IsInt()
    @Expose()
    reviewCount!: number;

    @ApiProperty({ description: '排除数' })
    @IsInt()
    @Expose()
    excludedCount!: number;

    @ApiProperty({ description: '未评分' })
    @IsInt()
    @Expose()
    unscoredCount!: number;

    @ApiProperty({ description: '平均分' })
    @IsNumber()
    @Expose()
    averageScore!: number;

    @ApiProperty({ description: '评分器版本' })
    @IsString()
    @Expose()
    scorerVersion!: string;

    @ApiProperty({ description: '各 Episode 结果', required: false })
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => RdsCleaningResultDto)
    @Expose()
    results?: RdsCleaningResultDto[];

    @ApiProperty({ description: '是否需要重新运行', required: false })
    @Expose()
    requiresRerun?: boolean;
}
